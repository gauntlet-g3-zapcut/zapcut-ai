"""Chat API routes."""
import logging
import uuid
import json
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from openai import OpenAI
from app.database import get_db
from app.models.user import User
from app.models.brand import Brand
from app.models.creative_bible import CreativeBible
from app.models.chat_message import ChatMessage
from app.api.auth import get_current_user
from app.config import settings
from app.services.chat_agent import ChatAgent, ASPECT_NAMES
from datetime import datetime
from app.utils.sanitization import sanitize_ideas, sanitize_scene_description, validate_user_input

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/brands", tags=["chat"])

# In-memory cache for ChatAgent instances to avoid recreating them on every message
_agent_cache: Dict[str, ChatAgent] = {}

def clear_agent_cache(creative_bible_id: str = None):
    """Clear agent cache for a specific creative bible or all agents."""
    if creative_bible_id:
        cache_key = str(creative_bible_id)
        if cache_key in _agent_cache:
            del _agent_cache[cache_key]
            logger.debug(f"Cleared agent cache for creative_bible: {creative_bible_id}")
    else:
        _agent_cache.clear()
        logger.debug("Cleared all agent cache")


class CampaignAnswers(BaseModel):
    answers: dict


class ChatMessageRequest(BaseModel):
    message: str


class ChatSessionResponse(BaseModel):
    creative_bible_id: str
    message: str
    messages: Optional[List[dict]] = []
    progress: Optional[int] = 0
    is_complete: Optional[bool] = False


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
            campaign_preferences=campaign_answers.answers,
            created_at=datetime.utcnow()
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
        raise HTTPException(status_code=500, detail="Failed to save campaign answers. Please try again.")


