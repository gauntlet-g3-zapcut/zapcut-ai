# User Flows

## Core User Journey: From Landing to Published Ad

### High-Level Flow
```
Landing Page → Login → Brand Setup → Chat Briefing → Video Generation → Preview & Edit → Export/Publish
```

---

## Flow 1: First-Time User Onboarding

### Stage 1: Landing & Authentication
**Screens**: Single-page app (SPA)

1. **User Action**: Visits `https://app.zapcut.video`
2. **System**: Shows login screen with Cognito Hosted UI
3. **User Action**: Clicks "Sign up with Email" or "Continue with Google"
4. **System**: AWS Cognito handles authentication
5. **Redirect**: After login, redirect to main chat interface

**Success Criteria**: User authenticated and JWT stored

---

### Stage 2: Brand Onboarding (Orchestrator-Guided)
**Orchestrator Stage**: `collect_brand_info` → `collect_product_info` → `collect_assets`

#### Step 1: Welcome & Brand Basics
**System Message**:
```
👋 Hi! I'm your Zapcut assistant. Let's create your first AI-generated video ad.

First, tell me about your brand:
- What's your brand name?
- What product or service do you want to advertise?
```

**User Input**: 
```
Brand: "Luna Coffee"  
Product: "Organic cold brew concentrate"
```

**Orchestrator**: Validates input, creates Project record in database

---

#### Step 2: Visual Assets Collection
**System Message**:
```
Great! Now I need some visual references of your product.

Please upload 2-4 images of your cold brew:
- Product shot (bottle/packaging)
- Lifestyle shot (product in use)
- Optional: Logo, brand colors
```

**User Action**: Uploads 2 product images
- `luna-coffee-bottle.jpg`
- `luna-coffee-lifestyle.jpg`

**System**: 
- Stores images in S3
- Creates Asset records linked to Project
- Analyzes images for color palette extraction

**Orchestrator**: Moves to `collect_product_info` stage

---

#### Step 3: Product & Audience Details
**System Message**:
```
Perfect! Now help me understand your product and audience:

1. Describe your product in 2-3 sentences
2. Who is your target audience?
3. What's the main benefit or feeling you want to convey?
```

**User Input**:
```
1. Luna Coffee is an organic, smooth cold brew concentrate. Just add water or milk. Perfect for busy mornings.
2. Target: 25-40 year olds, health-conscious, urban professionals
3. Feeling: Calm energy, morning ritual, premium but approachable
```

**Orchestrator**: Stores product info, moves to `collect_scenes` stage

---

### Stage 3: Ad Brief & Scene Planning
**Orchestrator Stage**: `collect_scenes`

#### Step 1: Creative Direction
**System Message**:
```
Got it! What style should your ad have?

Examples:
- "Modern and minimalist with clean backgrounds"
- "Energetic and dynamic with quick cuts"
- "Cozy and warm with soft lighting"

Or describe your own vision:
```

**User Input**:
```
"Clean and modern, soft morning light, warm earth tones, calm and serene feeling. Show someone's morning routine with the coffee."
```

**Orchestrator**: 
- Generates Creative Bible draft
- Calls Style & Brand Agent to analyze uploaded images + user's description
- Creates color palette: `["#8B7355", "#F5E6D3", "#4A4A4A", "#FFFFFF"]`
- Sets visual style: `"minimalist, soft natural lighting, cinematic, warm tones"`

---

#### Step 2: Scene Suggestions
**System Message**:
```
Based on your brief, I'm thinking we create a 30-second ad with these scenes:

Scene 1 (0-6s): Close-up of Luna Coffee bottle on kitchen counter, morning sunlight streaming through window
Scene 2 (6-12s): Pouring concentrate into glass with ice
Scene 3 (12-18s): Adding water/milk, showing the color blend
Scene 4 (18-24s): Person taking first sip, subtle satisfied expression
Scene 5 (24-30s): Final product shot with text overlay "Luna Coffee - Your Morning Ritual"

Does this feel right? Any changes you'd like?
```

**User Options**:
- "Looks perfect, let's go"
- "Can we change Scene 4 to show the person working on laptop instead?"
- "Make it more abstract, less literal"

**User Input**: `"Looks perfect!"`

**Orchestrator**: 
- Finalizes scene plan
- Moves to `final_review` stage

---

