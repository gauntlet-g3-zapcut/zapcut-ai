from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.brand import Brand
from app.models.creative_bible import CreativeBible
from app.api.auth import get_current_user
from app.services.openai_service import generate_creative_bible_from_answers, generate_storyline_and_prompts
import uuid

router = APIRouter(prefix="/api/brands", tags=["chat"])

# Questions with clickable options
QUESTIONS = [
    {
        "question": "How do you want this ad to look and feel?",
        "options": ["Modern & Sleek", "Energetic & Fun", "Luxurious & Sophisticated", "Minimal & Clean", "Bold & Dramatic"]
    },
    {
        "question": "Who is your target audience?",
        "options": ["Young Adults (18-25)", "Professionals (25-40)", "Families", "Seniors (50+)", "Everyone"]
    },
    {
        "question": "What's the key message or emotion you want viewers to feel?",
        "options": ["Excitement", "Trust & Reliability", "Joy & Happiness", "Luxury & Prestige", "Innovation"]
    },
    {
        "question": "What should be the pacing and energy?",
        "options": ["Fast-paced & Exciting", "Slow & Elegant", "Dynamic Build-up", "Steady & Calm"]
    },
    {
        "question": "What colors or visual style do you prefer?",
        "options": ["Bold & Vibrant", "Dark & Moody", "Light & Airy", "Natural & Earthy", "Match Product Colors"]
    }
]


class CampaignAnswers(BaseModel):
    answers: dict


@router.post("/{brand_id}/campaign-answers")
async def submit_campaign_answers(
    brand_id: str,
    campaign_answers: CampaignAnswers,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit all campaign answers at once"""
    # Get brand
    brand = db.query(Brand).filter(
        Brand.id == uuid.UUID(brand_id),
        Brand.user_id == current_user.id
    ).first()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Validate that all 5 questions are answered
    required_keys = ["style", "audience", "emotion", "pacing", "colors"]
    if not all(key in campaign_answers.answers for key in required_keys):
        raise HTTPException(status_code=400, detail="All questions must be answered")
    
    # Create creative bible with the answers
    creative_bible = CreativeBible(
        brand_id=brand.id,
        name=f"campaign_{uuid.uuid4().hex[:8]}",
        creative_bible={},
        reference_image_urls={},
        conversation_history=campaign_answers.answers  # Store answers in conversation_history
    )
    db.add(creative_bible)
    db.commit()
    
    return {
        "creative_bible_id": str(creative_bible.id),
        "message": "Campaign preferences saved successfully"
    }




@router.get("/{brand_id}/storyline/{creative_bible_id}")
async def get_storyline(
    brand_id: str,
    creative_bible_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get or generate storyline from creative bible"""
    # Get brand
    brand = db.query(Brand).filter(
        Brand.id == uuid.UUID(brand_id),
        Brand.user_id == current_user.id
    ).first()

    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    # Handle creative_bible_id (may be "default" string or UUID)
    if creative_bible_id == "default":
        # Look for a creative bible with name="default"
        creative_bible = db.query(CreativeBible).filter(
            CreativeBible.brand_id == brand.id,
            CreativeBible.name == "default"
        ).first()
    else:
        # Try to parse as UUID
        try:
            creative_bible_uuid = uuid.UUID(creative_bible_id)
            creative_bible = db.query(CreativeBible).filter(
                CreativeBible.id == creative_bible_uuid,
                CreativeBible.brand_id == brand.id
            ).first()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid creative_bible_id format")

    if not creative_bible:
        raise HTTPException(status_code=404, detail="Creative Bible not found")
    
    # Check if creative_bible already has data, if not generate it
    bible_data = creative_bible.creative_bible or {}
    if not bible_data or not bible_data.get("brand_style"):
        brand_info = {
            "title": brand.title,
            "description": brand.description
        }
        
        # Generate Creative Bible from answers
        answers = creative_bible.conversation_history  # This contains the structured answers
        creative_bible_data = generate_creative_bible_from_answers(answers, brand_info)
        
        # Generate storyline
        storyline_data = generate_storyline_and_prompts(creative_bible_data, brand_info)
        
        # Update creative bible with both creative bible and storyline
        creative_bible.creative_bible = {
            **creative_bible_data,
            "storyline": storyline_data["storyline"],
            "suno_prompt": storyline_data.get("suno_prompt", "")
        }
        creative_bible.name = f"{creative_bible_data.get('brand_style', 'custom')}_{uuid.uuid4().hex[:8]}"
        
        # Store reference images (user uploaded)
        creative_bible.reference_image_urls = {
            "user_1": brand.product_image_1_url,
            "user_2": brand.product_image_2_url,
            "hero": "",
            "detail": "",
            "lifestyle": ""
        }
        
        db.commit()
        db.refresh(creative_bible)
        # Reload bible_data after generation
        bible_data = creative_bible.creative_bible or {}

    return {
        "creative_bible": {
            "brand_style": bible_data.get("brand_style"),
            "vibe": bible_data.get("vibe"),
            "colors": bible_data.get("colors", []),
            "energy_level": bible_data.get("energy_level")
        },
        "storyline": bible_data.get("storyline", {}),
        "suno_prompt": bible_data.get("suno_prompt", "")
    }

