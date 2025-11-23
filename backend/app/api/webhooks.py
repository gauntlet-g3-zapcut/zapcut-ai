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
from app.tasks.video_generation import (
    DEFAULT_GENERATION_MODE,
    extract_last_frame,
    extract_video_url,
    trigger_next_scene_after_completion,
    update_scene_status_safe,
)
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
    try:
        # Read request body
        body = await request.body()
        
        # Verify signature if enabled
        if WEBHOOK_VERIFICATION_ENABLED and settings.REPLICATE_WEBHOOK_SECRET:
            if not x_replicate_content_sha256:
                logger.warning(f"Webhook missing signature header | campaign={campaign_id} | scene={scene_num}")
                raise HTTPException(
                    status_code=401,
                    detail="Missing webhook signature"
                )
            
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
            logger.warning("Webhook verification disabled or secret not configured")
        
        # Parse webhook payload
        import json
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
        
        # Get campaign from database
        db = get_session_local()()
        try:
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
            
            if not campaign:
                db.close()
                logger.warning(
                    f"Campaign not found (may have been deleted) | campaign={campaign_id} | "
                    f"scene={scene_num} | prediction_id={prediction_id} | status={status}"
                )
                # Return 200 OK so Replicate doesn't retry
                # The campaign may have been deleted or doesn't exist
                return {
                    "status": "ok",
                    "message": "Campaign not found - webhook acknowledged but not processed"
                }
            
            # Get storyline and scenes for reference
            storyline = campaign.storyline or {}
            scenes = storyline.get("scenes", [])
            preferences = {}
            if getattr(campaign, "creative_bible", None) and campaign.creative_bible.campaign_preferences:
                preferences = campaign.creative_bible.campaign_preferences or {}
            generation_mode = str(preferences.get("generation_mode", DEFAULT_GENERATION_MODE)).lower()
            
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
                
                if current_status in ["completed", "failed"] and stored_prediction_id == prediction_id:
                    logger.info(
                        f"Webhook already processed (idempotent) | campaign={campaign_id} | "
                        f"scene={scene_num} | prediction_id={prediction_id}"
                    )
                    return {"status": "ok", "message": "Already processed"}
            
            # Handle different prediction statuses
            if status == "succeeded":
                # Extract Replicate video URL from output
                replicate_video_url = extract_video_url(output)
                
                if not replicate_video_url:
                    error_msg = "No video URL in prediction output"
                    logger.error(f"{error_msg} | campaign={campaign_id} | scene={scene_num} | prediction_id={prediction_id}")
                    update_scene_status_safe(
                        campaign_id,
                        scene_num,
                        "failed",
                        error=error_msg,
                        prediction_id=prediction_id
                    )
                    # Return 500 so Replicate retries (though this shouldn't happen)
                    raise HTTPException(
                        status_code=500,
                        detail=error_msg
                    )
                
                # Get scene duration from campaign data
                scene_data = next(
                    (s for s in scenes if s.get("scene_number") == scene_num),
                    None
                )
                duration = scene_data.get("duration", 6.0) if scene_data else 6.0
                seed_image_url = None
                
                logger.info(
                    f"Scene {scene_num} succeeded | campaign={campaign_id} | "
                    f"prediction_id={prediction_id} | replicate_url={replicate_video_url}"
                )
                
                # Download video from Replicate and upload to S3
                try:
                    # Download video bytes from Replicate
                    logger.info(
                        f"Downloading video from Replicate | campaign={campaign_id} | "
                        f"scene={scene_num} | url={replicate_video_url}"
                    )
                    
                    # Use httpx with timeout and retries
                    with httpx.Client(timeout=60.0) as client:
                        response = client.get(replicate_video_url)
                        response.raise_for_status()
                        video_bytes = response.content
                    
                    logger.info(
                        f"Video downloaded | campaign={campaign_id} | scene={scene_num} | "
                        f"size={len(video_bytes)} bytes"
                    )
                    
                    # Upload to Supabase S3
                    # File key format: generated/{campaign_id}/scene-{scene_num}/prediction-{prediction_id}.mp4
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
                    
                    if generation_mode == "sequential":
                        frame_bytes = extract_last_frame(video_bytes)
                        if frame_bytes:
                            seed_key = f"generated/{campaign_id}/scene-{scene_num}/seed-{prediction_id}.png"
                            try:
                                seed_image_url = upload_bytes(
                                    bucket_name=bucket_name,
                                    file_key=seed_key,
                                    data=frame_bytes,
                                    content_type="image/png",
                                    acl="public-read",
                                )
                                logger.info(
                                    "Seed image uploaded | campaign=%s | scene=%s | key=%s",
                                    campaign_id,
                                    scene_num,
                                    seed_key,
                                )
                            except Exception as seed_error:
                                seed_image_url = None
                                logger.error(
                                    "Failed to upload seed image | campaign=%s | scene=%s | error=%s",
                                    campaign_id,
                                    scene_num,
                                    seed_error,
                                )
                        else:
                            logger.warning(
                                "Sequential mode: unable to extract seed frame | campaign=%s | scene=%s",
                                campaign_id,
                                scene_num,
                            )
                    
                except httpx.HTTPError as e:
                    error_msg = f"Failed to download video from Replicate: {str(e)}"
                    logger.error(
                        f"{error_msg} | campaign={campaign_id} | scene={scene_num} | "
                        f"prediction_id={prediction_id}",
                        exc_info=True
                    )
                    update_scene_status_safe(
                        campaign_id,
                        scene_num,
                        "failed",
                        error=error_msg,
                        prediction_id=prediction_id
                    )
                    # Return 500 so Replicate retries
                    raise HTTPException(
                        status_code=500,
                        detail=error_msg
                    )
                except Exception as upload_error:
                    error_msg = f"Failed to upload video to S3: {str(upload_error)}"
                    logger.error(
                        f"{error_msg} | campaign={campaign_id} | scene={scene_num} | "
                        f"prediction_id={prediction_id}",
                        exc_info=True
                    )
                    update_scene_status_safe(
                        campaign_id,
                        scene_num,
                        "failed",
                        error=error_msg,
                        prediction_id=prediction_id
                    )
                    # Return 500 so Replicate retries
                    raise HTTPException(
                        status_code=500,
                        detail=error_msg
                    )
                
                # Update scene status to completed with S3 URL
                update_success = update_scene_status_safe(
                    campaign_id,
                    scene_num,
                    "completed",
                    video_url=s3_video_url,  # Use S3 URL, not Replicate URL
                    duration=duration,
                    prediction_id=prediction_id,
                    seed_image_url=seed_image_url,
                )
                
                if update_success:
                    logger.info(
                        f"Scene {scene_num} S3 video URL saved | campaign={campaign_id} | "
                        f"s3_url={s3_video_url}"
                    )
                else:
                    logger.error(
                        f"Failed to save S3 video URL for scene {scene_num} | campaign={campaign_id} | "
                        f"s3_url={s3_video_url}"
                    )
                
                # Check if all scenes are complete and update campaign status
                # Refresh to get latest data after update_scene_status_safe
                db.refresh(campaign)
                final_scene_video_urls = campaign.video_urls or []
                
                # Log all scene video URLs for debugging
                logger.debug(
                    f"Campaign {campaign_id} video_urls after update: {final_scene_video_urls}"
                )
                
                completed = [
                    v for v in final_scene_video_urls
                    if v.get("status") == "completed" and v.get("video_url")
                ]
                failed = [
                    v for v in final_scene_video_urls
                    if v.get("status") == "failed"
                ]
                total_scenes = len(scenes)
                
                # Only mark as completed when ALL scenes are done
                if len(completed) == total_scenes:
                    campaign.status = "completed"
                    if final_scene_video_urls and final_scene_video_urls[0].get("video_url"):
                        campaign.final_video_url = final_scene_video_urls[0]["video_url"]
                    logger.info(
                        f"Campaign completed | campaign={campaign_id} | scenes={len(completed)}"
                    )
                elif len(completed) > 0:
                    # Keep status as "processing" until all scenes are complete
                    # Don't set status to "completed" yet
                    logger.info(
                        f"Campaign in progress | campaign={campaign_id} | "
                        f"completed={len(completed)}/{total_scenes} | failed={len(failed)}"
                    )
                elif len(failed) == total_scenes:
                    campaign.status = "failed"
                    logger.error(
                        f"Campaign failed | campaign={campaign_id} | failed={len(failed)}"
                    )
                
                db.commit()
                
                if generation_mode == "sequential":
                    trigger_next_scene_after_completion(
                        campaign_id,
                        scene_num,
                        seed_image_url,
                    )
                
            elif status == "failed":
                error_msg = error or "Unknown error"
                
                # Get current retry count
                db.refresh(campaign)
                scene_video_urls = campaign.video_urls or []
                scene_entry = next(
                    (s for s in scene_video_urls if s.get("scene_number") == scene_num),
                    None
                )
                current_retry_count = scene_entry.get("retry_count", 0) if scene_entry else 0
                max_retries = 3
                
                if current_retry_count < max_retries:
                    # Retry the prediction
                    new_retry_count = current_retry_count + 1
                    logger.warning(
                        f"Prediction failed, retrying ({new_retry_count}/{max_retries}) | "
                        f"campaign={campaign_id} | scene={scene_num} | "
                        f"prediction_id={prediction_id} | error={error_msg}"
                    )
                    
                    # Update scene with retry count and error, but keep status as "generating"
                    update_scene_status_safe(
                        campaign_id,
                        scene_num,
                        "generating",  # Set back to generating for retry
                        error=f"Retry {new_retry_count}/{max_retries}: {error_msg}",
                        retry_count=new_retry_count
                    )
                    
                    # Trigger retry by creating new prediction
                    from app.tasks.video_generation import retry_scene_prediction
                    retry_success = retry_scene_prediction(campaign_id, scene_num)
                    
                    if not retry_success:
                        logger.error(
                            f"Failed to create retry prediction | campaign={campaign_id} | scene={scene_num}"
                        )
                        # Mark as failed if retry creation failed
                        update_scene_status_safe(
                            campaign_id,
                            scene_num,
                            "failed",
                            error=f"Retry failed: {error_msg}",
                            prediction_id=prediction_id,
                            retry_count=new_retry_count
                        )
                    
                    db.commit()
                else:
                    # Max retries exhausted, mark as permanently failed
                    logger.error(
                        f"Prediction failed after {max_retries} retries | campaign={campaign_id} | "
                        f"scene={scene_num} | prediction_id={prediction_id} | error={error_msg}"
                    )
                    
                    # Update scene status to failed
                    update_scene_status_safe(
                        campaign_id,
                        scene_num,
                        "failed",
                        error=error_msg,
                        prediction_id=prediction_id,
                        retry_count=current_retry_count
                    )
                    
                    # Check if all scenes failed
                    db.refresh(campaign)
                    final_scene_video_urls = campaign.video_urls or []
                    failed = [
                        v for v in final_scene_video_urls
                        if v.get("status") == "failed"
                    ]
                    total_scenes = len(scenes)
                    
                    if len(failed) == total_scenes:
                        campaign.status = "failed"
                        db.commit()
                        logger.error(
                            f"Campaign failed | campaign={campaign_id} | failed={len(failed)}"
                        )
                    else:
                        db.commit()
                
            elif status == "canceled":
                error_msg = "Prediction canceled"
                
                # Get current retry count (same logic as failed)
                db.refresh(campaign)
                scene_video_urls = campaign.video_urls or []
                scene_entry = next(
                    (s for s in scene_video_urls if s.get("scene_number") == scene_num),
                    None
                )
                current_retry_count = scene_entry.get("retry_count", 0) if scene_entry else 0
                max_retries = 3
                
                if current_retry_count < max_retries:
                    # Retry the prediction
                    new_retry_count = current_retry_count + 1
                    logger.warning(
                        f"Prediction canceled, retrying ({new_retry_count}/{max_retries}) | "
                        f"campaign={campaign_id} | scene={scene_num} | prediction_id={prediction_id}"
                    )
                    
                    # Update scene with retry count and error, but keep status as "generating"
                    update_scene_status_safe(
                        campaign_id,
                        scene_num,
                        "generating",  # Set back to generating for retry
                        error=f"Retry {new_retry_count}/{max_retries}: {error_msg}",
                        retry_count=new_retry_count
                    )
                    
                    # Trigger retry by creating new prediction
                    from app.tasks.video_generation import retry_scene_prediction
                    retry_success = retry_scene_prediction(campaign_id, scene_num)
                    
                    if not retry_success:
                        logger.error(
                            f"Failed to create retry prediction | campaign={campaign_id} | scene={scene_num}"
                        )
                        # Mark as failed if retry creation failed
                        update_scene_status_safe(
                            campaign_id,
                            scene_num,
                            "failed",
                            error=f"Retry failed: {error_msg}",
                            prediction_id=prediction_id,
                            retry_count=new_retry_count
                        )
                    
                    db.commit()
                else:
                    # Max retries exhausted, mark as permanently failed
                    logger.error(
                        f"Prediction canceled after {max_retries} retries | campaign={campaign_id} | "
                        f"scene={scene_num} | prediction_id={prediction_id}"
                    )
                    
                    update_scene_status_safe(
                        campaign_id,
                        scene_num,
                        "failed",
                        error=error_msg,
                        prediction_id=prediction_id,
                        retry_count=current_retry_count
                    )
                    db.commit()
                
            else:
                # Status is "starting" or "processing" - log but don't update
                logger.debug(
                    f"Prediction in progress | campaign={campaign_id} | scene={scene_num} | "
                    f"prediction_id={prediction_id} | status={status}"
                )
            
            return {"status": "ok", "message": "Webhook processed"}
            
        except HTTPException:
            # Re-raise HTTP exceptions (already handled)
            db.rollback()
            db.close()
            raise
        except Exception as db_error:
            # Database errors
            db.rollback()
            db.close()
            logger.error(
                f"Database error processing webhook | campaign={campaign_id} | scene={scene_num} | error={str(db_error)}",
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(db_error)}"
            )
        finally:
            if db:
                db.close()
    
    except HTTPException:
        # Re-raise HTTP exceptions from outer scope
        raise
    except Exception as e:
        logger.error(
            f"Error processing webhook | campaign={campaign_id} | scene={scene_num} | error={str(e)}",
            exc_info=True
        )
        # Return 500 so Replicate retries
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