#### Step 3: Final Review
**System Message**:
```
Perfect! Here's what we're creating:

✅ Brand: Luna Coffee  
✅ Product: Organic cold brew concentrate  
✅ Style: Clean, modern, warm morning light  
✅ Duration: 30 seconds  
✅ Scenes: 5 (morning routine narrative)  
✅ Music: Calm acoustic background track

Estimated generation time: 4-5 minutes  
Cost: ~$2.50

Ready to generate your video?
```

**User Action**: Clicks "Generate Video" button

**Orchestrator**: Moves to `generate_video` stage

---

### Stage 4: Video Generation (Background Worker)
**Orchestrator Stage**: `generate_video`

#### Frontend Experience
**Loading Screen with Progress**:
```
⚡ Generating your video...

[██████░░░░] 60% - Generating Scene 3 of 5
✅ Creative Bible created
✅ Reference images generated (4 images)
✅ Scene 1 rendered
✅ Scene 2 rendered
✅ Scene 3 rendering... (45s remaining)
⏳ Scene 4 queued
⏳ Scene 5 queued
⏳ Music generation queued
⏳ Final composition queued

Elapsed: 2m 35s | Est. remaining: 2m 10s
```

#### Backend Worker Process
1. **Creative Bible Generation** (30s)
   - Claude analyzes user brief + product images
   - Generates style parameters, color palette, lighting rules
   - Stores in `creative_bibles` table

2. **Reference Image Generation** (45s)
   - Claude creates 4 DALL-E prompts based on Creative Bible
   - DALL-E generates 4 reference images in parallel:
     - Hero product shot
     - Detail/close-up shot
     - Lifestyle/context shot
     - Alternate angle
   - Stores URLs in Creative Bible record

3. **Scene Storyboard** (15s)
   - Claude generates detailed 5-scene breakdown
   - Each scene includes:
     - Description, duration, camera direction
     - Energy level progression
     - Key story events
   - Stores in `generated_ads` table

4. **Sora Prompt Generation** (10s)
   - Prompt Synthesis Agent creates 5 Sora prompts
   - Each includes:
     - Scene description + Creative Bible + reference image URLs
     - Continuity instructions (for scenes 2-5)
     - Safety constraints

5. **Parallel Generation** (2-3 minutes)
   - **Sora**: Generate 5 video scenes (parallel API calls)
   - **Suno**: Generate 30s music track (parallel)
   - Poll Replicate for completion

6. **Video Composition** (30s)
   - FFmpeg stitches 5 scenes with 0.5s crossfades
   - Mixes Suno audio underneath
   - Adds text overlays at Scene 5 (product name, CTA)
   - Encodes to H.264, 1080p, 30fps
   - Uploads to S3

7. **Finalization**
   - Updates database with final video URL
   - Notifies frontend via WebSocket or polling

**Total Time**: 4-5 minutes

---

### Stage 5: Preview & Iteration
**Orchestrator Stage**: `export_video`

#### Preview Interface
**System Message**:
```
🎉 Your video is ready!

[Embedded Video Player showing 30s ad]

▶️ Play  |  ⏸️ Pause  |  🔊 Volume

What would you like to do?
- Download video (MP4)
- Generate variations
- Post to social media
- Edit specific scene
```

**User Options**:

**Option A: Happy with result**
```
User: "This is perfect! Download it."
System: Downloads `luna-coffee-ad-v1.mp4`
```

**Option B: Request variation**
```
User: "Can you make a version with more energy? Faster cuts?"
System: Regenerates with adjusted Creative Bible (higher energy level, shorter scene durations)
```

**Option C: Edit specific scene**
```
User: "Scene 4 doesn't match. Can we make the person younger?"
System: Regenerates just Scene 4 with updated prompt
```

---

### Stage 6: Export & Publish

#### Direct Publishing
**User Action**: Clicks "Post to X" or "Post to LinkedIn"

**System Checks**:
1. Are social accounts connected?
   - If NO: Show OAuth connection modal
   - If YES: Proceed to compose

**Compose Modal**:
```
Post to X (Twitter)

[Video thumbnail preview]

Caption:
"Introducing Luna Coffee ☕️ - Your perfect morning ritual. 
Organic cold brew concentrate that's smooth, rich, and ready in seconds.
#MorningCoffee #ColdBrew"

[200/280 characters]

☐ Also post to LinkedIn

[Cancel] [Post Now]
```

**User Action**: Clicks "Post Now"

**Backend**:
1. Uploads video to X Media API
2. Creates tweet with video attachment
3. If LinkedIn selected, registers upload + creates post
4. Returns URLs of published posts

**Success Message**:
```
✅ Posted successfully!

View on X: [link]
View on LinkedIn: [link]
```

