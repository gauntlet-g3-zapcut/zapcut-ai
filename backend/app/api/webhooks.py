"""Webhook endpoints for external services."""
import logging
import hmac
import hashlib
import uuid
import httpx
from fastapi import APIRouter, Request, HTTPException, Query, Header
from typing import Optional
from app.database import get_session_local
from app.models.campaign import Campaign
from app.config import settings
from app.tasks.video_generation import update_scene_status_safe, extract_video_url
from app.services.storage import upload_bytes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Constants
WEBHOOK_VERIFICATION_ENABLED = True


def verify_replicate_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
    """Verify Replicate webhook signature using HMAC-SHA256.
    
    Replicate sends webhooks with X-Replicate-Content-SHA256 header.
    The signature is computed as HMAC-SHA256 of the request body using the webhook secret.
    """
    if not secret:
        logger.warning("Webhook secret not configured, skipping verification")
        return False
    
    try:
        # Compute expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures (constant-time comparison)
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False


@router.post("/replicate")
async def replicate_webhook(
    request: Request,
    campaign_id: str = Query(..., description="Campaign UUID"),
    scene_num: int = Query(..., description="Scene number"),
    x_replicate_content_sha256: Optional[str] = Header(None, alias="X-Replicate-Content-SHA256")
):
    """Handle Replicate webhook callbacks for video generation predictions.

    This endpoint receives webhooks from Replicate when predictions complete.
    It verifies the signature, extracts the prediction result, and updates
    the campaign scene status accordingly.

    IMPORTANT: This handler uses a two-phase approach to avoid database lock contention:
    1. Short transaction: Validate and mark scene as "uploading" (releases lock quickly)
    2. Slow I/O: Download from Replicate, upload to S3 (no lock held)
    3. Short transaction: Update with final S3 URL and check completion

    Query Parameters:
        campaign_id: UUID of the campaign
        scene_num: Scene number being processed

    Headers:
        X-Replicate-Content-SHA256: HMAC-SHA256 signature of the request body

    Returns:
        200 OK if webhook processed successfully
        401 Unauthorized if signature verification fails
        500 Internal Server Error if processing fails (Replicate will retry)
    """
    import json

    try:
        # Read request body
        body = await request.body()

        # Verify signature if provided
        if not settings.REPLICATE_WEBHOOK_SECRET:
            logger.warning(
                f"REPLICATE_WEBHOOK_SECRET not configured - signature verification disabled (SECURITY RISK) | "
                f"campaign={campaign_id} | scene={scene_num}"
            )
        elif x_replicate_content_sha256:
            if not verify_replicate_signature(
                body,
                x_replicate_content_sha256,
                settings.REPLICATE_WEBHOOK_SECRET
            ):
                logger.error(f"Invalid webhook signature | campaign={campaign_id} | scene={scene_num}")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid webhook signature"
                )
            logger.debug(f"Webhook signature verified | campaign={campaign_id} | scene={scene_num}")
        else:
            logger.debug(f"Webhook received without signature header | campaign={campaign_id} | scene={scene_num}")

        # Parse webhook payload
        try:
            payload = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook payload | campaign={campaign_id} | scene={scene_num} | error={e}")
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON payload"
            )

        # Extract prediction data
        prediction_id = payload.get("id")
        status = payload.get("status")
        output = payload.get("output")
        error = payload.get("error")

        logger.info(
            f"Webhook received | campaign={campaign_id} | scene={scene_num} | "
            f"prediction_id={prediction_id} | status={status}"
        )

        # Validate campaign_id format
        try:
            campaign_uuid = uuid.UUID(campaign_id)
        except ValueError:
            logger.error(f"Invalid campaign_id format | campaign={campaign_id}")
            raise HTTPException(
                status_code=400,
                detail="Invalid campaign_id format"
            )

        # ============================================================
        # PHASE 1: Quick validation and mark as "uploading" (short lock)
        # ============================================================
        replicate_video_url = None
        duration = 6.0
        scenes = []

        db = get_session_local()()
        try:
            # Short lock - only for validation and status update
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).with_for_update().first()

            if not campaign:
                logger.warning(
                    f"Campaign not found (may have been deleted) | campaign={campaign_id} | "
                    f"scene={scene_num} | prediction_id={prediction_id} | status={status}"
                )
                return {
                    "status": "ok",
                    "message": "Campaign not found - webhook acknowledged but not processed"
                }

            # Get storyline and scenes for reference
            storyline = campaign.storyline or {}
            scenes = storyline.get("scenes", [])

            # Check if this webhook is for the correct scene (idempotency check)
            scene_video_urls = campaign.video_urls or []
            scene_entry = next(
                (s for s in scene_video_urls if s.get("scene_number") == scene_num),
                None
            )

            if scene_entry:
                # Check if already processed (idempotency)
                current_status = scene_entry.get("status")
                stored_prediction_id = scene_entry.get("prediction_id")

                if current_status in ["completed", "failed", "uploading"] and stored_prediction_id == prediction_id:
                    logger.info(
                        f"Webhook already processed (idempotent) | campaign={campaign_id} | "
                        f"scene={scene_num} | prediction_id={prediction_id} | status={current_status}"
                    )
                    db.close()
                    return {"status": "ok", "message": "Already processed"}

            # Handle different prediction statuses
            if status == "succeeded":
                # Extract Replicate video URL from output
                replicate_video_url = extract_video_url(output)

                if not replicate_video_url:
                    error_msg = "No video URL in prediction output"
                    logger.error(f"{error_msg} | campaign={campaign_id} | scene={scene_num} | prediction_id={prediction_id}")
                    _update_scene_field_atomic(db, campaign, scene_num, {
                        "status": "failed",
                        "error": error_msg,
                        "prediction_id": prediction_id
                    })
                    db.commit()
                    db.close()
                    raise HTTPException(status_code=500, detail=error_msg)

                # Get scene duration from campaign data
                scene_data = next(
                    (s for s in scenes if s.get("scene_number") == scene_num),
                    None
                )
                duration = scene_data.get("duration", 6.0) if scene_data else 6.0

                logger.info(
                    f"Scene {scene_num} succeeded | campaign={campaign_id} | "
                    f"prediction_id={prediction_id} | replicate_url={replicate_video_url}"
                )

                # Mark as "uploading" to prevent duplicate processing
                _update_scene_field_atomic(db, campaign, scene_num, {
                    "status": "uploading",
                    "prediction_id": prediction_id
                })
                db.commit()
                # Lock released here

            elif status == "failed":
                error_msg = error or "Unknown error"

                # Handle retry logic within the lock
                scene_video_urls = campaign.video_urls or []
                scene_entry = next(
                    (s for s in scene_video_urls if s.get("scene_number") == scene_num),
                    None
                )
                current_retry_count = scene_entry.get("retry_count", 0) if scene_entry else 0
                max_retries = 3

                if current_retry_count < max_retries:
                    new_retry_count = current_retry_count + 1
                    logger.warning(
                        f"Prediction failed, retrying ({new_retry_count}/{max_retries}) | "
                        f"campaign={campaign_id} | scene={scene_num} | "
                        f"prediction_id={prediction_id} | error={error_msg}"
                    )

                    _update_scene_field_atomic(db, campaign, scene_num, {
                        "status": "generating",
                        "error": f"Retry {new_retry_count}/{max_retries}: {error_msg}",
                        "retry_count": new_retry_count
                    })
                    db.commit()
                    db.close()

                    # Trigger retry outside of lock
                    from app.tasks.video_generation import retry_scene_prediction
                    retry_success = retry_scene_prediction(campaign_id, scene_num)

                    if not retry_success:
                        logger.error(f"Failed to create retry prediction | campaign={campaign_id} | scene={scene_num}")
                        # Mark as failed in new transaction
                        db2 = get_session_local()()
                        try:
                            campaign2 = db2.query(Campaign).filter(Campaign.id == campaign_uuid).with_for_update().first()
                            if campaign2:
                                _update_scene_field_atomic(db2, campaign2, scene_num, {
                                    "status": "failed",
                                    "error": f"Retry failed: {error_msg}",
                                    "prediction_id": prediction_id,
                                    "retry_count": new_retry_count
                                })
                                db2.commit()
                        finally:
                            db2.close()

                    return {"status": "ok", "message": "Webhook processed - retry triggered"}
                else:
                    logger.error(
                        f"Prediction failed after {max_retries} retries | campaign={campaign_id} | "
                        f"scene={scene_num} | prediction_id={prediction_id} | error={error_msg}"
                    )

                    _update_scene_field_atomic(db, campaign, scene_num, {
                        "status": "failed",
                        "error": error_msg,
                        "prediction_id": prediction_id,
                        "retry_count": current_retry_count
                    })

                    # Check if all scenes failed
                    failed = [v for v in (campaign.video_urls or []) if v.get("status") == "failed"]
                    if len(failed) == len(scenes):
                        campaign.status = "failed"
                        logger.error(f"Campaign failed | campaign={campaign_id} | failed={len(failed)}")

                    db.commit()
                    db.close()
                    return {"status": "ok", "message": "Webhook processed - scene failed"}

            elif status == "canceled":
                error_msg = "Prediction canceled"

                scene_video_urls = campaign.video_urls or []
                scene_entry = next(
                    (s for s in scene_video_urls if s.get("scene_number") == scene_num),
                    None
                )
                current_retry_count = scene_entry.get("retry_count", 0) if scene_entry else 0
                max_retries = 3

                if current_retry_count < max_retries:
                    new_retry_count = current_retry_count + 1
                    logger.warning(
                        f"Prediction canceled, retrying ({new_retry_count}/{max_retries}) | "
                        f"campaign={campaign_id} | scene={scene_num} | prediction_id={prediction_id}"
                    )

                    _update_scene_field_atomic(db, campaign, scene_num, {
                        "status": "generating",
                        "error": f"Retry {new_retry_count}/{max_retries}: {error_msg}",
                        "retry_count": new_retry_count
                    })
                    db.commit()
                    db.close()

                    from app.tasks.video_generation import retry_scene_prediction
                    retry_success = retry_scene_prediction(campaign_id, scene_num)

                    if not retry_success:
                        logger.error(f"Failed to create retry prediction | campaign={campaign_id} | scene={scene_num}")
                        db2 = get_session_local()()
                        try:
                            campaign2 = db2.query(Campaign).filter(Campaign.id == campaign_uuid).with_for_update().first()
                            if campaign2:
                                _update_scene_field_atomic(db2, campaign2, scene_num, {
                                    "status": "failed",
                                    "error": f"Retry failed: {error_msg}",
                                    "prediction_id": prediction_id,
                                    "retry_count": new_retry_count
                                })
                                db2.commit()
                        finally:
                            db2.close()

                    return {"status": "ok", "message": "Webhook processed - retry triggered"}
                else:
                    logger.error(
                        f"Prediction canceled after {max_retries} retries | campaign={campaign_id} | "
                        f"scene={scene_num} | prediction_id={prediction_id}"
                    )

                    _update_scene_field_atomic(db, campaign, scene_num, {
                        "status": "failed",
                        "error": error_msg,
                        "prediction_id": prediction_id,
                        "retry_count": current_retry_count
                    })
                    db.commit()
                    db.close()
                    return {"status": "ok", "message": "Webhook processed - scene failed"}

            else:
                # Status is "starting" or "processing" - log but don't update
                logger.debug(
                    f"Prediction in progress | campaign={campaign_id} | scene={scene_num} | "
                    f"prediction_id={prediction_id} | status={status}"
                )
                db.close()
                return {"status": "ok", "message": "Webhook acknowledged"}

        except HTTPException:
            db.rollback()
            db.close()
            raise
        except Exception as db_error:
            db.rollback()
            db.close()
            logger.error(
                f"Database error in phase 1 | campaign={campaign_id} | scene={scene_num} | error={str(db_error)}",
                exc_info=True
            )
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        finally:
            if db.is_active:
                db.close()

        # ============================================================
        # PHASE 2: Slow I/O operations (NO DATABASE LOCK HELD)
        # ============================================================
        if status != "succeeded" or not replicate_video_url:
            return {"status": "ok", "message": "Webhook processed"}

        s3_video_url = None
        try:
            # Download video bytes from Replicate
            logger.info(
                f"Downloading video from Replicate | campaign={campaign_id} | "
                f"scene={scene_num} | url={replicate_video_url}"
            )

            with httpx.Client(timeout=60.0) as client:
                response = client.get(replicate_video_url)
                response.raise_for_status()
                video_bytes = response.content

            logger.info(
                f"Video downloaded | campaign={campaign_id} | scene={scene_num} | "
                f"size={len(video_bytes)} bytes"
            )

            # Upload to Supabase S3
            bucket_name = settings.SUPABASE_S3_VIDEO_BUCKET
            file_key = f"generated/{campaign_id}/scene-{scene_num}/prediction-{prediction_id}.mp4"

            logger.info(
                f"Uploading video to S3 | campaign={campaign_id} | scene={scene_num} | "
                f"bucket={bucket_name} | key={file_key}"
            )

            s3_video_url = upload_bytes(
                bucket_name=bucket_name,
                file_key=file_key,
                data=video_bytes,
                content_type='video/mp4',
                acl='public-read'
            )

            logger.info(
                f"Video uploaded to S3 | campaign={campaign_id} | scene={scene_num} | "
                f"s3_url={s3_video_url}"
            )

        except httpx.HTTPError as e:
            error_msg = f"Failed to download video from Replicate: {str(e)}"
            logger.error(f"{error_msg} | campaign={campaign_id} | scene={scene_num}", exc_info=True)
            # Mark as failed in new transaction
            db = get_session_local()()
            try:
                campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).with_for_update().first()
                if campaign:
                    _update_scene_field_atomic(db, campaign, scene_num, {
                        "status": "failed",
                        "error": error_msg,
                        "prediction_id": prediction_id
                    })
                    db.commit()
            finally:
                db.close()
            raise HTTPException(status_code=500, detail=error_msg)

        except Exception as upload_error:
            error_msg = f"Failed to upload video to S3: {str(upload_error)}"
            logger.error(f"{error_msg} | campaign={campaign_id} | scene={scene_num}", exc_info=True)
            db = get_session_local()()
            try:
                campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).with_for_update().first()
                if campaign:
                    _update_scene_field_atomic(db, campaign, scene_num, {
                        "status": "failed",
                        "error": error_msg,
                        "prediction_id": prediction_id
                    })
                    db.commit()
            finally:
                db.close()
            raise HTTPException(status_code=500, detail=error_msg)

        # ============================================================
        # PHASE 3: Final update with S3 URL (short lock)
        # ============================================================
        db = get_session_local()()
        try:
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).with_for_update().first()

            if not campaign:
                logger.warning(f"Campaign deleted during upload | campaign={campaign_id}")
                db.close()
                return {"status": "ok", "message": "Campaign deleted during processing"}

            # Update scene with final S3 URL
            _update_scene_field_atomic(db, campaign, scene_num, {
                "status": "completed",
                "video_url": s3_video_url,
                "duration": duration,
                "prediction_id": prediction_id
            })

            logger.info(f"Scene {scene_num} S3 video URL saved | campaign={campaign_id} | s3_url={s3_video_url}")

            # Check if all scenes are complete
            storyline = campaign.storyline or {}
            scenes = storyline.get("scenes", [])
            final_scene_video_urls = campaign.video_urls or []

            completed = [
                v for v in final_scene_video_urls
                if v.get("status") == "completed" and v.get("video_url")
            ]
            failed = [
                v for v in final_scene_video_urls
                if v.get("status") == "failed"
            ]
            total_scenes = len(scenes)

            if len(completed) == total_scenes:
                pipeline_stage = campaign.pipeline_stage

                if pipeline_stage in ["videos_generating", "upscaling", "images_generating", "images_ready"]:
                    logger.info(
                        f"All videos completed | campaign={campaign_id} | scenes={len(completed)}"
                    )
                    campaign.pipeline_stage = "videos_ready"
                    db.commit()

                    if campaign.director_mode == "surprise_me":
                        # Use coordinated assembly - only triggers if audio is also ready
                        from app.tasks.video_generation import check_ready_and_assemble
                        check_ready_and_assemble(campaign_id)
                    else:
                        logger.info(f"Videos ready, waiting for approval | campaign={campaign_id}")
                else:
                    campaign.status = "completed"
                    if final_scene_video_urls and final_scene_video_urls[0].get("video_url"):
                        campaign.final_video_url = final_scene_video_urls[0]["video_url"]
                    logger.info(f"Campaign completed (legacy) | campaign={campaign_id} | scenes={len(completed)}")
                    db.commit()
            elif len(completed) > 0:
                logger.info(
                    f"Campaign in progress | campaign={campaign_id} | "
                    f"completed={len(completed)}/{total_scenes} | failed={len(failed)}"
                )
                db.commit()
            elif len(failed) == total_scenes:
                campaign.status = "failed"
                logger.error(f"Campaign failed | campaign={campaign_id} | failed={len(failed)}")
                db.commit()
            else:
                db.commit()

            return {"status": "ok", "message": "Webhook processed"}

        except Exception as db_error:
            db.rollback()
            logger.error(
                f"Database error in phase 3 | campaign={campaign_id} | scene={scene_num} | error={str(db_error)}",
                exc_info=True
            )
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error processing webhook | campaign={campaign_id} | scene={scene_num} | error={str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/replicate/image")
async def replicate_image_webhook(
    request: Request,
    campaign_id: str = Query(..., description="Campaign UUID"),
    scene_num: int = Query(..., description="Scene number"),
    x_replicate_content_sha256: Optional[str] = Header(None, alias="X-Replicate-Content-SHA256")
):
    """Handle Replicate webhook callbacks for Nano Banana image generation.

    On success: Downloads image, uploads to S3, triggers upscaling.
    On failure: Marks scene as failed or retries.
    """
    try:
        body = await request.body()

        # Verify signature if provided (optional - Replicate doesn't always send signatures)
        if x_replicate_content_sha256 and settings.REPLICATE_WEBHOOK_SECRET:
            if not verify_replicate_signature(body, x_replicate_content_sha256, settings.REPLICATE_WEBHOOK_SECRET):
                logger.error(f"Invalid image webhook signature | campaign={campaign_id} | scene={scene_num}")
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
            logger.debug(f"Image webhook signature verified | campaign={campaign_id} | scene={scene_num}")
        else:
            logger.debug(f"Image webhook without signature (allowed) | campaign={campaign_id} | scene={scene_num}")

        import json
        payload = json.loads(body.decode('utf-8'))

        prediction_id = payload.get("id")
        status = payload.get("status")
        output = payload.get("output")
        error = payload.get("error")

        logger.info(
            f"Image webhook received | campaign={campaign_id} | scene={scene_num} | "
            f"prediction_id={prediction_id} | status={status}"
        )

        campaign_uuid = uuid.UUID(campaign_id)
        db = get_session_local()()

        try:
            # CRITICAL: Use SELECT FOR UPDATE to prevent race conditions
            # Multiple image webhooks arriving simultaneously will serialize here
            # preventing the lost update problem when modifying the JSON video_urls array
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).with_for_update().first()

            if not campaign:
                db.close()
                logger.warning(f"Campaign not found for image webhook | campaign={campaign_id}")
                return {"status": "ok", "message": "Campaign not found"}

            if status == "succeeded":
                # Extract image URL from output (use Replicate URL directly, skip S3)
                image_url = extract_video_url(output)

                if not image_url:
                    logger.error(f"No image URL in output | campaign={campaign_id} | scene={scene_num}")
                    _update_scene_field_atomic(db, campaign, scene_num, {
                        "image_status": "failed",
                        "error": "No image URL in output"
                    })
                    db.commit()
                    return {"status": "ok", "message": "No image URL"}

                logger.info(f"Image completed (using Replicate URL directly) | campaign={campaign_id} | scene={scene_num}")

                # Update scene status atomically with all fields at once
                # This prevents partial updates and ensures consistency
                _update_scene_field_atomic(db, campaign, scene_num, {
                    "base_image_url": image_url,
                    "image_status": "completed",
                    "image_prediction_id": prediction_id
                })
                db.commit()

                # Check if all images are ready (will refresh campaign first)
                _check_images_ready_and_trigger_next(campaign, db, campaign_id)

            elif status == "failed":
                error_msg = error or "Unknown error"
                logger.error(f"Image generation failed | campaign={campaign_id} | scene={scene_num} | error={error_msg}")

                _update_scene_field_atomic(db, campaign, scene_num, {
                    "image_status": "failed",
                    "error": f"Image generation failed: {error_msg}"
                })
                db.commit()

            elif status == "canceled":
                logger.warning(f"Image generation canceled | campaign={campaign_id} | scene={scene_num}")
                _update_scene_field_atomic(db, campaign, scene_num, {
                    "image_status": "failed",
                    "error": "Image generation canceled"
                })
                db.commit()

            return {"status": "ok", "message": "Image webhook processed"}

        except HTTPException:
            db.rollback()
            raise
        except Exception as db_error:
            db.rollback()
            logger.error(f"Database error in image webhook | campaign={campaign_id} | error={str(db_error)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image webhook | campaign={campaign_id} | scene={scene_num} | error={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/replicate/upscale")