@router.put("/{brand_id}/campaign-answers/{creative_bible_id}")
async def update_campaign_answers(
    brand_id: str,
    creative_bible_id: str,
    campaign_answers: CampaignAnswers,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update campaign answers for existing creative bible and regenerate storyline."""
    logger.info(f"[UPDATE-CAMPAIGN] Received update for brand: {brand_id}, creative_bible: {creative_bible_id}")
    logger.info(f"[UPDATE-CAMPAIGN] Answers keys: {list(campaign_answers.answers.keys())}")

    try:
        brand_uuid = uuid.UUID(brand_id)
        creative_bible_uuid = uuid.UUID(creative_bible_id)
    except ValueError as e:
        logger.error(f"Invalid ID format: brand_id={brand_id}, creative_bible_id={creative_bible_id}, error: {e}")
        raise HTTPException(status_code=400, detail="Invalid ID format")

    brand = db.query(Brand).filter(
        Brand.id == brand_uuid,
        Brand.user_id == current_user.id
    ).first()

    if not brand:
        logger.warning(f"Brand not found: {brand_id} for user: {current_user.id}")
        raise HTTPException(status_code=404, detail="Brand not found")

    creative_bible = db.query(CreativeBible).filter(
        CreativeBible.id == creative_bible_uuid,
        CreativeBible.brand_id == brand.id
    ).first()

    if not creative_bible:
        logger.warning(f"Creative Bible not found: {creative_bible_id} for brand: {brand_id}")
        raise HTTPException(status_code=404, detail="Creative Bible not found")

    # Validate answers
    required_keys = ["style", "audience", "emotion", "pacing", "colors"]
    missing_keys = [key for key in required_keys if key not in campaign_answers.answers]
    if missing_keys:
        logger.error(f"Missing required answer keys: {missing_keys}")
        raise HTTPException(status_code=400, detail=f"All questions must be answered. Missing: {', '.join(missing_keys)}")

    try:
        logger.info(f"[UPDATE-CAMPAIGN] Updating campaign preferences and clearing old storyline")
        # Update campaign preferences
        creative_bible.campaign_preferences = campaign_answers.answers
        # Clear the old storyline so it will be regenerated
        creative_bible.creative_bible = {}
        # Save original if not already saved
        if not creative_bible.original_creative_bible:
            creative_bible.original_creative_bible = {}

        db.commit()
        db.refresh(creative_bible)

        logger.info(f"[UPDATE-CAMPAIGN] Updated creative bible: {creative_bible.id}")

        return {
            "creative_bible_id": str(creative_bible.id),
            "message": "Campaign preferences updated successfully"
        }
    except Exception as e:
        logger.error(f"[UPDATE-CAMPAIGN] Error updating creative bible: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update campaign preferences. Please try again.")


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
        raise HTTPException(status_code=404, detail="Brand not found")
    
    creative_bible = db.query(CreativeBible).filter(
        CreativeBible.id == creative_bible_uuid,
        CreativeBible.brand_id == brand.id
    ).first()
    
    if not creative_bible:
        raise HTTPException(status_code=404, detail="Creative Bible not found")
    
    # Generate storyline if not exists
    if not creative_bible.creative_bible or not creative_bible.creative_bible.get("brand_style"):
        # Extract preferences from chat-based fields (new format) or fallback to campaign_preferences (form format)
        if creative_bible.audience_description:
            # New chat-based format
            style_desc = creative_bible.style_description or ""
            style_keywords = creative_bible.style_keywords or []
            emotion_desc = creative_bible.emotion_description or ""
            emotion_keywords = creative_bible.emotion_keywords or []
            pacing_desc = creative_bible.pacing_description or ""
            pacing_keywords = creative_bible.pacing_keywords or []
            colors_desc = creative_bible.colors_description or ""
            colors_keywords = creative_bible.colors_keywords or []
            audience_desc = creative_bible.audience_description or ""
            audience_keywords = creative_bible.audience_keywords or []
        else:
            # Fallback to form-based format (campaign_preferences)
            answers = creative_bible.campaign_preferences or {}
            style_desc = answers.get("style", "Modern & Sleek")
            style_keywords = []
            emotion_desc = answers.get("emotion", "Excitement")
            emotion_keywords = []
            pacing_desc = answers.get("pacing", "Fast-paced & Exciting")
            pacing_keywords = []
            colors_desc = answers.get("colors", "Bold & Vibrant")
            colors_keywords = []
            audience_desc = answers.get("audience", "Everyone")
            audience_keywords = []

        # Get optional ideas field (from form submission) and sanitize it
        ideas = ""
        if creative_bible.campaign_preferences:
            raw_ideas = creative_bible.campaign_preferences.get("ideas", "")
            if raw_ideas:
                # Sanitize to prevent prompt injection
                ideas = sanitize_ideas(raw_ideas)
                logger.info(f"Sanitized ideas field: original_length={len(raw_ideas)}, sanitized_length={len(ideas)}")
        
        # Get brand information
        brand_title = brand.title or "Product"
        brand_description = brand.description or ""
        
        # Generate storyline using OpenAI
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set, using fallback storyline generation")
            creative_bible_data = _generate_fallback_storyline(style_desc, emotion_desc, pacing_desc, colors_desc)
        else:
            try:
                creative_bible_data = await _generate_storyline_with_openai(
                    brand_title, brand_description,
                    style_desc, style_keywords,
                    emotion_desc, emotion_keywords,
                    pacing_desc, pacing_keywords,
                    colors_desc, colors_keywords,
                    audience_desc, audience_keywords,
                    ideas
                )
                logger.info(f"Generated storyline with OpenAI for creative bible: {creative_bible.id}")
            except Exception as e:
                logger.error(f"OpenAI generation failed: {e}, using fallback")
                creative_bible_data = _generate_fallback_storyline(style_desc, emotion_desc, pacing_desc, colors_desc)
        
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
        creative_bible.original_creative_bible = creative_bible_data  # Store original for revert
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
    
    return {
        "creative_bible": {
            "brand_style": creative_bible.creative_bible.get("brand_style"),
            "vibe": creative_bible.creative_bible.get("vibe"),
            "colors": creative_bible.creative_bible.get("colors", []),
            "energy_level": creative_bible.creative_bible.get("energy_level")
        },
        "storyline": creative_bible.creative_bible.get("storyline", {}),
        "sora_prompts": creative_bible.creative_bible.get("sora_prompts", []),
        "suno_prompt": creative_bible.creative_bible.get("suno_prompt", ""),
        "updated_at": creative_bible.updated_at.isoformat() if creative_bible.updated_at else None
    }


async def _generate_storyline_with_openai(
    brand_title: str,
    brand_description: str,
    style_desc: str,
    style_keywords: list,
    emotion_desc: str,
    emotion_keywords: list,
    pacing_desc: str,
    pacing_keywords: list,
    colors_desc: str,
    colors_keywords: list,
    audience_desc: str,
    audience_keywords: list,
    ideas: str = ""
) -> dict:
    """Generate storyline using OpenAI."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # Build keyword context
    style_context = f"{style_desc}" + (f" (Keywords: {', '.join(style_keywords)})" if style_keywords else "")
    emotion_context = f"{emotion_desc}" + (f" (Keywords: {', '.join(emotion_keywords)})" if emotion_keywords else "")
    pacing_context = f"{pacing_desc}" + (f" (Keywords: {', '.join(pacing_keywords)})" if pacing_keywords else "")
    colors_context = f"{colors_desc}" + (f" (Keywords: {', '.join(colors_keywords)})" if colors_keywords else "")
    audience_context = f"{audience_desc}" + (f" (Keywords: {', '.join(audience_keywords)})" if audience_keywords else "")

    # Build ideas section if provided
    ideas_section = f"\nSpecific Ideas/Concepts to Include: {ideas}\n" if ideas and ideas.strip() else ""

    prompt = f"""Create a 30-second video ad storyline for a product/brand.

Brand: {brand_title}
Description: {brand_description}
Visual Style: {style_context}
Target Audience: {audience_context}
Emotion/Message: {emotion_context}
Pacing: {pacing_context}
Color Palette: {colors_context}{ideas_section}

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
                    scene["visual_notes"] = f"{style_desc} aesthetic with {emotion_desc} tone"
            
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


# New chat session endpoints
@router.post("/{brand_id}/chat-session", response_model=ChatSessionResponse)
async def create_chat_session(
    brand_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session for campaign creation and return initial state."""
    try:
        brand_uuid = uuid.UUID(brand_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid brand ID format")
    
    brand = db.query(Brand).filter(
        Brand.id == brand_uuid,
        Brand.user_id == current_user.id
    ).first()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    try:
        # Create new creative bible for this chat session
        creative_bible = CreativeBible(
            brand_id=brand.id,
            name=f"campaign_{uuid.uuid4().hex[:8]}",
            creative_bible={},
            reference_image_urls={},
            campaign_preferences={},
            created_at=datetime.utcnow()
        )
        db.add(creative_bible)
        db.commit()
        db.refresh(creative_bible)
        
        logger.info(f"Created chat session: {creative_bible.id} for brand: {brand_id}")
        
        # Return messages and status in the same call to reduce frontend requests
        messages = db.query(ChatMessage).filter(
            ChatMessage.creative_bible_id == creative_bible.id
        ).order_by(ChatMessage.created_at).all()
        
        # Count collected aspects
        collected = []
        if creative_bible.audience_description:
            collected.append("audience")
        if creative_bible.style_description:
            collected.append("style")
        if creative_bible.emotion_description:
            collected.append("emotion")
        if creative_bible.pacing_description:
            collected.append("pacing")
        if creative_bible.colors_description:
            collected.append("colors")
        
        return {
            "creative_bible_id": str(creative_bible.id),
            "message": "Chat session created successfully",
            "messages": [
                {
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in messages
            ],
            "progress": len(collected),
            "is_complete": len(collected) >= 5
        }
    except Exception as e:
        logger.error(f"Error creating chat session: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create chat session. Please try again.")


@router.get("/{brand_id}/chat-session/{creative_bible_id}")
async def get_chat_session(
    brand_id: str,
    creative_bible_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chat session status."""
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
        raise HTTPException(status_code=404, detail="Brand not found")
    
    creative_bible = db.query(CreativeBible).filter(
        CreativeBible.id == creative_bible_uuid,
        CreativeBible.brand_id == brand.id
    ).first()
    
    if not creative_bible:
        raise HTTPException(status_code=404, detail="Creative Bible not found")
    
    # Count collected aspects
    collected = []
    if creative_bible.audience_description:
        collected.append("audience")
    if creative_bible.style_description:
        collected.append("style")
    if creative_bible.emotion_description:
        collected.append("emotion")
    if creative_bible.pacing_description:
        collected.append("pacing")
    if creative_bible.colors_description:
        collected.append("colors")
    
    return {
        "creative_bible_id": str(creative_bible.id),
        "progress": len(collected),
        "collected_aspects": collected,
        "is_complete": len(collected) >= 5
    }


@router.post("/{brand_id}/chat/{creative_bible_id}")
async def send_chat_message(
    brand_id: str,
    creative_bible_id: str,
    message_request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a chat message and get agent response."""
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
        raise HTTPException(status_code=404, detail="Brand not found")
    
    creative_bible = db.query(CreativeBible).filter(
        CreativeBible.id == creative_bible_uuid,
        CreativeBible.brand_id == brand.id
    ).first()
    
    if not creative_bible:
        raise HTTPException(status_code=404, detail="Creative Bible not found")
    
    try:
        # Load existing chat messages first
        existing_messages = db.query(ChatMessage).filter(
            ChatMessage.creative_bible_id == creative_bible.id
        ).order_by(ChatMessage.created_at).all()
        
        # Store user message only if it's not empty (empty message is used to trigger initial greeting)
        if message_request.message.strip():
            user_message = ChatMessage(
                creative_bible_id=creative_bible.id,
                role="user",
                content=message_request.message
            )
            db.add(user_message)
            db.flush()  # Flush to get the message ID
        
        # Convert to format for agent (include the new user message if it was added)
        message_history = [
            {"role": msg.role, "content": msg.content}
            for msg in existing_messages
        ]
        if message_request.message.strip():
            message_history.append({"role": "user", "content": message_request.message})
        
        # Use cached agent or create new one
        cache_key = str(creative_bible.id)
        if cache_key in _agent_cache:
            agent = _agent_cache[cache_key]
            # Only reload conversation history if there are messages
            if message_history:
                agent.load_conversation_history(message_history)
            logger.debug(f"Using cached agent for creative_bible: {creative_bible.id}")
        else:
            # Initialize new agent
            agent = ChatAgent(
                brand_name=brand.title or "Product",
                brand_description=brand.description or ""
            )
            # Only load conversation history if there are messages
            if message_history:
                agent.load_conversation_history(message_history)
            # Cache the agent
            _agent_cache[cache_key] = agent
            logger.debug(f"Created and cached new agent for creative_bible: {creative_bible.id}")
        
        # Get current collected aspects from database
        collected = []
        aspect_map = {}
        if creative_bible.audience_description:
            collected.append("audience")
            aspect_map["audience"] = creative_bible.audience_description
        if creative_bible.style_description:
            collected.append("style")
            aspect_map["style"] = creative_bible.style_description
        if creative_bible.emotion_description:
            collected.append("emotion")
            aspect_map["emotion"] = creative_bible.emotion_description
        if creative_bible.pacing_description:
            collected.append("pacing")
            aspect_map["pacing"] = creative_bible.pacing_description
        if creative_bible.colors_description:
            collected.append("colors")
            aspect_map["colors"] = creative_bible.colors_description
        
        # Update agent's collected aspects
        agent.collected_aspects = collected
        agent.aspect_descriptions = aspect_map
        
        # Get the aspect we're currently asking about BEFORE processing
        # This is what the user is answering about
        current_aspect_being_answered = agent._get_next_aspect()

        # Process message - if no messages exist and message is empty, trigger initial greeting
        if len(message_history) == 0 and not message_request.message.strip():
            # Use template-based greeting for faster initialization (no API call)
            agent_response = agent.get_initial_greeting()
            next_aspect = agent._get_next_aspect()
            metadata = {
                "progress": len(collected),
                "collected_aspects": [ASPECT_NAMES.get(a, a) for a in collected],
                "next_aspect": ASPECT_NAMES.get(next_aspect, next_aspect) if next_aspect else None,
                "is_complete": len(collected) >= 5,
                "extracted_preferences": {}
            }
        else:
            # Process normal message
            agent_response, metadata = agent.process_message(message_request.message if message_request.message.strip() else "Continue")

        # Try to extract preference if user provided a meaningful response to the current aspect
        # Use the aspect we captured BEFORE processing (what the user was answering about)
        if current_aspect_being_answered and current_aspect_being_answered not in collected:
            # Check if user provided a meaningful response (not just "yes" or "ok")
            # Allow short answers like "young", "bold", "fast", "blue" etc.
            user_msg_lower = message_request.message.lower().strip()
            if len(user_msg_lower) > 2 and user_msg_lower not in ["yes", "ok", "sure", "yeah", "yep", "nope", "no"]:
                # Extract and store preference for the aspect the user was answering about
                preference = agent.extract_and_store_preference(current_aspect_being_answered, message_request.message)
                if preference:
                    # Update creative bible
                    if current_aspect_being_answered == "audience":
                        creative_bible.audience_description = preference["description"]
                        creative_bible.audience_keywords = preference["keywords"]
                    elif current_aspect_being_answered == "style":
                        creative_bible.style_description = preference["description"]
                        creative_bible.style_keywords = preference["keywords"]
                    elif current_aspect_being_answered == "emotion":
                        creative_bible.emotion_description = preference["description"]
                        creative_bible.emotion_keywords = preference["keywords"]
                    elif current_aspect_being_answered == "pacing":
                        creative_bible.pacing_description = preference["description"]
                        creative_bible.pacing_keywords = preference["keywords"]
                    elif current_aspect_being_answered == "colors":
                        creative_bible.colors_description = preference["description"]
                        creative_bible.colors_keywords = preference["keywords"]
        
        # Store agent response
        assistant_message = ChatMessage(
            creative_bible_id=creative_bible.id,
            role="assistant",
            content=agent_response
        )
        db.add(assistant_message)
        
        db.commit()
        
        # Update metadata with actual progress
        collected_after = []
        if creative_bible.audience_description:
            collected_after.append("audience")
        if creative_bible.style_description:
            collected_after.append("style")
        if creative_bible.emotion_description:
            collected_after.append("emotion")
        if creative_bible.pacing_description:
            collected_after.append("pacing")
        if creative_bible.colors_description:
            collected_after.append("colors")
        
        metadata["progress"] = len(collected_after)
        metadata["collected_aspects"] = collected_after
        metadata["is_complete"] = len(collected_after) >= 5
        
        return {
            "message": agent_response,
            "metadata": metadata
        }
    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to process message. Please try again.")


@router.get("/{brand_id}/chat/{creative_bible_id}/messages")
async def get_chat_messages(
    brand_id: str,
    creative_bible_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chat message history."""
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
        raise HTTPException(status_code=404, detail="Brand not found")
    
    creative_bible = db.query(CreativeBible).filter(
        CreativeBible.id == creative_bible_uuid,
        CreativeBible.brand_id == brand.id
    ).first()
    
    if not creative_bible:
        raise HTTPException(status_code=404, detail="Creative Bible not found")
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.creative_bible_id == creative_bible.id
    ).order_by(ChatMessage.created_at).all()
    
    return {
        "messages": [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ]
    }


@router.post("/{brand_id}/chat/{creative_bible_id}/complete")
async def complete_chat(
    brand_id: str,
    creative_bible_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark chat as complete and finalize preferences."""
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
        raise HTTPException(status_code=404, detail="Brand not found")

    creative_bible = db.query(CreativeBible).filter(
        CreativeBible.id == creative_bible_uuid,
        CreativeBible.brand_id == brand.id
    ).first()

    if not creative_bible:
        raise HTTPException(status_code=404, detail="Creative Bible not found")

    # Verify all 5 aspects are collected
    collected = []
    if creative_bible.audience_description:
        collected.append("audience")
    if creative_bible.style_description:
        collected.append("style")
    if creative_bible.emotion_description:
        collected.append("emotion")
    if creative_bible.pacing_description:
        collected.append("pacing")
    if creative_bible.colors_description:
        collected.append("colors")

    if len(collected) < 5:
        raise HTTPException(
            status_code=400,
            detail=f"Not all preferences collected. Missing: {set(['audience', 'style', 'emotion', 'pacing', 'colors']) - set(collected)}"
        )

    # Chat is complete - preferences are already stored
    return {
        "creative_bible_id": str(creative_bible.id),
        "message": "Chat completed successfully",
        "preferences": {
            "audience": {
                "description": creative_bible.audience_description,
                "keywords": creative_bible.audience_keywords or []
            },
            "style": {
                "description": creative_bible.style_description,
                "keywords": creative_bible.style_keywords or []
            },
            "emotion": {
                "description": creative_bible.emotion_description,
                "keywords": creative_bible.emotion_keywords or []
            },
            "pacing": {
                "description": creative_bible.pacing_description,
                "keywords": creative_bible.pacing_keywords or []
            },
            "colors": {
                "description": creative_bible.colors_description,
                "keywords": creative_bible.colors_keywords or []
            }
        }
    }


class UpdateStorylineRequest(BaseModel):
    scene_number: int = Field(gt=0, le=10, description="Scene number must be between 1 and 10")
    description: str = Field(min_length=10, max_length=2000, description="Scene description must be 10-2000 characters")
    last_modified: Optional[str] = Field(None, description="Timestamp of last known modification for optimistic locking")

    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v: str) -> str:
        """Sanitize description to prevent prompt injection."""
        # Validate first
        validate_user_input(v, "description", min_length=10, max_length=2000)
        # Then sanitize
        sanitized = sanitize_scene_description(v)
        if not sanitized or len(sanitized) < 10:
            raise ValueError("Description too short after sanitization")
        return sanitized


@router.put("/{brand_id}/storyline/{creative_bible_id}")
async def update_storyline(
    brand_id: str,
    creative_bible_id: str,
    update_request: UpdateStorylineRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a scene description in the creative bible storyline."""
    logger.info(f"Updating storyline scene {update_request.scene_number} for creative_bible: {creative_bible_id}")

    try:
        brand_uuid = uuid.UUID(brand_id)
        creative_bible_uuid = uuid.UUID(creative_bible_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    try:
        brand = db.query(Brand).filter(
            Brand.id == brand_uuid,
            Brand.user_id == current_user.id
        ).first()

        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")

        creative_bible = db.query(CreativeBible).filter(
            CreativeBible.id == creative_bible_uuid,
            CreativeBible.brand_id == brand.id
        ).first()

        if not creative_bible:
            raise HTTPException(status_code=404, detail="Creative Bible not found")

        if not creative_bible.creative_bible or "storyline" not in creative_bible.creative_bible:
            raise HTTPException(status_code=400, detail="No storyline found in creative bible")

        # Optimistic locking: Check if storyline was modified since client last loaded it
        if update_request.last_modified and creative_bible.updated_at:
            client_timestamp = update_request.last_modified
            server_timestamp = creative_bible.updated_at.isoformat()
            if client_timestamp != server_timestamp:
                logger.warning(f"Concurrent edit detected for creative_bible {creative_bible_id}")
                raise HTTPException(
                    status_code=409,
                    detail=f"Storyline was modified by another session. Please refresh and try again. (Client: {client_timestamp}, Server: {server_timestamp})"
                )

        # Get current creative bible data
        creative_bible_data = creative_bible.creative_bible.copy()
        storyline = creative_bible_data.get("storyline", {})
        scenes = storyline.get("scenes", [])

        # Validate scenes exist
        if not scenes:
            raise HTTPException(status_code=400, detail="No scenes found in storyline")

        # Find and update the scene
        scene_found = False
        for scene in scenes:
            if scene.get("scene_number") == update_request.scene_number:
                # Update description (already sanitized by Pydantic validator)
                scene["description"] = update_request.description
                scene_found = True
                logger.info(f"Updated scene {update_request.scene_number} description for user {current_user.id}")
                break

        if not scene_found:
            available_scenes = [s.get("scene_number") for s in scenes]
            raise HTTPException(
                status_code=404,
                detail=f"Scene {update_request.scene_number} not found. Available scenes: {available_scenes}"
            )

        # Regenerate sora_prompts with updated description
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

        # Update creative bible data
        creative_bible_data["storyline"]["scenes"] = scenes
        creative_bible_data["sora_prompts"] = sora_prompts

        # Save to database
        creative_bible.creative_bible = creative_bible_data
        # updated_at will be automatically set by SQLAlchemy onupdate
        db.commit()
        db.refresh(creative_bible)

        logger.info(f"Updated scene {update_request.scene_number} in creative_bible: {creative_bible_id}")

        return {
            "storyline": creative_bible_data.get("storyline", {}),
            "sora_prompts": sora_prompts,
            "updated_at": creative_bible.updated_at.isoformat() if creative_bible.updated_at else None
        }
    except HTTPException:
        # Re-raise HTTPExceptions (validation errors, 404s, etc.)
        raise
    except Exception as e:
        logger.error(f"Error updating storyline for creative_bible {creative_bible_id}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update storyline. Please try again.")


@router.post("/{brand_id}/storyline/{creative_bible_id}/revert")
async def revert_storyline(
    brand_id: str,
    creative_bible_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revert storyline to original AI-generated version."""
    logger.info(f"Reverting storyline for creative_bible: {creative_bible_id}")

    try:
        brand_uuid = uuid.UUID(brand_id)
        creative_bible_uuid = uuid.UUID(creative_bible_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    try:
        brand = db.query(Brand).filter(
            Brand.id == brand_uuid,
            Brand.user_id == current_user.id
        ).first()

        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")

        creative_bible = db.query(CreativeBible).filter(
            CreativeBible.id == creative_bible_uuid,
            CreativeBible.brand_id == brand.id
        ).first()

        if not creative_bible:
            raise HTTPException(status_code=404, detail="Creative Bible not found")

        if not creative_bible.original_creative_bible:
            raise HTTPException(status_code=400, detail="No original storyline found to revert to")

        # Revert to original
        creative_bible.creative_bible = creative_bible.original_creative_bible.copy()
        db.commit()
        db.refresh(creative_bible)

        logger.info(f"Reverted storyline to original for creative_bible: {creative_bible_id}")

        return {
            "message": "Storyline reverted to original",
            "storyline": creative_bible.creative_bible.get("storyline", {}),
            "sora_prompts": creative_bible.creative_bible.get("sora_prompts", [])
        }
    except HTTPException:
        # Re-raise HTTPExceptions (validation errors, 404s, etc.)
        raise
    except Exception as e:
        logger.error(f"Error reverting storyline for creative_bible {creative_bible_id}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to revert storyline. Please try again.")