---

## Flow 2: Returning User (Reusing Creative Bible)

### Scenario: User already has "Luna Coffee" brand set up

#### Fast Path
1. **User**: Opens Zapcut, sees project list
2. **System**: Shows "Luna Coffee" project card
3. **User**: Clicks "Create New Ad" on Luna Coffee project
4. **System**: "What should this ad focus on?"
5. **User**: "Highlight our new vanilla flavor"
6. **System**: Loads existing Creative Bible, generates new 5-scene storyboard
7. **Generation**: 3 minutes (skips Creative Bible + reference image generation)
8. **Result**: New ad in same visual style as original

**Time Savings**: 3 minutes instead of 5 minutes (40% faster)  
**Cost Savings**: $1.50 instead of $2.50 (40% cheaper)

---

## Flow 3: Batch Variation Generation

### Scenario: User wants to A/B test different hooks

#### Batch Request
1. **User**: "Generate 5 variations with different opening scenes"
2. **System**: 
   - Keeps Creative Bible and Scenes 2-5 identical
   - Generates 5 different Scene 1 prompts:
     - Version A: Close-up product shot
     - Version B: Overhead pouring shot
     - Version C: Person waking up reaching for coffee
     - Version D: Sunrise through window
     - Version E: Product on bedside table
3. **Generation**: All 5 variations generated in parallel
4. **Result**: 5 complete 30s ads, identical except opening scene

**Time**: 5 minutes for all 5 (same as generating 1)  
**Cost**: $8.00 for all 5 (~$1.60 each)

---

## Error Flows

### Error 1: Generation Failure (Sora API timeout)
**Scenario**: Sora takes too long or fails

**System Response**:
```
⚠️ Scene 3 generation timed out. Retrying...

Attempt 2 of 3...
```

**If all retries fail**:
```
❌ Unable to generate Scene 3 after 3 attempts.

Would you like to:
- Try with a simplified prompt
- Skip Scene 3 and continue with 4 scenes
- Cancel and try later
```

---

### Error 2: Safety Violation
**Scenario**: User requests unsafe content

**User Input**: `"Show someone doing shots of Luna Coffee at a party with alcohol"`

**System Response**:
```
⚠️ I can't create content that shows alcohol or unsafe consumption.

However, I can create:
- "Friends enjoying Luna Coffee at a casual gathering"
- "Morning coffee routine before a party/event"
- "Luna Coffee as the perfect pick-me-up drink"

Would any of these work instead?
```

---

### Error 3: Poor Image Quality
**Scenario**: User uploads blurry product image

**System Response**:
```
⚠️ The uploaded image "product.jpg" appears blurry or low-resolution.

For best results, please upload images that are:
- At least 1024x1024 pixels
- Well-lit and in focus
- Show the product clearly

Would you like to:
- Upload a different image
- Continue anyway (may affect video quality)
```

---

## Edge Cases

### Edge Case 1: No Product Images Available
**User**: "I don't have product images yet, can I generate concept ads?"

**System**: 
```
Absolutely! I can generate ads without product images using AI-generated visuals.

However, the product appearance will be synthetic and may not match your final packaging.

Best for:
- Pre-launch concept testing
- Service-based businesses (no physical product)
- Abstract/lifestyle ads

Continue with AI-generated product visuals?
```

---

### Edge Case 2: Very Long Video Request
**User**: "Create a 3-minute video"

**System**:
```
I can create videos up to 3 minutes, but this will:
- Take longer to generate (15-20 minutes)
- Cost more (~$6-8)
- Require 15-20 scenes for good pacing

For most ads, 30-60 seconds performs better and tests faster.

Would you like to:
- Continue with 3 minutes
- Start with 30-60s and expand later
```

---

## Metrics to Track

### User Journey Funnel
```
Landing Page → 100%
Sign Up Started → 45%
Sign Up Completed → 35%
Brand Setup Started → 30%
Brand Setup Completed → 25%
First Video Generated → 20%
First Video Downloaded → 18%
Social Media Published → 10%
Second Video Generated → 12% (retention)
```

### Time Metrics
- Time to first video: Target <15 minutes from sign-up
- Time per video generation: Target <5 minutes
- Time to publish (download → social post): Target <2 minutes

### Quality Metrics
- User satisfaction (1-5): Target 4.2+
- Generation success rate: Target 90%+
- Retry rate: Target <15%

---

**Last Updated**: November 15, 2025  
**Status**: Active  
**Next Review**: December 1, 2025