async def replicate_upscale_webhook(
    request: Request,
    campaign_id: str = Query(..., description="Campaign UUID"),
    scene_num: int = Query(..., description="Scene number"),
    x_replicate_content_sha256: Optional[str] = Header(None, alias="X-Replicate-Content-SHA256")
):
    """Handle Replicate webhook callbacks for Real-ESRGAN upscaling.

    On success: Downloads upscaled image, uploads to S3, triggers video generation.
    On failure: Falls back to base image for video generation.
    """
    try:
        body = await request.body()

        # Verify signature if provided (optional - Replicate doesn't always send signatures)
        if x_replicate_content_sha256 and settings.REPLICATE_WEBHOOK_SECRET:
            if not verify_replicate_signature(body, x_replicate_content_sha256, settings.REPLICATE_WEBHOOK_SECRET):
                logger.error(f"Invalid upscale webhook signature | campaign={campaign_id} | scene={scene_num}")
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
            logger.debug(f"Upscale webhook signature verified | campaign={campaign_id} | scene={scene_num}")
        else:
            logger.debug(f"Upscale webhook without signature (allowed) | campaign={campaign_id} | scene={scene_num}")

        import json
        payload = json.loads(body.decode('utf-8'))

        prediction_id = payload.get("id")
        status = payload.get("status")
        output = payload.get("output")
        error = payload.get("error")

        logger.info(
            f"Upscale webhook received | campaign={campaign_id} | scene={scene_num} | "
            f"prediction_id={prediction_id} | status={status}"
        )

        campaign_uuid = uuid.UUID(campaign_id)
        db = get_session_local()()

        try:
            # CRITICAL: Use SELECT FOR UPDATE to prevent race conditions
            # Multiple upscale webhooks arriving simultaneously will serialize here
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).with_for_update().first()

            if not campaign:
                db.close()
                logger.warning(f"Campaign not found for upscale webhook | campaign={campaign_id}")
                return {"status": "ok", "message": "Campaign not found"}

            # Get scene data for video generation
            video_urls = campaign.video_urls or []
            scene_entry = next((s for s in video_urls if s.get("scene_number") == scene_num), None)
            motion_prompt = scene_entry.get("motion_prompt", "") if scene_entry else ""

            if status == "succeeded":
                # Extract upscaled image URL (use Replicate URL directly, skip S3)
                upscaled_url = extract_video_url(output)

                if not upscaled_url:
                    logger.error(f"No upscaled URL in output | campaign={campaign_id} | scene={scene_num}")
                    # Fallback to base image
                    _trigger_video_with_fallback(campaign, scene_num, motion_prompt, db, campaign_id)
                    return {"status": "ok", "message": "No upscaled URL, using base image"}

                logger.info(f"Upscale completed (using Replicate URL directly) | campaign={campaign_id} | scene={scene_num}")

                # Update scene status atomically with all fields at once
                _update_scene_field_atomic(db, campaign, scene_num, {
                    "upscaled_image_url": upscaled_url,
                    "upscale_status": "completed",
                    "upscale_prediction_id": prediction_id
                })
                db.commit()

                # Trigger video generation with upscaled image (Replicate URL)
                _trigger_video_generation(campaign_id, scene_num, upscaled_url, motion_prompt)

            elif status in ["failed", "canceled"]:
                error_msg = error or f"Upscaling {status}"
                logger.warning(f"Upscaling {status} | campaign={campaign_id} | scene={scene_num} | error={error_msg}")

                _update_scene_field_atomic(db, campaign, scene_num, {
                    "upscale_status": "failed",
                    "error": error_msg
                })
                db.commit()

                # Fallback to base image
                _trigger_video_with_fallback(campaign, scene_num, motion_prompt, db, campaign_id)

            return {"status": "ok", "message": "Upscale webhook processed"}

        except HTTPException:
            db.rollback()
            raise
        except Exception as db_error:
            db.rollback()
            logger.error(f"Database error in upscale webhook | campaign={campaign_id} | error={str(db_error)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upscale webhook | campaign={campaign_id} | scene={scene_num} | error={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def _update_scene_field_atomic(db, campaign: Campaign, scene_num: int, updates: dict) -> None:
    """Atomically update multiple fields in a scene's video_urls entry.

    IMPORTANT: This function must be called within a transaction that has
    acquired a row-level lock using with_for_update() on the campaign.

    Args:
        db: Database session (with active transaction and row lock)
        campaign: Campaign object (must be locked with FOR UPDATE)
        scene_num: Scene number to update
        updates: Dict of field:value pairs to update atomically

    This prevents race conditions by:
    1. Requiring the caller to hold a row lock (enforced by code review)
    2. Updating all fields in a single operation
    3. Creating a new list to trigger SQLAlchemy change detection
    """
    # Create a completely new list to ensure SQLAlchemy detects the change
    video_urls = list(campaign.video_urls or [])
    scene_found = False

    for i, scene_entry in enumerate(video_urls):
        if scene_entry.get("scene_number") == scene_num:
            # Create a new dict with all existing fields plus updates
            updated = dict(scene_entry)
            updated.update(updates)
            video_urls[i] = updated
            scene_found = True
            break

    if not scene_found:
        # Create new entry with the updates
        new_entry = {"scene_number": scene_num}
        new_entry.update(updates)
        video_urls.append(new_entry)

    # Assign the new list to trigger SQLAlchemy's dirty tracking
    campaign.video_urls = video_urls

    # Note: We don't commit here - let the caller control transaction boundaries


def _check_images_ready_and_trigger_next(campaign: Campaign, db, campaign_id: str) -> None:
    """Check if all images are ready and trigger upscaling in surprise_me mode."""
    # IMPORTANT: Refresh campaign from database to get latest video_urls
    # This avoids race conditions where concurrent webhook handlers update different scenes
    db.refresh(campaign)

    video_urls = campaign.video_urls or []
    completed_images = [v for v in video_urls if v.get("image_status") == "completed"]
    total_scenes = len(video_urls)

    logger.info(f"Image progress | campaign={campaign_id} | completed={len(completed_images)}/{total_scenes}")

    if len(completed_images) == total_scenes:
        # All images ready
        campaign.pipeline_stage = "images_ready"
        db.commit()

        # In surprise_me mode, auto-trigger upscaling
        if campaign.director_mode == "surprise_me":
            logger.info(f"All images ready, triggering upscaling | campaign={campaign_id}")
            campaign.pipeline_stage = "upscaling"
            db.commit()

            # Trigger upscaling for each scene
            from app.tasks.image_generation import upscale_single_image_task
            for scene_entry in video_urls:
                scene_num = scene_entry.get("scene_number")
                base_image_url = scene_entry.get("base_image_url")
                if base_image_url:
                    upscale_single_image_task.delay(campaign_id, scene_num, base_image_url)


def _trigger_video_generation(campaign_id: str, scene_num: int, image_url: str, motion_prompt: str) -> None:
    """Trigger video generation for a scene with the given image."""
    logger.info(f"Triggering video generation | campaign={campaign_id} | scene={scene_num}")

    # Update pipeline stage to videos_generating
    # Use SELECT FOR UPDATE to prevent race conditions when multiple upscale webhooks
    # try to update pipeline_stage simultaneously
    try:
        db = get_session_local()()
        campaign_uuid = uuid.UUID(campaign_id)
        campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).with_for_update().first()
        if campaign and campaign.pipeline_stage in ["upscaling", "images_ready"]:
            campaign.pipeline_stage = "videos_generating"
            db.commit()
        db.close()
    except Exception as e:
        logger.warning(f"Failed to update pipeline_stage | campaign={campaign_id} | error={str(e)}")

    from app.tasks.video_generation import generate_single_scene_task

    # Create scene_data dict for video generation
    scene_data = {
        "scene_number": scene_num,
        "duration": 6.0,
    }

    generate_single_scene_task.delay(
        campaign_id,
        scene_data,
        scene_num - 1,  # scene_index
        motion_prompt,  # video_prompt
        image_url  # image parameter for image-to-video
    )


