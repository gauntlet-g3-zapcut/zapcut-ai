# AdCraft AI - MVP PRD

**Duration:** 24 hours  
**Focus:** Video + Music generation with consistent creative direction  
**Scope:** Minimal MVP with conversational brief interface

---

## 1. USER FLOW

### Screen 1: Landing Page
- **Content:** Hero section, value proposition, "Get Started" button
- **Action:** Click "Get Started" → Navigate to Login

### Screen 2: Login/Auth
- **Method:** Firebase Authentication
- **Options:** Email/Password, Google OAuth
- **Action:** After login → Redirect to Brands Dashboard

### Screen 3: Brands Dashboard
- **Left Sidebar:**
  - User profile info
  - Navigation menu
  - Credits/usage info
- **Main Area:**
  - Header: "Brands" with count
  - Grid/list of existing brands (cards with brand image, title, description, campaign count)
  - "Create Brand +" button (prominent)
- **Action:** Click brand card → Navigate to Brand Chat | Click "Create Brand" → Navigate to Create Brand

### Screen 4: Create Brand
- **Required Fields:**
  - Title (text input)
  - Description (textarea)
  - Product Image 1 (file upload)
  - Product Image 2 (file upload)
- **Action:** Submit → Store brand → Navigate to Brand Chat for that brand

### Screen 5: Brand Chat (Conversational Brief)
- **Interface:** Chat UI with message history
- **Flow:**
  1. User sends initial brief: "I want a [style] ad for my product"
  2. LLM (acting as creative director) asks follow-up questions **one at a time**
  3. User can answer, go back to previous questions, or skip
  4. After ~5 questions, LLM confirms brief is complete
- **Action:** Brief complete → Navigate to Storyline/Script Review

### Screen 6: Storyline/Script Review
- **Content:** 
  - Generated storyline/script split into scenes
  - Each scene shows: description, timing, energy level
  - Suno soundtrack prompt preview
- **Actions:**
  - "Approve" button → Start video generation
  - "Edit" button → Go back to chat (optional for MVP)
- **Action:** Click "Approve" → Navigate to Video Generation (progress)

### Screen 7: Video Generation (Progress)
- **Content:**
  - Progress indicator showing current stage:
    - Generating reference images...
    - Creating storyboard...
    - Generating video scenes (1/5, 2/5, etc.)...
    - Generating soundtrack...
    - Composing final video...
  - ETA/estimated time remaining
- **Action:** Generation completes → Navigate to Video Player

### Screen 8: Video Player with Editing
- **Content:**
  - 4K video player (autoplay preview)
  - Basic editing controls:
    - Play/Pause
    - Download MP4
    - Download WebM
    - Share link
    - (Optional: basic trim, text overlay adjustments)
- **Action:** User can create another campaign/ad for same brand → Returns to Brand Chat

---

## 2. BACKEND WORKFLOW

### Path A: New Campaign (First ad for brand)

```
1. User submits brief via chat + brand_id

   ↓

2. LLM (Creative Director) asks follow-up questions
   - Gathers: style, vibe, target audience, key message, tone
   - Stores conversation in database

   ↓

3. User approves brief → Generate Creative Bible (LLM)
   ├─ Extract style, vibe, energy from conversation
   ├─ Lock colors, mood, motion
   └─ Store Creative Bible in database

   ↓

4. Generate Storyline/Script (LLM - Creative Director)
   ├─ Split into 5 scenes
   ├─ Each scene: description, timing, energy progression
   └─ Generate Suno prompt with specific transitions and timing

   ↓

5. Generate Reference Images (PARALLEL)
   ├─ Use user-uploaded images (2) as base
   ├─ Replicate API: Generate 2-3 additional reference images
   │  └─ Best model on Replicate (e.g., Flux, SDXL, etc.)
   ├─ Total: 4-5 reference images
   └─ All match Creative Bible style

   ↓

6. Generate Sora Prompts (LLM) (PARALLEL)
   └─ 5 prompts (1 per scene) with Creative Bible + reference image URLs

   ↓

7. Call Generation APIs in PARALLEL:
   ├─ Sora (Replicate): Generate 5 video scenes (2-3 min)
   └─ Suno (Replicate): Generate 1 music track (1-2 min)

   ↓

8. Compose Video
   ├─ Download 5 video clips from Sora
   ├─ Download audio from Suno
   ├─ FFmpeg:
   │  ├─ Stitch 5 scenes with 0.5s crossfade
   │  ├─ Mix Suno audio underneath
   │  ├─ Add text overlay: Brand name (appears at 24s)
   │  ├─ Add text overlay: "Learn More" (appears at 27s)
   │  └─ Encode to H.264, 4K (3840x2160), 30fps
   └─ Upload to S3

   ↓

9. Store Campaign in database
   ├─ Campaign tied to brand_id + creative_bible_id
   └─ Video URLs stored
```

