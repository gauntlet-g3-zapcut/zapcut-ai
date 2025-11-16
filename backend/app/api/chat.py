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

    print(f"\n{'='*80}")
    print(f"📖 GET STORYLINE - Request received")
    print(f"{'='*80}")
    print(f"   Brand ID: {brand_id}")
    print(f"   Creative Bible ID: {creative_bible_id}")
    print(f"   Current User ID: {current_user.id if current_user else 'None'}")
    print(f"   Current User Email: {current_user.email if current_user else 'None'}")
    print(f"{'='*80}\n")

    # Get brand
    print(f"📋 Step 1: Looking up brand")
    print(f"   Brand ID: {brand_id}")
    print(f"   User ID filter: {current_user.id}")

    brand = db.query(Brand).filter(
        Brand.id == uuid.UUID(brand_id),
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

    print(f"✅ Brand found: {brand.title} (ID: {brand.id}, User: {brand.user_id})")

    # Handle creative_bible_id (may be "default" string or UUID)
    print(f"\n📋 Step 2: Looking up creative bible")
    print(f"   Creative Bible ID: {creative_bible_id}")

    if creative_bible_id == "default":
        # Look for a creative bible with name="default"
        print(f"   🔍 Looking for creative bible with name='default'")
        creative_bible = db.query(CreativeBible).filter(
            CreativeBible.brand_id == brand.id,
            CreativeBible.name == "default"
        ).first()
    else:
        # Try to parse as UUID
        try:
            creative_bible_uuid = uuid.UUID(creative_bible_id)
            print(f"   🔍 Looking for creative bible with UUID: {creative_bible_uuid}")
            creative_bible = db.query(CreativeBible).filter(
                CreativeBible.id == creative_bible_uuid,
                CreativeBible.brand_id == brand.id
            ).first()
        except ValueError as e:
            print(f"   ❌ ERROR: Invalid creative_bible_id format: {creative_bible_id}")
            print(f"   ValueError: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid creative_bible_id format")

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

    print(f"✅ Creative Bible found: {creative_bible.id} (Brand: {creative_bible.brand_id})")
    
    # Check if creative_bible already has data, if not generate it
    print(f"\n📋 Step 3: Checking if creative bible has data")
    bible_data = creative_bible.creative_bible or {}
    print(f"   Bible data keys: {list(bible_data.keys()) if bible_data else 'Empty'}")

    if not bible_data or not bible_data.get("brand_style"):
        print(f"   ℹ️  Creative bible needs generation (missing data)")

        brand_info = {
            "title": brand.title,
            "description": brand.description
        }

        # Generate Creative Bible from answers
        print(f"\n📋 Step 4: Generating creative bible and storyline")
        answers = creative_bible.conversation_history  # This contains the structured answers
        print(f"   User answers: {answers}")

        try:
            print(f"   🤖 Calling OpenAI to generate creative bible...")
            creative_bible_data = generate_creative_bible_from_answers(answers, brand_info)
            print(f"   ✅ Creative bible generated")

            print(f"   🤖 Calling OpenAI to generate storyline...")
            # Generate storyline
            storyline_data = generate_storyline_and_prompts(creative_bible_data, brand_info)
            print(f"   ✅ Storyline generated")
        except Exception as e:
            print(f"   ❌ ERROR: OpenAI generation failed")
            print(f"   Exception type: {type(e).__name__}")
            print(f"   Exception message: {str(e)}")
            import traceback
            print(f"   Traceback:\n{traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate storyline: {str(e)}"
            )

        print(f"   📝 Updating creative bible with generated data...")
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

        try:
            db.commit()
            db.refresh(creative_bible)
            print(f"   ✅ Creative bible updated in database")
        except Exception as e:
            print(f"   ❌ ERROR: Failed to save to database")
            print(f"   Exception: {str(e)}")
            db.rollback()
            raise

        # Reload bible_data after generation
        bible_data = creative_bible.creative_bible or {}
    else:
        print(f"   ✅ Creative bible already has data, using existing")

    print(f"\n✅ SUCCESS: Returning storyline data")
    print(f"   Storyline scenes: {len(bible_data.get('storyline', {}).get('scenes', []))}")
    print(f"{'='*80}\n")

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