def _trigger_video_with_fallback(campaign: Campaign, scene_num: int, motion_prompt: str, db, campaign_id: str) -> None:
    """Fallback: trigger video generation with base image when upscaling fails."""
    video_urls = campaign.video_urls or []
    scene_entry = next((s for s in video_urls if s.get("scene_number") == scene_num), None)

    if scene_entry and scene_entry.get("base_image_url"):
        base_url = scene_entry["base_image_url"]
        logger.warning(f"Falling back to base image for video | campaign={campaign_id} | scene={scene_num}")
        _trigger_video_generation(campaign_id, scene_num, base_url, motion_prompt)
    else:
        logger.error(f"No base image for fallback | campaign={campaign_id} | scene={scene_num}")


# =============================================================================
# V2 SEQUENTIAL PIPELINE WEBHOOKS
# =============================================================================


@router.post("/replicate/sequential")
async def replicate_sequential_video_webhook(
    request: Request,
    campaign_id: str = Query(..., description="Campaign UUID"),
    segment_num: int = Query(..., description="Segment number (1-5)"),
    x_replicate_content_sha256: Optional[str] = Header(None, alias="X-Replicate-Content-SHA256")
):
    """Handle Replicate webhook for V2 sequential video generation.

    IMPORTANT: This handler uses a two-phase approach to avoid database lock contention:
    1. Short transaction: Validate and mark segment as "uploading" (releases lock quickly)
    2. Slow I/O: Download from Replicate, upload to S3 (no lock held)
    3. Short transaction: Update with final S3 URL and trigger next steps

    On success:
    1. Downloads video from Replicate and uploads to S3
    2. Extracts last frame (for segments 1-4)
    3. Triggers next segment or assembly (for segment 5)
    """
    import json

    try:
        body = await request.body()

        # Verify signature if provided
        if x_replicate_content_sha256 and settings.REPLICATE_WEBHOOK_SECRET:
            if not verify_replicate_signature(body, x_replicate_content_sha256, settings.REPLICATE_WEBHOOK_SECRET):
                logger.error(f"Invalid sequential video webhook signature | campaign={campaign_id} | segment={segment_num}")
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

        payload = json.loads(body.decode('utf-8'))

        prediction_id = payload.get("id")
        status = payload.get("status")
        output = payload.get("output")
        error = payload.get("error")

        logger.info(
            f"Sequential video webhook received | campaign={campaign_id} | segment={segment_num} | "
            f"prediction_id={prediction_id} | status={status}"
        )

        campaign_uuid = uuid.UUID(campaign_id)

        # ============================================================
        # PHASE 1: Quick validation and mark as "uploading" (short lock)
        # ============================================================
        replicate_video_url = None
        total_segments = 0

        db = get_session_local()()
        try:
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).with_for_update().first()

            if not campaign:
                db.close()
                logger.warning(f"Campaign not found for sequential webhook | campaign={campaign_id}")
                return {"status": "ok", "message": "Campaign not found"}

            # Get total segments for later use
            story_document = campaign.story_document or {}
            total_segments = len(story_document.get("segments", []))

            if status == "succeeded":
                # Extract video URL
                replicate_video_url = extract_video_url(output)

                if not replicate_video_url:
                    logger.error(f"No video URL in sequential output | campaign={campaign_id} | segment={segment_num}")
                    _update_sequential_segment(campaign, segment_num, "failed", error="No video URL in output")
                    db.commit()
                    db.close()
                    return {"status": "ok", "message": "No video URL"}

                logger.info(f"Sequential video succeeded | campaign={campaign_id} | segment={segment_num}")

                # Mark as "uploading" to prevent duplicate processing
                _update_sequential_segment(campaign, segment_num, "uploading")
                db.commit()
                # Lock released here

            elif status == "failed":
                error_msg = error or "Unknown error"
                logger.error(f"Sequential video failed | campaign={campaign_id} | segment={segment_num} | error={error_msg}")
                _update_sequential_segment(campaign, segment_num, "failed", error=error_msg)
                db.commit()
                db.close()
                return {"status": "ok", "message": "Sequential webhook processed - failed"}

            elif status == "canceled":
                logger.warning(f"Sequential video canceled | campaign={campaign_id} | segment={segment_num}")
                _update_sequential_segment(campaign, segment_num, "failed", error="Prediction canceled")
                db.commit()
                db.close()
                return {"status": "ok", "message": "Sequential webhook processed - canceled"}

            else:
                # Status is "starting" or "processing"
                db.close()
                return {"status": "ok", "message": "Webhook acknowledged"}

        except HTTPException:
            db.rollback()
            db.close()
            raise
        except Exception as db_error:
            db.rollback()
            db.close()
            logger.error(f"Database error in phase 1 | campaign={campaign_id} | segment={segment_num} | error={str(db_error)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        finally:
            if db.is_active:
                db.close()

        # ============================================================
        # PHASE 2: Slow I/O operations (NO DATABASE LOCK HELD)
        # ============================================================
        if not replicate_video_url:
            return {"status": "ok", "message": "Webhook processed"}

        s3_video_url = None
        try:
            logger.info(f"Downloading segment video from Replicate | campaign={campaign_id} | segment={segment_num}")

            with httpx.Client(timeout=120.0) as client:
                response = client.get(replicate_video_url)
                response.raise_for_status()
                video_bytes = response.content

            bucket_name = settings.SUPABASE_S3_VIDEO_BUCKET
            file_key = f"generated/{campaign_id}/segments/segment_{segment_num}.mp4"

            s3_video_url = upload_bytes(
                bucket_name=bucket_name,
                file_key=file_key,
                data=video_bytes,
                content_type='video/mp4',
                acl='public-read'
            )

            logger.info(f"Segment {segment_num} uploaded to S3 | campaign={campaign_id} | url={s3_video_url}")

        except Exception as upload_error:
            error_msg = f"Failed to upload segment video: {str(upload_error)}"
            logger.error(f"{error_msg} | campaign={campaign_id} | segment={segment_num}")
            # Mark as failed in new transaction
            db = get_session_local()()
            try:
                campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).with_for_update().first()
                if campaign:
                    _update_sequential_segment(campaign, segment_num, "failed", error=error_msg)
                    db.commit()
            finally:
                db.close()
            raise HTTPException(status_code=500, detail=error_msg)

        # ============================================================
        # PHASE 3: Final update and trigger next steps (short lock)
        # ============================================================
        db = get_session_local()()
        try:
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).with_for_update().first()

            if not campaign:
                db.close()
                logger.warning(f"Campaign deleted during upload | campaign={campaign_id}")
                return {"status": "ok", "message": "Campaign deleted during processing"}

            # Update segment status with S3 URL
            _update_sequential_segment(campaign, segment_num, "completed", video_url=s3_video_url)
            db.commit()

            # Extract last frame (except for final segment)
            if segment_num < total_segments:
                logger.info(f"Extracting last frame from segment {segment_num} | campaign={campaign_id}")

                from app.services.frame_extraction import extract_last_frame
                frame_url = extract_last_frame(s3_video_url, campaign_id, segment_num)

                if frame_url:
                    # Update with frame URL in new short transaction
                    campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).with_for_update().first()
                    if campaign:
                        _update_sequential_segment(campaign, segment_num, "completed", last_frame_url=frame_url)
                        db.commit()
                else:
                    logger.error(f"Failed to extract frame from segment {segment_num} | campaign={campaign_id}")

            db.close()

            # Trigger next segment or assembly (outside lock)
            from app.tasks.sequential_video import trigger_next_segment_or_assembly
            if segment_num < total_segments:
                trigger_next_segment_or_assembly(campaign_id, segment_num)
            else:
                logger.info(f"Final segment {segment_num} complete | campaign={campaign_id}")
                trigger_next_segment_or_assembly(campaign_id, segment_num)

            return {"status": "ok", "message": "Sequential webhook processed"}

        except Exception as db_error:
            db.rollback()
            logger.error(f"Database error in phase 3 | campaign={campaign_id} | segment={segment_num} | error={str(db_error)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing sequential webhook | campaign={campaign_id} | segment={segment_num} | error={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/replicate/segment-image")