### Path B: Reuse Creative Bible (Subsequent campaigns for same brand + style)

```
1. User selects existing Creative Bible + brand_id
   OR
   User creates new campaign with same style

   ↓

2. Retrieve Creative Bible + Reference Images from database
   ├─ Skip LLM generation (FAST)
   └─ Reference images already cached

   ↓

3. Generate NEW Storyline/Script (LLM)
   └─ Different storyboard, same Creative Bible

   ↓

4. Generate Sora Prompts (using cached reference images)

   ↓

5. Generate Suno Prompt (new, matching new storyboard)

   ↓

6. Call Generation APIs (same as Path A, steps 7-9)
   ├─ Sora: 2-3 min
   └─ Suno: 1-2 min

   ↓

7. Store Campaign in database
   ├─ Same creative_bible_id
   └─ New campaign_id
```

**Speed difference:**
- Path A (new Bible): 4-5 minutes (LLM calls + Replicate images + Sora + Suno)
- Path B (reuse Bible): 3 minutes (only Sora + Suno, no LLM/Replicate)

---

## 3. REFERENCE IMAGE GENERATION

**Step 1: Use user-uploaded images**
- Brand creation provides 2 product images
- These serve as base reference images

**Step 2: Generate additional reference images via Replicate**
- **Model Selection:** Best available model on Replicate (e.g., Flux Pro, SDXL, etc.)
- **Prompt Generation (LLM):**
  ```
  Based on Creative Bible + user images, generate prompts for:
  - Hero shot (product centered, premium)
  - Detail shot (close-up, texture focus)
  - Lifestyle shot (product in context)
  - Alternate angle (different perspective)
  ```
- **Generation:** 2-3 additional images via Replicate API (parallel)
- **Total:** 4-5 reference images stored, URLs passed to Sora prompts

**Result:** Consistent visual style across all reference images, locked by Creative Bible

---

## 4. CREATIVE DIRECTOR LLM PROMPT

**System Prompt:**
```
You are an expert creative director specializing in product advertisement videos.

Your role:
1. Ask thoughtful follow-up questions (one at a time) to understand:
   - Visual style preferences
   - Target audience
   - Key message/emotion
   - Tone (energetic, sophisticated, minimal, etc.)
   - Color preferences
   - Motion style

2. After gathering information, create a comprehensive Creative Bible:
   - Brand style
   - Vibe/energy
   - Color palette (hex codes)
   - Lighting style
   - Camera movement
   - Motion characteristics
   - Energy level (1-10)

3. Generate a detailed storyline/script:
   - Split into 5 scenes (6 seconds each = 30s total)
   - Each scene: title, description, energy progression, visual notes
   - Ensure narrative flow and visual consistency

4. Generate Suno soundtrack prompt:
   - Match vibe and energy of Creative Bible
   - Specify exact timing for transitions (0-6s, 6-12s, etc.)
   - Match energy levels to scene progression
   - Include tempo, instrumentation, no vocals
   - Be VERY specific about transitions and seconds

Ask questions one at a time. Wait for user response before asking the next.
```

---

## 5. STORYLINE/SCRIPT FORMAT

