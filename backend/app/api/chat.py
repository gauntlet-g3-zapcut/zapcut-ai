"""Chat API routes."""
import logging
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from openai import OpenAI
from app.database import get_db
from app.models.user import User
from app.models.brand import Brand
from app.models.creative_bible import CreativeBible
from app.api.auth import get_current_user
from app.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/brands", tags=["chat"])


class CampaignAnswers(BaseModel):
    answers: dict


@router.post("/{brand_id}/campaign-answers")
async def submit_campaign_answers(
    brand_id: str,
    campaign_answers: CampaignAnswers,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit campaign answers."""
    logger.info(f"[CAMPAIGN-ANSWERS] Received request for brand: {brand_id}, user: {current_user.id}")
    logger.info(f"[CAMPAIGN-ANSWERS] Answers keys: {list(campaign_answers.answers.keys())}")
    
    try:
        brand_uuid = uuid.UUID(brand_id)
    except ValueError as e:
        logger.error(f"Invalid brand ID format: {brand_id}, error: {e}")
        raise HTTPException(status_code=400, detail="Invalid brand ID")
    
    brand = db.query(Brand).filter(
        Brand.id == brand_uuid,
        Brand.user_id == current_user.id
    ).first()
    
    if not brand:
        logger.warning(f"Brand not found: {brand_id} for user: {current_user.id}")
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Validate answers
    required_keys = ["style", "audience", "emotion", "pacing", "colors"]
    missing_keys = [key for key in required_keys if key not in campaign_answers.answers]
    if missing_keys:
        logger.error(f"Missing required answer keys: {missing_keys}. Received keys: {list(campaign_answers.answers.keys())}")
        raise HTTPException(status_code=400, detail=f"All questions must be answered. Missing: {', '.join(missing_keys)}")
    
    try:
        logger.info(f"[CAMPAIGN-ANSWERS] Creating creative bible for brand: {brand_id}")
        # Create creative bible
        creative_bible = CreativeBible(
            brand_id=brand.id,
            name=f"campaign_{uuid.uuid4().hex[:8]}",
            creative_bible={},
            reference_image_urls={},
            conversation_history=campaign_answers.answers,
            created_at=datetime.utcnow().isoformat()
        )
        logger.info(f"[CAMPAIGN-ANSWERS] CreativeBible object created, adding to session")
        db.add(creative_bible)
        logger.info(f"[CAMPAIGN-ANSWERS] Committing to database...")
        db.commit()
        logger.info(f"[CAMPAIGN-ANSWERS] Commit successful, refreshing object...")
        db.refresh(creative_bible)
        
        logger.info(f"[CAMPAIGN-ANSWERS] Created creative bible: {creative_bible.id} for brand: {brand_id}")
        
        return {
            "creative_bible_id": str(creative_bible.id),
            "message": "Campaign preferences saved successfully"
        }
    except Exception as e:
        logger.error(f"[CAMPAIGN-ANSWERS] Error creating creative bible: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save campaign answers: {str(e)}")


@router.get("/{brand_id}/storyline/{creative_bible_id}")
async def get_storyline(
    brand_id: str,
    creative_bible_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get or generate storyline."""
    try:
        brand_uuid = uuid.UUID(brand_id)
        creative_bible_uuid = uuid.UUID(creative_bible_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    brand = db.query(Brand).filter(
        Brand.id == brand_uuid,
        Brand.user_id == current_user.id
    ).first()

    if not brand:
        print(f"❌ ERROR: Brand not found")
        print(f"   - Either brand doesn't exist with ID: {brand_id}")
        print(f"   - Or brand doesn't belong to user: {current_user.id}")
        # Debug: Check if brand exists at all (without user filter)
        brand_exists = db.query(Brand).filter(Brand.id == uuid.UUID(brand_id)).first()
        if brand_exists:
            print(f"   ℹ️  Brand exists but belongs to user: {brand_exists.user_id}")
        else:
            print(f"   ℹ️  Brand does not exist in database")
        raise HTTPException(status_code=404, detail="Brand not found")
    
    creative_bible = db.query(CreativeBible).filter(
        CreativeBible.id == creative_bible_uuid,
        CreativeBible.brand_id == brand.id
    ).first()
    
    if not creative_bible:
        print(f"❌ ERROR: Creative Bible not found")
        print(f"   Brand ID: {brand.id}")
        print(f"   Creative Bible ID: {creative_bible_id}")
        # Debug: Check if creative bible exists at all (without brand filter)
        if creative_bible_id != "default":
            try:
                cb_exists = db.query(CreativeBible).filter(
                    CreativeBible.id == uuid.UUID(creative_bible_id)
                ).first()
                if cb_exists:
                    print(f"   ℹ️  Creative Bible exists but belongs to brand: {cb_exists.brand_id}")
                else:
                    print(f"   ℹ️  Creative Bible does not exist in database")
            except:
                pass
        raise HTTPException(status_code=404, detail="Creative Bible not found")
    
    # Generate storyline if not exists
    if not creative_bible.creative_bible or not creative_bible.creative_bible.get("brand_style"):
        # Extract preferences from conversation history
        answers = creative_bible.conversation_history or {}
        style = answers.get("style", "Modern & Sleek")
        emotion = answers.get("emotion", "Excitement")
        pacing = answers.get("pacing", "Fast-paced & Exciting")
        colors_pref = answers.get("colors", "Bold & Vibrant")
        audience = answers.get("audience", "Everyone")
        
        # Get brand information
        brand_title = brand.title or "Product"
        brand_description = brand.description or ""
        
        # Generate storyline using OpenAI
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set, using fallback storyline generation")
            creative_bible_data = _generate_fallback_storyline(style, emotion, pacing, colors_pref)
        else:
            try:
                creative_bible_data = await _generate_storyline_with_openai(
                    brand_title, brand_description, style, emotion, pacing, colors_pref, audience
                )
                logger.info(f"Generated storyline with OpenAI for creative bible: {creative_bible.id}")
            except Exception as e:
                logger.error(f"OpenAI generation failed: {e}, using fallback")
                creative_bible_data = _generate_fallback_storyline(style, emotion, pacing, colors_pref)
        
        # Log what we're about to save
        logger.info(f"=== SAVING CREATIVE BIBLE DATA ===")
        logger.info(f"Creative Bible ID: {creative_bible.id}")
        logger.info(f"Data keys: {list(creative_bible_data.keys())}")
        logger.info(f"sora_prompts in data: {'sora_prompts' in creative_bible_data}")
        if 'sora_prompts' in creative_bible_data:
            sora_prompts_value = creative_bible_data.get('sora_prompts')
            logger.info(f"sora_prompts type: {type(sora_prompts_value)}")
            logger.info(f"sora_prompts value: {sora_prompts_value}")
            logger.info(f"sora_prompts length: {len(sora_prompts_value) if isinstance(sora_prompts_value, list) else 'N/A'}")
        else:
            logger.warning(f"sora_prompts NOT FOUND in creative_bible_data!")
        
        creative_bible.creative_bible = creative_bible_data
        db.commit()
        db.refresh(creative_bible)
        
        # Log what was actually saved
        logger.info(f"=== VERIFYING SAVED DATA ===")
        saved_data = creative_bible.creative_bible or {}
        logger.info(f"Saved data keys: {list(saved_data.keys())}")
        saved_sora_prompts = saved_data.get('sora_prompts', 'NOT_FOUND')
        logger.info(f"Saved sora_prompts: {saved_sora_prompts}")
        logger.info(f"Saved sora_prompts type: {type(saved_sora_prompts)}")
        if isinstance(saved_sora_prompts, list):
            logger.info(f"Saved sora_prompts length: {len(saved_sora_prompts)}")
            if len(saved_sora_prompts) > 0:
                logger.info(f"First sora_prompt example: {saved_sora_prompts[0]}")
        
        logger.info(f"Saved storyline for creative bible: {creative_bible.id}")
    
    bible_data = creative_bible.creative_bible or {}
    return {
        "creative_bible": {
            "brand_style": bible_data.get("brand_style"),
            "vibe": bible_data.get("vibe"),
            "colors": bible_data.get("colors", []),
            "energy_level": bible_data.get("energy_level")
        },
        "storyline": bible_data.get("storyline", {}),
        "sora_prompts": bible_data.get("sora_prompts", []),
        "suno_prompt": bible_data.get("suno_prompt", "")
    }


async def _generate_storyline_with_openai(
    brand_title: str,
    brand_description: str,
    style: str,
    emotion: str,
    pacing: str,
    colors_pref: str,
    audience: str
) -> dict:
    """Generate storyline using OpenAI."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    prompt = f"""Create a 30-second video ad storyline for a product/brand.

Brand: {brand_title}
Description: {brand_description}
Style: {style}
Target Audience: {audience}
Emotion/Message: {emotion}
Pacing: {pacing}
Color Preference: {colors_pref}

Generate a creative bible and detailed storyline with exactly 5 scenes, each 6 seconds long (total 30 seconds).

For each scene, provide:
- scene_number (1-5)
- title (short, engaging scene title)
- description (detailed description of what happens)
- start_time (in seconds, e.g., 0.0, 6.0, 12.0, 18.0, 24.0)
- end_time (in seconds, e.g., 6.0, 12.0, 18.0, 24.0, 30.0)
- duration (6.0 for each scene)
- energy_start (0.0 to 1.0, starting energy level)
- energy_end (0.0 to 1.0, ending energy level - should progress upward)
- visual_notes (specific visual direction and style notes)

Also provide:
- brand_style (one word: modern, energetic, luxurious, minimal, bold)
- vibe (one word: energetic, sophisticated, fun, elegant, dramatic)
- colors (array of 2-3 hex color codes matching the color preference)
- energy_level (high, medium, or low)
- suno_prompt (music generation prompt for Suno AI)

Return ONLY valid JSON in this exact format:
{{
  "brand_style": "modern",
  "vibe": "energetic",
  "colors": ["#FF5733", "#33FF57"],
  "energy_level": "high",
  "storyline": {{
    "scenes": [
      {{
        "scene_number": 1,
        "title": "Hook & Attention Grab",
        "description": "Detailed description...",
        "start_time": 0.0,
        "end_time": 6.0,
        "duration": 6.0,
        "energy_start": 0.3,
        "energy_end": 0.4,
        "visual_notes": "Specific visual direction..."
      }}
    ]
  }},
  "suno_prompt": "Music description..."
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert video ad creative director. Generate compelling, detailed video ad storylines in JSON format."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    logger.info(f"=== OPENAI RAW RESPONSE ===")
    logger.info(f"Response length: {len(content)} chars")
    logger.info(f"Response preview: {content[:500]}...")
    logger.debug(f"OpenAI full response: {content}")
    
    try:
        result = json.loads(content)
        logger.info(f"=== PARSED JSON RESULT ===")
        logger.info(f"Result keys: {list(result.keys())}")
        logger.info(f"Has 'storyline' key: {'storyline' in result}")
        if 'storyline' in result:
            logger.info(f"Storyline keys: {list(result['storyline'].keys()) if isinstance(result['storyline'], dict) else 'Not a dict'}")
            if isinstance(result['storyline'], dict) and 'scenes' in result['storyline']:
                logger.info(f"Number of scenes: {len(result['storyline']['scenes'])}")
        
        # Validate and ensure all scenes have required fields
        if "storyline" in result and "scenes" in result["storyline"]:
            scenes = result["storyline"]["scenes"]
            total_duration = 30
            scene_duration = total_duration / len(scenes)
            
            # Ensure proper timing and structure
            for i, scene in enumerate(scenes):
                scene["scene_number"] = i + 1
                scene["start_time"] = round(i * scene_duration, 1)
                scene["end_time"] = round((i + 1) * scene_duration, 1)
                scene["duration"] = round(scene_duration, 1)
                if "energy_start" not in scene:
                    scene["energy_start"] = round(0.3 + (i * 0.15), 1)
                if "energy_end" not in scene:
                    scene["energy_end"] = round(0.4 + (i * 0.15), 1)
                if "visual_notes" not in scene:
                    scene["visual_notes"] = f"{style} aesthetic with {emotion} tone"
            
            # Generate sora_prompts from scenes
            sora_prompts = []
            for scene in scenes:
                scene_num = scene.get("scene_number", 0)
                scene_title = scene.get("title", f"Scene {scene_num}")
                scene_description = scene.get("description", "")
                visual_notes = scene.get("visual_notes", "")
                
                # Create comprehensive prompt for Sora
                sora_prompt = f"{scene_title}. {scene_description}. {visual_notes}".strip()
                
                sora_prompts.append({
                    "scene_number": scene_num,
                    "prompt": sora_prompt
                })
            
            # Store sora_prompts in result
            result["sora_prompts"] = sora_prompts
            logger.info(f"Generated {len(sora_prompts)} sora_prompts in OpenAI response")
            logger.info(f"First sora_prompt example: {sora_prompts[0] if sora_prompts else 'N/A'}")
        else:
            logger.warning("No 'storyline' or 'scenes' found in OpenAI response, sora_prompts not generated")
            result["sora_prompts"] = []
        
        logger.info(f"Returning result with keys: {list(result.keys())}")
        logger.info(f"Result sora_prompts: {result.get('sora_prompts', 'NOT_FOUND')}")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate storyline")


def _generate_fallback_storyline(style: str, emotion: str, pacing: str, colors_pref: str) -> dict:
    """Fallback storyline generation without OpenAI."""
    brand_style = "modern" if "Modern" in style or "Sleek" in style else "energetic"
    vibe = "energetic" if "Energetic" in style or "Fun" in style else "sophisticated"
    energy_level = "high" if "Fast" in pacing or "Exciting" in pacing else "medium"
    
    if "Bold" in colors_pref or "Vibrant" in colors_pref:
        colors = ["#FF5733", "#33FF57", "#3357FF"]
    elif "Dark" in colors_pref or "Moody" in colors_pref:
        colors = ["#1a1a1a", "#4a4a4a", "#8a8a8a"]
    elif "Light" in colors_pref or "Airy" in colors_pref:
        colors = ["#FFFFFF", "#F0F0F0", "#E0E0E0"]
    else:
        colors = ["#FF5733", "#33FF57"]
    
    scenes = []
    total_duration = 30
    num_scenes = 5
    scene_duration = total_duration / num_scenes
    
    scene_titles = [
        "Hook & Attention Grab",
        "Product Introduction",
        "Key Benefits",
        "Social Proof",
        "Call to Action"
    ]
    
    scene_descriptions = [
        "Dynamic opening that immediately captures attention with bold visuals",
        "Showcase the product with clear, compelling visuals",
        "Highlight the main benefits and value proposition",
        "Build trust with testimonials or social proof",
        "Strong call-to-action with clear next steps"
    ]
    
    energy_levels = [0.3, 0.5, 0.7, 0.8, 0.9]
    
    for i in range(num_scenes):
        start_time = i * scene_duration
        end_time = (i + 1) * scene_duration
        scenes.append({
            "scene_number": i + 1,
            "title": scene_titles[i],
            "description": scene_descriptions[i],
            "start_time": round(start_time, 1),
            "end_time": round(end_time, 1),
            "duration": round(scene_duration, 1),
            "energy_start": energy_levels[i],
            "energy_end": energy_levels[i] + 0.1 if i < num_scenes - 1 else 1.0,
            "visual_notes": f"{style} aesthetic with {emotion} tone, {pacing} pacing"
        })
    
    # Generate sora_prompts from scenes
    sora_prompts = []
    for scene in scenes:
        scene_num = scene.get("scene_number", 0)
        scene_title = scene.get("title", f"Scene {scene_num}")
        scene_description = scene.get("description", "")
        visual_notes = scene.get("visual_notes", "")
        
        # Create comprehensive prompt for Sora
        sora_prompt = f"{scene_title}. {scene_description}. {visual_notes}".strip()
        
        sora_prompts.append({
            "scene_number": scene_num,
            "prompt": sora_prompt
        })
    
    result = {
        "brand_style": brand_style,
        "vibe": vibe,
        "colors": colors,
        "energy_level": energy_level,
        "storyline": {
            "scenes": scenes
        },
        "sora_prompts": sora_prompts,
        "suno_prompt": f"Upbeat {energy_level} energy music for {emotion.lower()} product advertisement"
    }
    
    logger.info(f"Fallback storyline generated with {len(sora_prompts)} sora_prompts")
    logger.info(f"Fallback result keys: {list(result.keys())}")
    logger.info(f"Fallback sora_prompts: {result.get('sora_prompts', 'NOT_FOUND')}")
    
    return result