async def replicate_segment_image_webhook(
    request: Request,
    campaign_id: str = Query(..., description="Campaign UUID"),
    segment_num: int = Query(..., description="Segment number"),
    x_replicate_content_sha256: Optional[str] = Header(None, alias="X-Replicate-Content-SHA256")
):
    """Handle Replicate webhook for V2 segment image generation.

    On success: Triggers video generation for this segment with the generated image.
    """
    try:
        body = await request.body()

        # Verify signature if provided
        if x_replicate_content_sha256 and settings.REPLICATE_WEBHOOK_SECRET:
            if not verify_replicate_signature(body, x_replicate_content_sha256, settings.REPLICATE_WEBHOOK_SECRET):
                logger.error(f"Invalid segment image webhook signature | campaign={campaign_id} | segment={segment_num}")
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

        import json
        payload = json.loads(body.decode('utf-8'))

        prediction_id = payload.get("id")
        status = payload.get("status")
        output = payload.get("output")
        error = payload.get("error")

        logger.info(
            f"Segment image webhook received | campaign={campaign_id} | segment={segment_num} | "
            f"prediction_id={prediction_id} | status={status}"
        )

        campaign_uuid = uuid.UUID(campaign_id)
        db = get_session_local()()

        try:
            # CRITICAL: Use SELECT FOR UPDATE to prevent race conditions
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).with_for_update().first()

            if not campaign:
                db.close()
                logger.warning(f"Campaign not found for segment image webhook | campaign={campaign_id}")
                return {"status": "ok", "message": "Campaign not found"}

            if status == "succeeded":
                # Extract image URL
                image_url = extract_video_url(output)

                if not image_url:
                    logger.error(f"No image URL in segment image output | campaign={campaign_id} | segment={segment_num}")
                    _update_sequential_segment(campaign, segment_num, "failed", error="No image URL in output")
                    db.commit()
                    return {"status": "ok", "message": "No image URL"}

                logger.info(f"Segment {segment_num} image completed | campaign={campaign_id} | url={image_url[:60]}...")

                # Store image URL in segment data
                _update_sequential_segment(campaign, segment_num, "image_completed", base_image_url=image_url)
                db.commit()

                # Trigger video generation with this image
                from app.tasks.sequential_video import generate_segment_video_task
                generate_segment_video_task.delay(campaign_id, segment_num, image_url)

            elif status == "failed":
                error_msg = error or "Unknown error"
                logger.error(f"Segment image failed | campaign={campaign_id} | segment={segment_num} | error={error_msg}")
                _update_sequential_segment(campaign, segment_num, "failed", error=f"Image generation failed: {error_msg}")
                db.commit()

            elif status == "canceled":
                logger.warning(f"Segment image canceled | campaign={campaign_id} | segment={segment_num}")
                _update_sequential_segment(campaign, segment_num, "failed", error="Image generation canceled")
                db.commit()

            return {"status": "ok", "message": "Segment image webhook processed"}

        except HTTPException:
            db.rollback()
            raise
        except Exception as db_error:
            db.rollback()
            logger.error(f"Database error in segment image webhook | campaign={campaign_id} | error={str(db_error)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing segment image webhook | campaign={campaign_id} | segment={segment_num} | error={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def _update_sequential_segment(
    campaign: Campaign,
    segment_num: int,
    status: str,
    video_url: Optional[str] = None,
    last_frame_url: Optional[str] = None,
    base_image_url: Optional[str] = None,
    error: Optional[str] = None
) -> None:
    """Helper to update segment status in V2 sequential pipeline."""
    video_urls = list(campaign.video_urls or [])

    for i, entry in enumerate(video_urls):
        if entry.get("scene_number") == segment_num:
            updated = dict(entry)
            updated["video_status"] = status
            updated["status"] = status

            if video_url:
                updated["video_url"] = video_url
            if last_frame_url:
                updated["last_frame_url"] = last_frame_url
            if base_image_url:
                updated["base_image_url"] = base_image_url
            if error:
                updated["error"] = error

            video_urls[i] = updated
            break

    campaign.video_urls = video_urls