**LLM Output:**
```json
{
  "creative_bible": {
    "brand_style": "modern",
    "vibe": "energetic",
    "colors": ["#00b4ff", "#1a1a1a", "#ffffff"],
    "lighting": "bright, high-contrast",
    "camera": "dynamic, fast movements",
    "motion": "energetic, constant movement",
    "energy_level": "high"
  },
  "storyline": {
    "total_duration": 30,
    "scenes": [
      {
        "scene_number": 1,
        "title": "Product Reveal",
        "duration": 6,
        "start_time": 0,
        "end_time": 6,
        "description": "Product zooms into frame on white background, dramatic reveal",
        "energy_start": 3,
        "energy_end": 5,
        "visual_notes": "Clean, centered, premium feel"
      },
      {
        "scene_number": 2,
        "title": "Detail Close-Up",
        "duration": 6,
        "start_time": 6,
        "end_time": 12,
        "description": "Extreme close-up of product details, showcasing craftsmanship",
        "energy_start": 5,
        "energy_end": 6,
        "visual_notes": "Dynamic lighting, texture focus"
      },
      {
        "scene_number": 3,
        "title": "Action/Motion",
        "duration": 6,
        "start_time": 12,
        "end_time": 18,
        "description": "Product in motion, energetic use, dynamic angles",
        "energy_start": 6,
        "energy_end": 8,
        "visual_notes": "Fast motion, multiple angles"
      },
      {
        "scene_number": 4,
        "title": "Lifestyle",
        "duration": 6,
        "start_time": 18,
        "end_time": 24,
        "description": "Product integrated into lifestyle, real-world context",
        "energy_start": 7,
        "energy_end": 8,
        "visual_notes": "Premium environment, aspirational"
      },
      {
        "scene_number": 5,
        "title": "CTA",
        "duration": 6,
        "start_time": 24,
        "end_time": 30,
        "description": "Final product shot, 'Learn More' text appears",
        "energy_start": 8,
        "energy_end": 6,
        "visual_notes": "Hero shot, clean, professional"
      }
    ]
  },
  "suno_prompt": "Create an energetic background music track for a product ad. Duration: 30 seconds exactly. Style: modern electronic/cinematic. Vibe: energetic, dynamic. Energy Level: high. Tempo: 120-140 BPM. No vocals. Professional commercial quality. Music Structure: 0-6s (Scene 1 - Product Reveal): Energy building from 3 to 5/10, establishing beat, subtle intro. 6-12s (Scene 2 - Detail): Energy 5 to 6/10, maintain energy with subtle intensity shift, add texture. 12-18s (Scene 3 - Action): Energy 6 to 8/10, peak energy section, dynamic movement, driving rhythm. 18-24s (Scene 4 - Lifestyle): Energy 7 to 8/10, sustain peak, premium feeling, full instrumentation. 24-30s (Scene 5 - CTA): Energy 8 to 9/10 at 27s (climax), then resolve to 6/10 for ending, clean finish. Transitions: Smooth crossfade at 6s, subtle build at 12s, dynamic shift at 18s, maintain at 24s, resolve at 27s. Make the music RHYTHMIC with clear progression matching the energy levels."
}
```

---

## 6. SORA PROMPTS (Scene Prompts)

**Template for each scene:**
```
SCENE [N] PROMPT

Creative Direction (locked):
- Style: {creative_bible.brand_style}
- Vibe: {creative_bible.vibe}
- Colors: {creative_bible.colors}
- Lighting: {creative_bible.lighting}
- Camera: {creative_bible.camera}
- Motion: {creative_bible.motion}

Reference Images (style anchors):
- User Image 1: {user_image_1_url}
- User Image 2: {user_image_2_url}
- Generated Hero: {reference_image_urls.hero}
- Generated Detail: {reference_image_urls.detail}
- Generated Lifestyle: {reference_image_urls.lifestyle}

Scene [N]: {storyline.scenes[n].title}
Duration: 6 seconds at 30fps
Description: {storyline.scenes[n].description}
Energy: {storyline.scenes[n].energy_start} → {storyline.scenes[n].energy_end}

Product: {brand.product_name}

Requirements:
- Use reference images as visual style guide
- Maintain EXACT product appearance from user-uploaded images
- Use ONLY the locked colors above
- Keep {creative_bible.motion} motion style
- Match energy progression: {storyline.scenes[n].energy_start} to {storyline.scenes[n].energy_end}
- Professional, cinematic quality
- Follow visual notes: {storyline.scenes[n].visual_notes}

Generate video matching all constraints above.
```

**5 prompts sent to Sora (Replicate) in parallel, each with reference image URLs included.**

---

## 7. API CALLS SUMMARY

| API | Purpose | Count | Time |
|-----|---------|-------|------|
| OpenAI (GPT-4) | Creative Director Q&A | 5-7 calls | 30-45s |
| OpenAI (GPT-4) | Creative Bible | 1 call | 5s |
| OpenAI (GPT-4) | Storyline/Script + Suno Prompt | 1 call | 10s |
| OpenAI (GPT-4) | Reference Image Prompts | 1 call | 5s |
| OpenAI (GPT-4) | Sora Prompts | 1 call | 5s |
| Replicate | Reference Images | 2-3 calls (parallel) | 30-60s |
| Sora (Replicate) | Video scenes | 5 calls (parallel) | 2-3 min |
| Suno (Replicate) | Music track | 1 call | 1-2 min |
| **TOTAL** | | | **4-5 min** |