# ============================================================
# PARALLEL PIPELINE WEBHOOKS (V2 Option B)
# ============================================================

@router.post("/replicate/character-ref")
async def replicate_character_ref_webhook(
    request: Request,
    campaign_id: str = Query(..., description="Campaign UUID"),
    x_replicate_content_sha256: Optional[str] = Header(None, alias="X-Replicate-Content-SHA256")
):
    """Handle webhook for character reference image generation.

    On success: Stores character reference URL and triggers all scene image generation.
    """
    import json

    try:
        body = await request.body()

        if x_replicate_content_sha256 and settings.REPLICATE_WEBHOOK_SECRET:
            if not verify_replicate_signature(body, x_replicate_content_sha256, settings.REPLICATE_WEBHOOK_SECRET):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

        payload = json.loads(body.decode('utf-8'))

        prediction_id = payload.get("id")
        status = payload.get("status")
        output = payload.get("output")
        error = payload.get("error")

        logger.info(
            f"Character ref webhook | campaign={campaign_id} | "
            f"prediction_id={prediction_id} | status={status}"
        )

        campaign_uuid = uuid.UUID(campaign_id)

        if status == "succeeded":
            # Extract image URL from output
            image_url = None
            if isinstance(output, str):
                image_url = output
            elif isinstance(output, list) and output:
                image_url = output[0]
            elif isinstance(output, dict):
                image_url = output.get("url") or output.get("image")

            if not image_url:
                logger.error(f"No image URL in character ref output | campaign={campaign_id}")
                return {"status": "ok", "message": "No image URL"}

            # Upload to S3
            try:
                with httpx.Client(timeout=60.0) as client:
                    response = client.get(image_url)
                    response.raise_for_status()
                    image_bytes = response.content

                bucket_name = settings.SUPABASE_S3_VIDEO_BUCKET
                file_key = f"generated/{campaign_id}/reference/character_ref.png"

                s3_url = upload_bytes(
                    bucket_name=bucket_name,
                    file_key=file_key,
                    data=image_bytes,
                    content_type='image/png',
                    acl='public-read'
                )

                logger.info(f"Character ref uploaded | campaign={campaign_id} | url={s3_url}")

            except Exception as upload_error:
                logger.error(f"Failed to upload character ref | campaign={campaign_id} | error={str(upload_error)}")
                return {"status": "ok", "message": "Upload failed"}

            # Store in campaign and trigger scene image generation
            db = get_session_local()()
            try:
                campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
                if campaign:
                    story_document = dict(campaign.story_document or {})
                    story_document["character_reference_url"] = s3_url
                    campaign.story_document = story_document
                    campaign.pipeline_stage = "character_ref_complete"
                    db.commit()

                    # Trigger parallel scene image generation
                    from app.tasks.parallel_video import generate_all_scene_images_task
                    generate_all_scene_images_task.delay(campaign_id)
                    logger.info(f"Triggered scene images generation | campaign={campaign_id}")
            finally:
                db.close()

        elif status == "failed":
            logger.error(f"Character ref failed | campaign={campaign_id} | error={error}")

        return {"status": "ok", "message": "Character ref webhook processed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing character ref webhook | campaign={campaign_id} | error={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/replicate/scene-image")
async def replicate_scene_image_webhook(
    request: Request,
    campaign_id: str = Query(..., description="Campaign UUID"),
    segment_num: int = Query(..., description="Segment number"),
    x_replicate_content_sha256: Optional[str] = Header(None, alias="X-Replicate-Content-SHA256")
):
    """Handle webhook for scene image generation (parallel pipeline).

    On success: Triggers video generation for this segment.
    """
    import json

    try:
        body = await request.body()

        if x_replicate_content_sha256 and settings.REPLICATE_WEBHOOK_SECRET:
            if not verify_replicate_signature(body, x_replicate_content_sha256, settings.REPLICATE_WEBHOOK_SECRET):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

        payload = json.loads(body.decode('utf-8'))

        prediction_id = payload.get("id")
        status = payload.get("status")
        output = payload.get("output")
        error = payload.get("error")

        logger.info(
            f"Scene image webhook | campaign={campaign_id} | segment={segment_num} | "
            f"prediction_id={prediction_id} | status={status}"
        )

        campaign_uuid = uuid.UUID(campaign_id)

        if status == "succeeded":
            # Extract image URL
            image_url = None
            if isinstance(output, str):
                image_url = output
            elif isinstance(output, list) and output:
                image_url = output[0]
            elif isinstance(output, dict):
                image_url = output.get("url") or output.get("image")

            if not image_url:
                logger.error(f"No image URL in scene image output | campaign={campaign_id} | segment={segment_num}")
                return {"status": "ok", "message": "No image URL"}

            # Upload to S3
            try:
                with httpx.Client(timeout=60.0) as client:
                    response = client.get(image_url)
                    response.raise_for_status()
                    image_bytes = response.content

                bucket_name = settings.SUPABASE_S3_VIDEO_BUCKET
                file_key = f"generated/{campaign_id}/scenes/segment_{segment_num}_scene.png"

                s3_url = upload_bytes(
                    bucket_name=bucket_name,
                    file_key=file_key,
                    data=image_bytes,
                    content_type='image/png',
                    acl='public-read'
                )

                logger.info(f"Scene image uploaded | campaign={campaign_id} | segment={segment_num} | url={s3_url}")

            except Exception as upload_error:
                logger.error(f"Failed to upload scene image | campaign={campaign_id} | segment={segment_num} | error={str(upload_error)}")
                return {"status": "ok", "message": "Upload failed"}

            # Update campaign and trigger video generation
            db = get_session_local()()
            try:
                campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
                if campaign:
                    video_urls = list(campaign.video_urls or [])
                    for entry in video_urls:
                        if entry.get("scene_number") == segment_num:
                            entry["scene_image_url"] = s3_url
                            entry["status"] = "scene_image_complete"
                            break
                    campaign.video_urls = video_urls
                    db.commit()

                    # Trigger video generation for this segment
                    from app.tasks.parallel_video import generate_segment_video_parallel_task
                    generate_segment_video_parallel_task.delay(campaign_id, segment_num, s3_url)
                    logger.info(f"Triggered video generation for segment {segment_num} | campaign={campaign_id}")
            finally:
                db.close()

        elif status == "failed":
            logger.error(f"Scene image failed | campaign={campaign_id} | segment={segment_num} | error={error}")
            # Update status to failed
            db = get_session_local()()
            try:
                campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
                if campaign:
                    video_urls = list(campaign.video_urls or [])
                    for entry in video_urls:
                        if entry.get("scene_number") == segment_num:
                            entry["status"] = "failed"
                            entry["error"] = error or "Scene image generation failed"
                            break
                    campaign.video_urls = video_urls
                    db.commit()
            finally:
                db.close()

        return {"status": "ok", "message": "Scene image webhook processed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing scene image webhook | campaign={campaign_id} | segment={segment_num} | error={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/replicate/parallel-video")