**Note:** Reference images, Storyline, Sora Prompts, and Suno Prompt generation can happen in parallel after Creative Bible is created.

---

## 8. DATABASE SCHEMA

```sql
-- Users (Firebase Auth handles auth, we store minimal user data)
CREATE TABLE users (
  id UUID PRIMARY KEY,
  firebase_uid VARCHAR UNIQUE NOT NULL,
  email VARCHAR UNIQUE NOT NULL,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Brands (Products)
CREATE TABLE brands (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  title VARCHAR NOT NULL,
  description TEXT,
  product_image_1_url VARCHAR NOT NULL,
  product_image_2_url VARCHAR NOT NULL,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Creative Bibles (one per brand + style combination)
CREATE TABLE creative_bibles (
  id UUID PRIMARY KEY,
  brand_id UUID NOT NULL REFERENCES brands(id),
  name VARCHAR NOT NULL, -- e.g., "modern_minimalist_v1", "energetic_dynamic_v2"
  creative_bible JSONB NOT NULL, -- {colors, vibe, style, lighting, camera, motion, energy_level}
  reference_image_urls JSONB NOT NULL, -- {user_1, user_2, hero, detail, lifestyle, alternate}
  conversation_history JSONB, -- Store Q&A conversation
  created_at TIMESTAMP,
  
  UNIQUE(brand_id, name) -- Can't have duplicate Bible names per brand
);

-- Campaigns (Ads)
CREATE TABLE campaigns (
  id UUID PRIMARY KEY,
  brand_id UUID NOT NULL REFERENCES brands(id),
  creative_bible_id UUID NOT NULL REFERENCES creative_bibles(id),
  storyline JSONB NOT NULL, -- Full storyline/script with scenes
  sora_prompts JSONB NOT NULL, -- Array of 5 prompts
  suno_prompt TEXT NOT NULL,
  video_urls JSONB, -- {scene_1, scene_2, ..., scene_5} S3 URLs
  music_url VARCHAR, -- S3 URL
  final_video_url VARCHAR NOT NULL, -- S3 URL
  status VARCHAR NOT NULL DEFAULT 'pending', -- pending, generating, completed, failed
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Indexes for fast queries
CREATE INDEX idx_brands_user_id ON brands(user_id);
CREATE INDEX idx_creative_bibles_brand_id ON creative_bibles(brand_id);
CREATE INDEX idx_campaigns_brand_id ON campaigns(brand_id);
CREATE INDEX idx_campaigns_creative_bible_id ON campaigns(creative_bible_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);
```

---

## 9. TECH STACK

| Layer | Tech |
|-------|------|
| Frontend | React (Vite or Create React App) |
| Frontend Framework | Next.js (optional, for SSR if needed) |
| Authentication | Firebase Auth |
| Backend | FastAPI (Python) |
| Task Queue | Celery + Redis |
| Database | PostgreSQL |
| Storage | S3 (AWS) |
| LLM | OpenAI (GPT-4) |
| Image Gen | Replicate (best model available) |
| Video Gen | Sora 2 (Replicate) |
| Music Gen | Suno (Replicate) |
| Video Composition | FFmpeg |
| Deployment | Railway (Backend), Vercel/Netlify (Frontend) |

---

## 10. WHAT'S NOT IN MVP

❌ LoRA training  
❌ Advanced video editing (brush tool, color grading)  
❌ Voiceover/TTS  
❌ Multiple variations generation  
❌ Text overlay customization beyond basic  
❌ Audio editing  
❌ Brand kit management UI  
❌ Campaign history/comparison  
❌ User collaboration  
❌ Analytics/insights  

---

## 11. CRITICAL SUCCESS CRITERIA

✅ **Generation completes in < 5 minutes**  
✅ **Video and audio feel cohesive** (music matches energy of scenes with precise timing)  
✅ **Product looks consistent across all 5 scenes**  
✅ **4K quality output**  
✅ **Error handling** (retry logic, graceful failures)  
✅ **UI shows progress** (current stage + ETA)  
✅ **Chat interface feels natural** (one question at a time, can go back)  
✅ **Storyline/script is clear and actionable**  

---

## 12. TIMELINE (24 HOURS)

**Hours 1-4: Setup & Auth**
- [ ] Project scaffold (React + FastAPI)
- [ ] Firebase Auth integration
- [ ] Database setup (PostgreSQL schema)
- [ ] Railway deployment setup

**Hours 5-8: Core UI**
- [ ] Landing page
- [ ] Login/Auth flow
- [ ] Brands Dashboard
- [ ] Create Brand form
- [ ] Basic routing

**Hours 9-12: Chat & Generation**
- [ ] Chat interface (React)
- [ ] LLM integration (OpenAI GPT-4 - Creative Director)
- [ ] Storyline/script review page
- [ ] Celery task queue setup

**Hours 13-16: Video Generation Pipeline**
- [ ] Replicate API integration (images, Sora, Suno)
- [ ] Reference image generation
- [ ] Sora video generation (5 scenes)
- [ ] Suno music generation
- [ ] FFmpeg composition
- [ ] S3 upload

**Hours 17-20: Video Player & Polish**
- [ ] Video player with basic controls
- [ ] Download functionality
- [ ] Share link generation
- [ ] Progress tracking UI
- [ ] Error handling

**Hours 21-24: Testing & Deploy**
- [ ] End-to-end testing (3 sample brands)
- [ ] Bug fixes
- [ ] Deploy to Railway (backend)
- [ ] Deploy to Vercel (frontend)
- [ ] Final polish

---

## 13. SAMPLE EXECUTION

**User Input:**
```
Brand: "Luxury Coffee Maker"
Description: "Premium espresso machine for coffee enthusiasts"
Images: 2 product photos uploaded

Chat Brief:
User: "I want a modern, sleek, minimalist ad"
LLM: "What emotion should viewers feel when they see this ad?"
User: "Sophisticated and aspirational"
LLM: "Who is your target audience?"
User: "Coffee enthusiasts, 30-50, urban professionals"
LLM: "What's the key message you want to convey?"
User: "Quality craftsmanship and premium experience"
LLM: "Any specific colors you want to emphasize?"
User: "Black, white, and warm gold accents"
LLM: "Perfect! I have everything I need. Generating your ad..."
```

**Creative Bible (Generated):**
```json
{
  "brand_style": "minimalist",
  "vibe": "sophisticated",
  "colors": ["#2c2c2c", "#ffffff", "#d4af37"],
  "lighting": "soft, warm, studio",
  "camera": "smooth, deliberate movements",
  "motion": "slow, refined",
  "energy_level": "medium"
}
```

**Storyline (Generated):**
- Scene 1: Product reveal on white background (0-6s, energy 3→5)
- Scene 2: Close-up of coffee brewing mechanism (6-12s, energy 5→6)
- Scene 3: Coffee pouring into cup, steam rising (12-18s, energy 6→8)
- Scene 4: Person enjoying coffee in modern kitchen (18-24s, energy 7→8)
- Scene 5: Final product shot with "Learn More" (24-30s, energy 8→9→6)

**Reference Images:**
- User images: 2 product photos
- Generated: Hero shot, detail shot, lifestyle shot (via Replicate)

**Generation:**
- Sora generates 5 scenes (~3 min)
- Suno generates music (~1.5 min) with precise timing matching scenes

**Composition:**
- Stitch scenes + add music + add text overlay
- Encode to 4K

**Output:**
- Beautiful 30-second ad with consistent product appearance, sophisticated visual style, matching audio with precise transitions, professional quality, ready to share

---

## 14. KEY DECISIONS

1. **Reference Images:** User-uploaded + Replicate generation (best model) instead of DALL-E
2. **Chat Interface:** One question at a time, users can go back
3. **Creative Director:** LLM acts as expert, asks 5-7 follow-up questions
4. **Storyline Generation:** Single LLM call creates both storyline and Suno prompt with precise timing
5. **Multiple Campaigns:** Users can create multiple ads per brand, reuse Creative Bibles
6. **Auth:** Firebase Authentication (email/password + OAuth)
7. **Deployment:** Railway (backend), Vercel/Netlify (frontend)
8. **Timeline:** 24 hours (aggressive but focused)

---

## DONE ✅

This is the complete MVP PRD. Minimal, focused, achievable in 24 hours with clear user flow and technical specifications.