async def replicate_parallel_video_webhook(
    request: Request,
    campaign_id: str = Query(..., description="Campaign UUID"),
    segment_num: int = Query(..., description="Segment number"),
    x_replicate_content_sha256: Optional[str] = Header(None, alias="X-Replicate-Content-SHA256")
):
    """Handle webhook for parallel video generation.

    On success: Uploads video, updates status, checks if all videos complete for assembly.
    """
    import json

    try:
        body = await request.body()

        if x_replicate_content_sha256 and settings.REPLICATE_WEBHOOK_SECRET:
            if not verify_replicate_signature(body, x_replicate_content_sha256, settings.REPLICATE_WEBHOOK_SECRET):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

        payload = json.loads(body.decode('utf-8'))

        prediction_id = payload.get("id")
        status = payload.get("status")
        output = payload.get("output")
        error = payload.get("error")

        logger.info(
            f"Parallel video webhook | campaign={campaign_id} | segment={segment_num} | "
            f"prediction_id={prediction_id} | status={status}"
        )

        campaign_uuid = uuid.UUID(campaign_id)

        if status == "succeeded":
            # Extract video URL
            video_url = extract_video_url(output)

            if not video_url:
                logger.error(f"No video URL in output | campaign={campaign_id} | segment={segment_num}")
                return {"status": "ok", "message": "No video URL"}

            # Upload to S3
            try:
                with httpx.Client(timeout=120.0) as client:
                    response = client.get(video_url)
                    response.raise_for_status()
                    video_bytes = response.content

                bucket_name = settings.SUPABASE_S3_VIDEO_BUCKET
                file_key = f"generated/{campaign_id}/videos/segment_{segment_num}.mp4"

                s3_url = upload_bytes(
                    bucket_name=bucket_name,
                    file_key=file_key,
                    data=video_bytes,
                    content_type='video/mp4',
                    acl='public-read'
                )

                logger.info(f"Video uploaded | campaign={campaign_id} | segment={segment_num} | url={s3_url}")

            except Exception as upload_error:
                logger.error(f"Failed to upload video | campaign={campaign_id} | segment={segment_num} | error={str(upload_error)}")
                return {"status": "ok", "message": "Upload failed"}

            # Update campaign status
            db = get_session_local()()
            try:
                campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
                if campaign:
                    video_urls = list(campaign.video_urls or [])
                    for entry in video_urls:
                        if entry.get("scene_number") == segment_num:
                            entry["video_url"] = s3_url
                            entry["video_status"] = "completed"
                            entry["status"] = "completed"
                            break
                    campaign.video_urls = video_urls
                    db.commit()
            finally:
                db.close()

            # Check if all videos complete and trigger assembly
            from app.tasks.parallel_video import check_all_videos_complete_and_assemble
            check_all_videos_complete_and_assemble(campaign_id)

        elif status == "failed":
            logger.error(f"Video generation failed | campaign={campaign_id} | segment={segment_num} | error={error}")
            db = get_session_local()()
            try:
                campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
                if campaign:
                    video_urls = list(campaign.video_urls or [])
                    for entry in video_urls:
                        if entry.get("scene_number") == segment_num:
                            entry["video_status"] = "failed"
                            entry["status"] = "failed"
                            entry["error"] = error or "Video generation failed"
                            break
                    campaign.video_urls = video_urls
                    db.commit()
            finally:
                db.close()

        return {"status": "ok", "message": "Parallel video webhook processed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing parallel video webhook | campaign={campaign_id} | segment={segment_num} | error={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
