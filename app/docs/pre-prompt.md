Generate a PRD.md for non-technical stuff and Architecture.md for the technical architecture.

AI Video Generation Pipeline
Background
Video generation with AI has transformed creative production. What once required teams of editors, motion designers, and sound engineers can now be orchestrated through intelligent pipelines that understand context, timing, and visual coherence.
Companies like Runway, Pika, and others have shown us what's possible. But true AI video generation isn't just about creating clips. It's about building cohesive narratives that seamlessly integrate image generation, video synthesis, audio, voiceovers, and timing.
Consider how Midjourney transformed image creation. Now imagine that same revolution for video production. A single prompt generates a complete music video synced to beats, or an entire ad campaign tailored to a brand's visual identity.
This project challenges you to build an end-to-end AI video generation pipeline that creates professional-quality video content with minimal human intervention.
Why This Matters
The future of content creation is generative. Brands need hundreds of ad variations. Musicians want instant music videos. Creators need content at scale.
The team that builds the most robust, cost-effective pipeline wins not just this competition, but potentially defines the future of AI video production. You'll be building technology that could power the next generation of creative tools.
Project Overview
This is a one-week sprint with a $5,000 bounty for the winning team.
Key Deadlines:
Start: Friday, Nov 14, 2025
MVP: Sunday (48 Hours)
Early Submission: Wednesday (5 days)
Final: Next Sunday (9 days)
You'll build a complete AI video generation pipeline that takes high-level prompts and outputs publication-ready video content with synchronized audio, coherent visuals, and professional polish.
MVP Requirements (48 Hours)
This is a hard gate. To pass the MVP checkpoint, you must have:
Working video generation for at least ONE category (music video OR ad creative)
Basic prompt to video flow (text input to video output)
Audio visual sync (video matches audio timing/beats)
Multi clip composition (at least 3 to 5 clips stitched together)
Consistent visual style across clips
Deployed pipeline (API or web interface)
Sample outputs (at least 2 generated videos demonstrating capability)
The MVP proves your pipeline works end to end. A simple but reliable music video generator beats a feature-rich system that produces incoherent output.
Example MVP Architecture
At minimum, you should have:
Prompt Parser: Interprets user input and extracts creative direction
Content Planner: Breaks video into scenes/segments with timing
Generation Engine: Calls AI models (video, image, audio) for each segment
Composition Layer: Stitches clips with transitions and audio sync
Output Handler: Renders final video in standard format (MP4, WebM)
Core Pipeline Requirements
Video Categories
You must support at least ONE of these categories with full end to end generation:
Category 1: Music Video Pipeline
Input: Song file (generated or uploaded) + creative direction
Output: Complete music video (1 to 3 minutes)
Requirements:
Generate or accept AI generated music (Suno, Udio, etc.)
Analyze song structure (intro, verse, chorus, bridge, outro)
Detect beats and tempo for scene transitions
Generate visuals that match song mood and lyrics
Sync visual transitions to musical beats
Maintain visual coherence across scenes
Apply consistent style/aesthetic throughout
Example Prompts:
"Create an ethereal music video for this ambient electronic track with floating geometric shapes"
"Generate a high energy punk rock video with urban graffiti aesthetics"
"Make a dreamy indie pop video with pastel colors and nature scenes"
Category 2: Ad Creative Pipeline
Input: Product description + brand guidelines + ad specifications
Output: Video advertisement (15 to 60 seconds)
Requirements:
Generate product showcase clips
Apply brand colors and visual identity
Create multiple ad variations (A/B testing)
Support different aspect ratios (16:9, 9:16, 1:1)
Add text overlays (product name, CTA, price)
Generate background music or sound effects
Include voiceover capability (optional but bonus)
Example Prompts:
"Create a 30 second Instagram ad for luxury watches with elegant gold aesthetics"
"Generate 3 variations of a TikTok ad for energy drinks with extreme sports footage"
"Make a product showcase video for minimalist skincare brand with clean white backgrounds"
Category 3: Educational/Explainer Pipeline (Bonus Category)
Input: Topic/script + visual style preferences
Output: Explainer video with narration and visuals
Requirements:
Generate narration/voiceover from script
Create visualizations matching narration timing
Add text captions and graphics
Maintain educational clarity
Support diagrams, charts, and animations
Technical Requirements
1. Generation Quality
Visual Coherence:
Consistent art style across all clips
Smooth transitions between scenes
No jarring style shifts or artifacts
Professional color grading
Audio Visual Sync:
Beat matched transitions (music videos)
Voiceover timing (ad creatives)
Sound effects aligned with visuals
No audio video drift
Output Quality:
Minimum 1080p resolution
30+ FPS
Clean audio (no distortion or clipping)
Proper compression (reasonable file size)
2. Pipeline Performance
Speed Targets:
30 second video: Generate in under 5 minutes
60 second video: Generate in under 10 minutes
3 minute video: Generate in under 20 minutes
Note: We understand AI model inference takes time. We're measuring end to end pipeline efficiency, including smart caching and optimization strategies.
Cost Efficiency:
Track and report generation cost per video
Optimize API calls (avoid redundant generations)
Implement caching for repeated elements
Target: Under $200.00 per minute of final video
Reliability:
90%+ successful generation rate
Graceful failure handling
Automatic retry logic for failed API calls
Error logging and debugging support
3. User Experience
Input Flexibility:
Natural language prompts
Optional parameter controls (style, duration, mood)
Reference image/video uploads (style transfer)
Brand guideline documents (for ads)
Output Control:
Preview generation before final render
Regenerate specific scenes
Adjust timing and transitions
Export in multiple formats
Feedback Loop:
Show generation progress
Display which stage is processing
Preview intermediate results
Allow user intervention/correction
Advanced Features (Competitive Advantages)
These aren't required but will significantly strengthen your submission:
Style Consistency Engine
Train custom LoRA models for brand consistency
Character consistency across scenes
Automatic style transfer from reference images
Intelligent Scene Planning
Analyze music structure (AI powered beat detection)
Generate storyboards before video creation
Shot variety logic (close ups, wide shots, transitions)
Multi Modal Generation
Combined image + video generation (static + motion)
Text to speech with emotion control
Sound effect generation matching visuals
Iterative Refinement
Chat interface for video editing
"Make this scene brighter"
"Add more motion to the chorus"
"Change the color palette to warmer tones"
Batch Generation
Generate multiple variations simultaneously
A/B testing for ad creatives
Different aspect ratios from single prompt
Evaluation Criteria
Your pipeline will be judged on these weighted factors:
1. Output Quality (40%)
Visual coherence: Does it look professional?
Audio visual sync: Are transitions timed properly?
Creative execution: Does it match the prompt?
Technical polish: Resolution, frame rate, compression
2. Pipeline Architecture (25%)
Code quality: Clean, maintainable, documented
System design: Scalable and modular
Error handling: Robust failure recovery
Performance optimization: Fast and efficient
3. Cost Effectiveness (20%)
Generation cost: Price per video produced
API efficiency: Smart caching and optimization
Resource usage: Memory, compute, storage
4. User Experience (15%)
Ease of use: Intuitive interface
Prompt flexibility: Handles varied inputs
Feedback quality: Clear progress indicators
Output control: Fine tuning capabilities
Testing Scenarios
We'll evaluate your pipeline with prompts like:
Music Videos:
"Generate a music video for [attached song] with cyberpunk aesthetics"
"Create a lo fi hip hop video with cozy study room vibes"
"Make an epic orchestral video with fantasy landscapes"
Ad Creatives:
"Create 3 variations of a 15 second Instagram ad for [product description]"
"Generate a luxury brand video ad with minimal aesthetic"
"Make a dynamic product showcase for tech gadgets"
Stress Tests:
Multiple concurrent generation requests
Very long videos (3+ minutes)
Complex multi part narratives
Unusual style combinations
Technical Stack
You'll have access to all the latest image and video generation models on Replicate.
Important: Start development with cheaper models to iterate quickly and control costs. As you approach the showcase, switch to more expensive, higher quality models for your final outputs.
Use whatever stack produces the best results. We care about output quality, not tech stack choices.
Submission Requirements
Submit by Sunday 10:59 PM CT:
1. GitHub Repository
README with setup instructions and architecture overview
Documentation explaining pipeline stages
Cost analysis (breakdown of generation costs)
Deployed link (API endpoint or web interface)
2. Demo Video (5 to 7 minutes)
Show:
Live generation from prompt to final video
Walkthrough of your pipeline architecture
Comparison of different prompts/styles
Challenges you solved and trade offs you made
3. AI Generated Video Samples
You must submit at least 3 AI generated videos for your chosen category:
For Music Videos:
One video synced to an upbeat/energetic song
One video synced to a slow/emotional song
One video demonstrating complex visual transitions
For Ad Creatives:
Three different product ads showing style variation
At least one ad in vertical format (9:16) for social media
At least one ad with text overlays and call to action
For Educational/Explainer:
One technical explanation with diagrams
One narrative driven explainer
One demonstration with step by step visuals
4. Technical Deep Dive (1 page)
Answer these questions:
How do you ensure visual coherence across clips?
How do you handle audio visual synchronization?
What's your cost optimization strategy?
How do you handle generation failures?
What makes your pipeline better than others?
5. Live Deployment
Public URL for testing your pipeline
API documentation if applicable
Test credentials for judges to access
Rate limits clearly communicated
Judging Process
Round 1: Initial Review
All submissions reviewed for completeness and basic functionality.
Round 2: Technical Evaluation
Deep dive into code quality, architecture, and innovation.
Round 3: Output Testing
Judges generate videos with standardized prompts and evaluate quality.
Round 4: Final Scoring
Weighted scores across all criteria determine the winner.
Winner Announcement: Monday following submission deadline
Prize Structure
Grand Prize: $5,000
Best overall video generation pipeline. Combination of quality, cost efficiency, and innovation.
Bonus Recognition:
Most cost efficient pipeline
Best music video generator
Best ad creative generator
Most innovative architecture
Inspiration
Study these to understand the state of the art:
Companies:
Runway ML (Gen 3)
Pika Labs
Kaiber AI
Synthesia
HeyGen
Kling AI
Concepts:
Icon's rapid creative generation
Midjourney's consistent style system
Modern ad tech platforms (Meta Ads, Google Ads creative studios)
Think about:
How do professional video editors build music videos?
What makes an ad creative effective vs generic?
How do you maintain visual coherence without human oversight?
What's the minimum viable feature set for real world usage?
Final Note
This is your chance to build technology that could redefine content creation. The best AI video startups are raising millions to solve these exact problems.
A working pipeline that generates ONE category of video beautifully beats a complex system that tries to do everything poorly.
Focus on:
Coherence over quantity
Reliability over features
Cost efficiency over bleeding edge models
Ship something real that actually works.
Let's build the future of video creation.
Questions? Ready to build?
The clock starts now. Make it count.

✅ MASTER SYSTEM PROMPT (Top-Level Agent Coordinating Video Generation)
Use this before ANY script → storyboard → video → audio generation.
SYSTEM — MASTER VIDEO CREATION AGENT
You are an AI Video Ad Director responsible for producing safe, brand-accurate, visually consistent, high-quality video ads using user-provided assets (script, branding, images, goals, tone).
Your output must ALWAYS follow these constraints:
1. SAFETY & CONTENT RULES (Mandatory)
You MUST reject or repair any content that includes:
1.1 Prohibited Content
Violence, blood, abuse, self-harm
Sexual content, nudity, suggestive poses
Drugs, smoking, alcohol (unless brand AND legal region explicitly provided)
Hate speech, extremist symbols, harassment
Dangerous activities (reckless driving, cliff jumping, etc.)
Minors shown in unsafe or adult contexts
1.2 Deepfake + Authenticity Restrictions
Never depict real celebrities, influencers, politicians, CEOs, or public figures.
Never imitate real voices.
All humans must be synthetic and non-identifiable.
1.3 Copyright Restrictions
No copyrighted characters, movie references, or branded locations.
No competitor logos or imitational packaging.
No copied melodies in music generation.
 Must be wholly synthetic.
2. BRANDING RULES (From User’s Onboarding Input)
You MUST apply:
Brand colors, fonts, logo, tone, voice guidelines.
Only use assets uploaded by the user (photos, logos, product shots).
Never hallucinate competitor logos or realistic brands.
Product visuals must be consistent across shots.
3. VIDEO QUALITY RULES (Sora + LORA)
You MUST enforce:
3.1 Visual Consistency
No warped faces
No extra limbs
No unnatural movements
No shape-shifting product
No flickering scenes or sudden environment changes
3.2 Scene Dynamics
Prefer:
Clear camera motions (slow pan, dolly, orbit)
Stable lighting
One focal subject per shot
Avoid:
Fast motion
Complex crowds
Fights/chaos
Micro-detailed hand interactions (unless necessary)
3.3 Product Accuracy
Product must match user-uploaded images
Must maintain consistent shape, color, and proportions
4. SCRIPT RULES (If writing or refining scripts)
Scripts MUST:
Be 100% brand-safe
Respect tone from onboarding (e.g., “Energetic”, “Emotional”, “Premium”)
Avoid prohibited claims unless user input explicitly provides them
 (e.g., “Best in the world”, “Guaranteed weight loss”)
Include natural transitions and clear scene descriptions
End with a strong CTA (based on user goal)
5. SORA VIDEO GENERATION RULES
When generating a video prompt:
ALWAYS produce a shot-by-shot breakdown
Max 3–5 scenes per 15 seconds
Provide:
Scene description
Camera movement
Lighting
Character style
Product placement
On-screen text
Audio cues (if audio pipeline exists)
Your Sora prompt MUST include:
5.1 Safety Stamp
Add at the top:
“This video must not contain violence, sexual content, copyrighted characters, real people, unsafe behavior, or trademarks. Humans must be synthetic, safe, and generic.”
5.2 Brand Stamp
Add:
“Use the provided brand tone: {brandTone}. Use brand colors {primaryColor} and {secondaryColor}. Use brand assets from URLs provided.”
6. TRIAGE RULES: Reject / Repair / Replace
Reject
If user requests unsafe or illegal content:
 → Explain safety violation and decline.
Repair
If request is fixable:
 → Rewrite script or scenes to comply.
Replace
If user requests copyrighted materials:
 → Replace with generic equivalents (castle, forest, city alley, futuristic lab).
7. OUTPUT FORMAT — ALWAYS USE JSON
The Master Agent must ALWAYS output:
{
  "status": "ready",
  "script": "... refined script ...",
  "scene_breakdown": [ { ... } ],
  "sora_prompt": "... final video prompt for Sora ...",
  "audio_prompt": "... optional sfx/music prompt ...",
  "safety_notes": "... final checks ..."
}
✅ SYSTEM PROMPT FOR THE SCRIPT GENERATION AGENT
Use when generating or refining a video script.
SYSTEM — SCRIPTWRITER AGENT
You write high-quality ad scripts following:
Brand tone: {brandTone}
Goal: {goal} (e.g., conversions, awareness)
Length: {duration} (e.g., 15s, 30s)
Product info, benefits, and description
Safety & authenticity rules (no violence, false claims, etc.)
You MUST:
Produce a shot-based script: Scene 1, Scene 2, etc.
Include on-screen text, voiceover, visuals, action, camera motion.
Ensure brand-safe content only.
Reject unsafe content and propose alternatives.
✅ SYSTEM PROMPT FOR THE SORA VIDEO GENERATION AGENT
This is what you send directly to Sora via your backend.
SYSTEM — SORA VIDEO GENERATOR
Generate a video that strictly follows:
🔒 SAFETY REQUIREMENTS
No violence, drugs, sexual content, hate, unsafe behavior
No real people, no deepfakes
No copyrighted characters
No competitor logos
Only synthetic humans
No minors in unsafe contexts
🎨 BRAND REQUIREMENTS
Tone: {brandTone}
Colors: {primaryColor}, {secondaryColor}
Use only the product images linked in: {imageUrls}
🎥 QUALITY REQUIREMENTS
Smooth shots
No flickering frames
No mutated limbs or distorted faces
No object teleportation
Lighting must be consistent
🧩 PROMPT STRUCTURE
Always follow this format:
SAFETY STAMP:
(No unsafe content. Use synthetic humans only.)
BRAND STAMP:
Brand tone: {brandTone}. Colors: {primaryColor}/{secondaryColor}. Product assets: {imageUrls}.
VIDEO INSTRUCTIONS:
Scene 1:
- Visual:
- Camera:
- Lighting:
- Product placement:
- On-screen text:
Scene 2:
...
STYLE:
Cinematic, stable, clean, premium.
RESTRICTIONS:
No logos unless uploaded by the user.
No references to real copyrighted characters.
No real humans.
✅ SYSTEM PROMPT FOR THE SAFETY VALIDATION AGENT (PRE-SORA FILTER)
This agent reviews script + scenes BEFORE hitting Sora.
SYSTEM — SAFETY VALIDATION AGENT
Your job is to scan the script and scenes for:
Safety violations
Copyright violations
Trademark issues
False or misleading claims
Deepfakes or real-person likeness
Unsafe activities
Overly complex scenes Sora might fail at
If ANY violation exists:
Output "status": "blocked" with a clear explanation.
Provide a safe rewrite version automatically.
Else:
Output "status": "approved".
Output format:
{
  "status": "approved",
  "issues": [],
  "safe_script": "... final approved script ..."
}
🚀 WANT ME TO PACKAGE THIS INTO…
✅ A single .md file for your repo?
✅ A full spec section for your PRD?
✅ A json-based policy file to load into your backend?
✅ A multi-agent architecture diagram using these prompts?
Just tell me:
 “Give me the repo-ready version.”


Duration: 48 hours (Friday-Sunday)
Focus: Video + Music generation with consistent creative direction
Scope: Ruthlessly minimal

1. USER FLOW
Screen 1: Create Project

Input: Product name + product image (upload OR "generate")
If generate: User describes product → DALL-E generates one image
Output: Product image stored

Screen 2: Ad Brief

Input: "I want a [style] ad for my product"

Example: "very modern, energetic ad"


Output: Stored for Creative Bible

Screen 3: Video Editor (Display Generated Ad)

Input: None (just wait for generation)
Output: 4K video with music
Actions:

Download MP4
Download WebM
Share link



That's it. No editing, no variations, no voiceover.

2. BACKEND WORKFLOW
Path A: New Creative Bible (First ad for product)
1. User submits brief + project_id
   ↓
2. Generate Creative Bible (LLM analyzes brief)
   ├─ Extract style, vibe, energy
   └─ Lock colors, mood, motion
   ↓
3. Store Creative Bible in database
   ├─ creative_bible_id generated
   └─ Tied to project
   ↓
4. Generate Reference Image Prompts (LLM)
   └─ Claude creates 4 DALL-E prompts matching Creative Bible
   ↓
5. Generate Reference Images (PARALLEL to 6-9)
   ├─ DALL-E: Hero shot (product centered)
   ├─ DALL-E: Detail shot (close-up)
   ├─ DALL-E: Lifestyle shot (product in context)
   └─ DALL-E: Alternate angle
   ↓
6. Generate 5-Scene Storyboard (LLM) (PARALLEL)
   ↓
7. Generate Sora Prompts (1 per scene) (PARALLEL)
   └─ Each includes: Scene description + Creative Bible + reference image URLs
   ↓
8. Generate Single Suno Prompt (PARALLEL)
   └─ From storyboard structure + Creative Bible
   ↓
9. Call Generation APIs in PARALLEL:
   ├─ Sora: Generate 5 video scenes (2-3 min)
   └─ Suno: Generate 1 music track (1-2 min)
   ↓
10. Compose Video
   ├─ Stitch 5 scenes with 0.5s crossfade
   ├─ Mix audio underneath
   ├─ Add text overlay (product name + "Learn More")
   └─ Encode to 4K/30fps
   ↓
11. Store Ad in database
    ├─ Ad tied to project_id + creative_bible_id
    └─ Video stored
Path B: Reuse Creative Bible (Subsequent ads for same product + style)
1. User selects existing Creative Bible + project_id
   ↓
2. Retrieve Creative Bible + Reference Images from database
   ├─ Skip LLM generation (FAST)
   └─ Reference images already cached
   ↓
3. Generate 5-Scene Storyboard (LLM, new)
   └─ Different storyboard, same Creative Bible
   ↓
4. Generate Sora Prompts (using cached reference images)
   ↓
5. Generate Suno Prompt
   ↓
6. Call Generation APIs (same as Path A, steps 9-11)
   ├─ Sora: 2-3 min
   └─ Suno: 1-2 min
   ↓
7. Store Ad in database
    ├─ Same creative_bible_id
    └─ New ad_id
Speed difference:

Path A (new Bible): 5 minutes (LLM calls + DALL-E + Sora + Suno)
Path B (reuse Bible): 3 minutes (only Sora + Suno, no LLM/DALL-E)


4. REFERENCE IMAGE GENERATION
Step 1: LLM generates DALL-E prompts
Claude creates 4 optimized DALL-E prompts based on Creative Bible:
{
  "hero_shot": "Professional product photography. [Product]. 
    Style: {creative_bible.brand_style}. 
    Colors: {creative_bible.colors}. 
    Lighting: {creative_bible.lighting}. 
    Centered, clean background, premium quality.",
    
  "detail_shot": "Close-up detail photography of [Product]. 
    Focus on texture and craftsmanship. 
    Same style and colors as hero shot.",
    
  "lifestyle_shot": "Lifestyle product photography. [Product] in use. 
    Real-world context, premium environment. 
    Same aesthetic as hero shot.",
    
  "alternate_angle": "Product photography from different perspective. 
    [Product] at 45-degree angle. 
    Professional lighting, same brand aesthetic."
}
Step 2: DALL-E generates all 4 images (parallel)

Takes ~30-60 seconds
Returns URLs for each image
All images match same visual style (locked by Creative Bible)

Result: 4 reference images stored, URLs passed to Sora prompts

5. SORA PROMPTS (Scene Prompts)
Single LLM call generates:
json{
  "brand_style": "modern",
  "vibe": "energetic",
  "colors": ["#00b4ff", "#1a1a1a", "#ffffff"],
  "lighting": "bright, high-contrast",
  "camera": "dynamic, fast movements",
  "motion": "energetic, constant movement",
  "energy_level": "high"
}
Used in ALL prompts to Sora and Suno.

6. STORYBOARD
Single LLM call generates 5 scenes:
Scene 1 (0-6s): Product Reveal
- Description: Product zooms into frame on white background
- Energy: 3/10 → 5/10
- Sora Prompt Basis: Modern bright reveal shot

Scene 2 (6-12s): Detail Close-Up
- Description: Extreme close-up of product details
- Energy: 5/10 → 6/10
- Sora Prompt Basis: Detail showcase with dynamic lighting

Scene 3 (12-18s): Action/Motion
- Description: Product in motion, energetic use
- Energy: 6/10 → 8/10
- Sora Prompt Basis: Fast motion, dynamic angles

Scene 4 (18-24s): Lifestyle
- Description: Product integrated into lifestyle
- Energy: 7/10 → 8/10
- Sora Prompt Basis: Real-world context, premium feel

Scene 5 (24-30s): CTA
- Description: Final product shot, "Learn More" text appears
- Energy: 8/10 → 9/10 → 6/10 (resolve)
- Sora Prompt Basis: Hero shot, clean, professional

5. SORA PROMPTS (Scene Prompts)
Template for each scene:
SCENE [N] PROMPT

Creative Direction (locked):
- Style: {creative_bible.brand_style}
- Vibe: {creative_bible.vibe}
- Colors: {creative_bible.colors}
- Lighting: {creative_bible.lighting}
- Camera: {creative_bible.camera}

Reference Images (style anchors):
- Hero: {reference_image_urls.hero}
- Detail: {reference_image_urls.detail}
- Lifestyle: {reference_image_urls.lifestyle}

Scene [N]: {storyboard[n].title}
Duration: 6 seconds at 30fps
Description: {storyboard[n].description}

Product: {product_description}

Requirements:
- Use reference images as visual style guide
- Maintain EXACT product appearance from reference images
- Use ONLY the locked colors above
- Keep {creative_bible.motion} motion style
- Professional, cinematic quality

Generate video matching all constraints above.
5 prompts sent to Sora in parallel, each with reference image URLs included.

7. SUNO PROMPT (One Comprehensive Prompt)
Single prompt for entire 30-second track:
Create a {creative_bible.vibe} background music track for a product ad.

Duration: 30 seconds exactly
Style: {creative_bible.brand_style}
Vibe: {creative_bible.vibe}
Energy Level: {creative_bible.energy_level}

Music Structure:
- 0-6s: Scene 1 (Product reveal) - Energy building from 3 to 5/10
  → Music intro, establishing beat
- 6-12s: Scene 2 (Detail) - Energy 5 to 6/10
  → Maintain energy, subtle intensity shift
- 12-18s: Scene 3 (Action) - Energy 6 to 8/10
  → Peak energy section, dynamic movement
- 18-24s: Scene 4 (Lifestyle) - Energy 7 to 8/10
  → Sustain peak, premium feeling
- 24-30s: Scene 5 (CTA) - Energy 8 to 9 to 6/10
  → Climax at 27s, then resolve for ending

Characteristics:
- Tempo: 120-140 BPM (energetic)
- Instrumentation: Modern, electronic/cinematic
- No vocals
- Professional commercial quality
- Royalty-free

Make the music RHYTHMIC with clear progression matching the energy levels.
At 6s, 12s, 18s, 24s → music should have subtle transitions (not jarring cuts).
1 prompt sent to Suno.

8. VIDEO COMPOSITION
Once Sora videos + Suno music ready:

Download 5 video clips from Sora
Download audio from Suno
FFmpeg compose:

   - Concatenate 5 clips with 0.5s crossfade
   - Mix Suno audio underneath
   - Add text overlay: Product name (appears at 24s)
   - Add text overlay: "Learn More" (appears at 27s)
   - Encode to H.264, 4K (3840x2160), 30fps

Upload to S3
Done


9. API CALLS SUMMARY
APIPurposeCountTimeClaude (Anthropic)Creative Bible1 call5sClaude (Anthropic)Reference Image Prompts1 call5sClaude (Anthropic)Storyboard1 call10sClaude (Anthropic)Sora Prompts1 call5sClaude (Anthropic)Suno Prompt1 call5sDALL-E 3Reference images4 calls (parallel)30-60sSora (Replicate)Video scenes5 calls (parallel)2-3 minSuno (Replicate)Music track1 call1-2 minTOTAL3-4 min
Note: DALL-E, Storyboard, Sora Prompts, and Suno Prompt generation all happen in parallel while Creative Bible is being created. Total LLM call time is ~30s, reference images ~45s, video generation ~3 min.

10. DATABASE SCHEMA
sql-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE NOT NULL,
  created_at TIMESTAMP
);

-- Projects (Products)
CREATE TABLE projects (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  product_name VARCHAR NOT NULL,
  product_image_url VARCHAR NOT NULL,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Creative Bibles (one per project + style)
CREATE TABLE creative_bibles (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id),
  name VARCHAR NOT NULL, -- e.g., "modern_minimalist_v1", "energetic_dynamic_v2"
  creative_bible JSONB NOT NULL, -- {colors, vibe, style, lighting, camera, motion, energy_level}
  reference_image_urls JSONB NOT NULL, -- {hero, detail, lifestyle, alternate}
  created_at TIMESTAMP,
  
  UNIQUE(project_id, name) -- Can't have duplicate Bible names per project
);

-- Generated Ads
CREATE TABLE generated_ads (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id),
  creative_bible_id UUID NOT NULL REFERENCES creative_bibles(id),
  storyboard JSONB NOT NULL,
  sora_prompts JSONB NOT NULL,
  suno_prompt TEXT NOT NULL,
  video_urls JSONB, -- {scene_1, scene_2, ..., scene_5} S3 URLs
  music_url VARCHAR,
  final_video_url VARCHAR NOT NULL,
  created_at TIMESTAMP
);

-- Indexes for fast queries
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_creative_bibles_project_id ON creative_bibles(project_id);
CREATE INDEX idx_generated_ads_project_id ON generated_ads(project_id);
CREATE INDEX idx_generated_ads_creative_bible_id ON generated_ads(creative_bible_id);

10. TECH STACK
LayerTechFrontendNext.js + ReactBackendFastAPI (Python)Task QueueCelery + RedisDatabasePostgreSQLStorageS3LLMClaude (Anthropic)Video GenSora (Replicate)Music GenSuno (Replicate)CompositionFFmpeg

12. WHAT'S NOT IN MVP
❌ LoRA training
❌ Video editing with brush tool
❌ Voiceover/TTS
❌ Multiple variations
❌ Color grading/LUTs
❌ Text overlay customization
❌ Audio editing
❌ Brand kit management
❌ Project history/saved projects

12. CRITICAL SUCCESS CRITERIA
✅ Generation completes in < 5 minutes
✅ Video and audio feel cohesive (music matches energy of scenes)
✅ Product looks consistent across all 5 scenes
✅ 4K quality output
✅ Error handling (retry logic, graceful failures)
✅ UI shows progress (current stage + ETA)

13. TIMELINE
Friday (12 hours)

 FastAPI scaffold + Celery setup
 Claude integration (Creative Bible, Storyboard, Prompts)
 Sora + Suno integration via Replicate
 Basic React UI (upload + text input + display)

Saturday (12 hours)

 End-to-end generation pipeline
 FFmpeg composition
 S3 integration
 Error handling + retries

Sunday (8 hours)

 Generate 3 sample videos (test different products/styles)
 Deploy (Vercel + Render)
 Polish UI
 Final testing


14. SAMPLE EXECUTION
User Input:
Product: Luxury coffee maker
Brief: "Modern, sleek, minimalist ad for coffee enthusiasts"
Creative Bible (Generated):
{
  "brand_style": "minimalist",
  "vibe": "sophisticated",
  "colors": ["#2c2c2c", "#ffffff", "#8b6f47"],
  "lighting": "soft, warm, studio",
  "camera": "smooth, deliberate movements",
  "motion": "slow, refined",
  "energy_level": "medium"
}
Storyboard (Generated):
Scene 1: Product reveal on white background
Scene 2: Close-up of coffee brewing
Scene 3: Coffee pouring into cup
Scene 4: Person enjoying coffee
Scene 5: Final product shot with tagline
Sora Prompts (Generated):
5 prompts, each with Creative Bible + scene description
Suno Prompt (Generated):
1 prompt describing 30s progression: slow intro → warm build → sustain → elegant resolve
Generation (Parallel):

Sora generates 5 scenes (~3 min)
Suno generates music (~1.5 min)

Composition:

Stitch scenes + add music + add text overlay
Encode to 4K

Output:
Beautiful 30-second ad with:
- Consistent product appearance
- Sophisticated visual style
- Matching audio that builds and resolves
- Professional, ready to share

DONE ✅
This is the MVP. Minimal, focused, achievable in 48 hours.

1. Backend POST /api/generate-video – Contract & Behavior
Request shape (your “block-like” scenes API)
From mobile or web:
POST /api/generate-video
Authorization: Bearer <JWT>
{
  "projectId": "proj_123",
  "scenes": [
    {
      "prompt": "Close-up shot of the can with cold condensation droplets.",
      "media": [
        {
          "type": "image",
          "source": "upload",         // or "generated"
          "url": "https://s3.../hero1.png",
          "label": "hero_can",
          "role": "primary_product",  // e.g. primary_product, background, logo
          "startTime": 0,
          "endTime": 5
        }
      ]
    },
    {
      "prompt": "Group of friends laughing at a table with cans on it.",
      "media": [
        {
          "type": "image",
          "source": "generated",
          "url": "https://s3.../friends.png",
          "label": "friends_scene",
          "role": "background"
        }
      ]
    }
  ],
  "durationSeconds": 15,
  "aspectRatio": "16:9",
  "audioOptions": {
    "musicStyle": "upbeat electronic",
    "voiceoverLanguage": "en-US",
    "voiceStyle": "friendly"
  },
  "exportTargets": ["x", "linkedin"]   // optional hint for post-generation
}
Key points:
scenes is an array of scene blocks.
Each scene has:
prompt (textual description).
media[] (uploaded/selected assets from the gallery / branding library).
This matches your “block-like API request” idea from the frontend.
Response (async job pattern)
The endpoint should not block until Sora finishes. It should:
Validate input.
Run safety checks (LLM or moderation).
Enqueue a video generation job.
Return a job id.
{
  "jobId": "job_abc123",
  "status": "queued"
}
Then you’ll have a separate endpoint:
GET /api/generate-video/job/:jobId
{
  "jobId": "job_abc123",
  "status": "completed",
  "videoUrl": "https://s3.../final_ad.mp4",
  "thumbnailUrl": "https://s3.../final_ad_thumb.jpg"
}
2. Backend Implementation Flow (High-Level)
Pseudocode-ish TypeScript/Node backend logic:
// POST /api/generate-video
async function generateVideoHandler(req, res) {
  const userId = req.auth.sub;  // From Cognito JWT
  const { projectId, scenes, durationSeconds, aspectRatio, audioOptions, exportTargets } = req.body;
  // 1. Basic validation
  validateScenes(scenes);
  // 2. Load project + ownership check
  const project = await db.project.findById(projectId);
  if (!project || project.userId !== userId) {
    return res.status(404).json({ error: "Project not found" });
  }
  // 3. Safety / content validation (script + prompts)
  const safetyResult = await safetyValidator.checkScenes({ project, scenes });
  if (safetyResult.status === "blocked") {
    return res.status(400).json({
      error: "safety_violation",
      issues: safetyResult.issues,
      safeSuggestion: safetyResult.safe_script ?? null
    });
  }
  // 4. Persist job
  const job = await db.adVideoJob.create({
    projectId,
    userId,
    scenes,
    durationSeconds,
    aspectRatio,
    audioOptions,
    status: "queued"
  });
  // 5. Enqueue message to SQS (for worker)
  await sqs.sendMessage({
    QueueUrl: process.env.VIDEO_JOBS_QUEUE_URL!,
    MessageBody: JSON.stringify({ jobId: job.id }),
  }).promise();
  return res.status(202).json({ jobId: job.id, status: "queued" });
}
Worker (Elastic Beanstalk worker tier or separate service):
Receives jobId from SQS.
Fetches job + scenes from DB.
Calls orchestrator agent to build script + Sora prompt from scenes.
Calls Sora API, polls for completion.
Stores video file in S3 and updates DB.
Optionally triggers export to X/LinkedIn if requested.
3. Frontend at https://app.zapcut.video – Single-Page Chat-like UI
You said:
it should act as a single webpage without any navigation screens.
 store everything locally and in the database.
 Make it look like and act like ChatGPT, an agent on every screen.
Structure
SPA (React/Next/whatever) with one main route: /.
Layout:
Left: small sidebar (logo, account, maybe project picker).
Center: chat-like conversation (messages).
Right (collapsible): context panel (current scenes, media gallery, video preview).
Flow (Stages enforced by orchestrator agent)
Landing / Login
Slim screen: "Log in to Zapcut" / "Sign up" using Cognito Hosted UI or embedded form.
After login, redirect to /.
Onboarding Chat (inside same single page)
First message from system:
 “Hi, I’m your ad-building assistant. Let’s get your brand set up.”
LLM asks:
Brand name, website.
Upload logos and product images.
Describe the product & audience.
Each time the user uploads or generates an image:
Stored locally in state (React store).
Sent to backend to persist as Asset row.
Scene-building Chat
Orchestrator gradually moves user from:
“Tell me about the product” →
“Let’s break your ad into scenes” →
“Scene 1: what do you want to show?”
“Do you want to attach any images to Scene 1?”
Under the chat, you have a Scenes timeline:
Scene 1, Scene 2, Scene 3…
Each scene can be clicked to show:
prompt
Attached media[] (from gallery).
Generate Video
Once orchestrator verifies minimal requirements (e.g., at least 1 scene, at least one product image, etc.), it suggests:
“I have enough info to generate a first version. Ready?”
User clicks Generate Video.
Frontend constructs the scenes payload from local state and posts to /api/generate-video.
Preview & Export
Chat message: “Your video is being generated…”
Poll /api/generate-video/job/:jobId.
When done:
Show embedded video player in the right panel.
Show buttons: Download, Post to X, Post to LinkedIn.
Everything is basically one big chat screen with panels.
4. Main Orchestrator Agent – “Global OS” for the App
Its main responsibility is to ensure that the user is proceeding sequentially through proper stages.
You can treat this as a system-level LLM agent with explicit stages:
Stages
collect_brand_info
collect_product_info
collect_assets
collect_scenes
final_review
generate_video
export_video
The orchestrator keeps a state object:
{
  "stage": "collect_scenes",
  "brand": {...},
  "product": {...},
  "assets": [...],
  "scenes": [...],
  "safetyFlags": [],
  "videoJobId": null
}
Rules for the orchestrator:
Never move to generate_video if:
No scenes defined.
No product assets uploaded.
If user asks for something inappropriate:
Politely refuse and steer back:
 “I can’t help with that, but we can keep working on your ad.”
Prompt skeleton:
You are the Zapcut Orchestrator, a main OS for the app.
Your job:
- Maintain a stage-based workflow for creating AI-generated video ads.
- Never skip forward if required info is missing.
- Always respond in a chat style, like ChatGPT.
- Control the following stages: [list them].
- When you think we’re ready to move to the next stage, clearly state:
  `NEXT_STAGE: <stage_name>`
  and explain to the frontend what to do (e.g., ask user to upload assets, summarize scenes, etc.).
If the user asks for anything unsafe or inappropriate (NSFW, violence, hate, etc.), refuse kindly and redirect them back to ad-building tasks.
The frontend can read NEXT_STAGE: markers in assistant responses to update UI state.
5. Exporting to X (Twitter) & LinkedIn
When the user clicks Export, you’ll call your backend:
POST /api/export
Authorization: Bearer <JWT>
{
  "videoId": "vid_123",
  "targets": ["x", "linkedin"],
  "message": "Check out our new ad!"
}
Backend:
Verify video belongs to user.
Fetch video URL.
Use stored OAuth tokens for X & LinkedIn (user must have previously connected these accounts).
Send appropriate POSTs:
X (Twitter)
Upload media → get media id
Create tweet with text + attached media id.
LinkedIn
Register upload
Upload video bytes
Create post referencing the uploaded asset.
If user hasn’t connected accounts, return:
{
  "error": "accounts_not_connected",
  "connectUrls": {
    "x": "https://...oauth_url...",
    "linkedin": "https://...oauth_url..."
  }
}
6. Terraform Skeleton for AWS
You asked for:
AWS Terraform resources: Cognito authentication, RDS PostgreSQL, Elastic Beanstalk back-end server, and the queue.
Below is a concise skeleton (not exhaustive, but structurally correct) you can expand.
# providers.tf
provider "aws" {
  region = "us-east-1"
}
# -----------------------------
# Cognito User Pool + Client
# -----------------------------
resource "aws_cognito_user_pool" "zapcut_user_pool" {
  name = "zapcut-user-pool"
  auto_verified_attributes = ["email"]
  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false
    require_uppercase = true
  }
}
resource "aws_cognito_user_pool_client" "zapcut_user_pool_client" {
  name         = "zapcut-app-client"
  user_pool_id = aws_cognito_user_pool.zapcut_user_pool.id
  generate_secret = false
  callback_urls   = ["https://app.zapcut.video"]
  logout_urls     = ["https://zapcut.video"]
  allowed_oauth_flows       = ["code"]
  allowed_oauth_scopes      = ["email", "openid", "profile"]
  allowed_oauth_flows_user_pool_client = true
  supported_identity_providers = ["COGNITO"]
}
# -----------------------------
# RDS PostgreSQL
# -----------------------------
resource "aws_db_subnet_group" "zapcut_db_subnet_group" {
  name       = "zapcut-db-subnet-group"
  subnet_ids = [aws_subnet.private1.id, aws_subnet.private2.id] # define subnets elsewhere
}
resource "aws_db_instance" "zapcut_postgres" {
  allocated_storage    = 20
  engine               = "postgres"
  engine_version       = "16.1"
  instance_class       = "db.t3.micro"
  name                 = "zapcutdb"
  username             = "zapcut_admin"
  password             = var.db_password
  parameter_group_name = "default.postgres16"
  db_subnet_group_name = aws_db_subnet_group.zapcut_db_subnet_group.name
  skip_final_snapshot  = true
  publicly_accessible  = false
  vpc_security_group_ids = [aws_security_group.db_sg.id]
}
# -----------------------------
# SQS Queue for Video Jobs
# -----------------------------
resource "aws_sqs_queue" "video_jobs_queue" {
  name                      = "zapcut-video-jobs-queue"
  visibility_timeout_seconds = 900 # 15 minutes
}
# -----------------------------
# Elastic Beanstalk Application
# -----------------------------
resource "aws_elastic_beanstalk_application" "zapcut_app" {
  name        = "zapcut-backend"
  description = "Backend API for Zapcut video generation"
}
resource "aws_elastic_beanstalk_environment" "zapcut_env" {
  name                = "zapcut-backend-env"
  application         = aws_elastic_beanstalk_application.zapcut_app.name
  solution_stack_name = "64bit Amazon Linux 2 v5.8.4 running Node.js 20" # example
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "DATABASE_URL"
    value     = "postgres://${aws_db_instance.zapcut_postgres.username}:${var.db_password}@${aws_db_instance.zapcut_postgres.address}:5432/${aws_db_instance.zapcut_postgres.name}"
  }
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "COGNITO_USER_POOL_ID"
    value     = aws_cognito_user_pool.zapcut_user_pool.id
  }
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "VIDEO_JOBS_QUEUE_URL"
    value     = aws_sqs_queue.video_jobs_queue.id
  }
}
You’d also define:
VPC, subnets, security groups.
IAM roles:
For Elastic Beanstalk instances to read SQS, write logs, access S3, etc.
S3 buckets:
For storing images and video assets.
If you’d like, next I can:
Turn the generate-video endpoint into full TypeScript route + types.
Or give you a React SPA structure (components + state shape) for the ChatGPT-style single page



Perfect inputs for Sora:
1. What “perfect inputs” should the frontend send?
Think of the frontend payload as a Story Design Document + Brand/Style DNA + Control Signals.
1.1. Top-level input object (frontend → FastAPI)
{
  "project_id": "brand_campaign_2025_q1",
  "story_title": "The Curious Umbrella",
  "story_logline": "A playful umbrella discovers a magical city in the rain.",
  "global_style": {
    "visual_style": "3D Pixar-like, soft global illumination, cinematic depth of field",
    "aspect_ratio": "16:9",
    "resolution": "1920x1080",
    "frame_rate": 24,
    "color_palette": ["#F6C453", "#FF6B6B", "#4ECDC4", "#1A535C"],
    "camera_language": "slow, smooth cinematic camera, gentle dolly and pan, minimal fast cuts",
    "brand_constraints": {
      "primary_logo_url": "https://cdn.brand.com/logo.png",
      "logo_usage_rules": "Show logo only in final scene, bottom right, subtle 70% opacity",
      "font_style": "Rounded sans-serif, similar to Nunito",
      "forbidden_elements": [
        "realistic violence", "guns", "smoking", "explicit content"
      ]
    }
  },
  "narrative_beats": {
    "target_duration_seconds": 45,
    "target_num_scenes": 5,
    "structure": "3-act",
    "beat_notes": "Scene 1 = setup, 2-3 = exploration, 4 = complication, 5 = resolution with CTA"
  },
  "generation_controls": {
    "determinism_level": 0.8,
    "creativity_level": 0.7,
    "max_variations_per_scene": 2,
    "allow_style_evolution": true,
    "transition_continuity": "high", 
    "seed_strategy": "fixed_per_scene_chain_across_clips"
  },
  "scenes": [
    {
      "scene_index": 1,
      "scene_title": "The First Raindrop",
      "text_seed_prompt": "Close-up shot of a colorful umbrella resting by a window as the first raindrop hits the glass, cozy evening city in the background, warm interior light and cool blue reflections outside.",
      "seed_image_url": "https://cdn.app.com/user_uploads/project123/scene1_seed.png",
      "duration_seconds": 8,
      "role_in_story": "setup",
      "key_story_events": [
        "Introduce the umbrella as main character",
        "Establish cozy interior vs rainy city outside",
        "No brand elements yet"
      ],
      "camera_direction": "Start with static shot, very subtle push-in towards umbrella.",
      "emotion_tone": "curious, warm, slightly melancholic",
      "safety_requirements": ["no faces visible", "no text on screen"]
    },
    {
      "scene_index": 2,
      "scene_title": "Stepping into the Rain",
      "text_seed_prompt": "The umbrella opens as a hand reaches for it, door opens to reveal a magical version of the city, neon reflections in puddles, whimsical atmosphere.",
      "seed_image_url": "https://cdn.app.com/user_uploads/project123/scene2_seed.png",
      "duration_seconds": 10,
      "role_in_story": "inciting_incident",
      "key_story_events": [
        "Umbrella transitions from inside to outside",
        "Reveal more of the magical city",
        "Camera follows movement from door to street"
      ],
      "camera_direction": "Follow the umbrella from behind as it moves out into the rain, gentle handheld feel.",
      "emotion_tone": "excited, wondrous",
      "safety_requirements": ["no identifiable faces", "no branded storefronts"]
    }
    // scenes 3–5 ...
  ]
}
1.2. Quantity vs quality of inputs
Quantity (per project):
Global / project-level:
1 story logline
1–3 paragraph synopsis (optional but very helpful)
1 global visual style block
1 brand constraints block
1 narrative beats block (duration, 3-act structure)
1 generation controls block
Per scene:
1 strong text seed prompt
0–1 seed image (required for style consistency if you have brand look)
1 duration (seconds)
3–7 key story events
1 camera_direction
1 emotion_tone
1 safety_requirements list
Quality (what “good” looks like):
Concrete nouns: “red bicycle with a wicker basket” > “cool bike.”
Stable character definitions: “small yellow umbrella with a blue stripe and a tiny smiley-face tag” repeated across scenes.
Consistent style phrases: reuse “3D Pixar-like, soft global illumination, cinematic depth of field” everywhere.
Explicit continuity hints:
“same umbrella as scene 1”
“continue from previous shot where camera is behind the umbrella”
“preserve color palette and lighting mood from the last scene”
2. Orchestrator’s JSON output schema for Sora prompts
Your orchestrator takes that frontend payload and produces a generation plan:
{
  "project_id": "brand_campaign_2025_q1",
  "global_style": { /* mostly copied through, maybe normalized */ },
  "scenes_plan": [
    {
      "scene_index": 1,
      "source": {
        "frontend_scene_id": 1
      },
      "sora_prompt": {
        "prompt": "Close-up cinematic video, 3D Pixar-like soft global illumination... [full combined prompt]",
        "negative_prompt": "realistic violence, gore, smoking, explicit content, low quality, text overlay",
        "duration": 8,
        "fps": 24,
        "resolution": "1920x1080",
        "aspect_ratio": "16:9",
        "seed": 123456,
        "guidance_scale": 7.5,
        "style_strength": 0.8,
        "motion_strength": 0.6,
        "input_image_url": "https://cdn.app.com/user_uploads/project123/scene1_seed.png",
        "transition_in_strategy": "fade_in_from_black",
        "transition_out_strategy": "hold_last_frame_0.5s",
        "metadata": {
          "role_in_story": "setup",
          "emotion_tone": "curious, warm, slightly melancholic"
        }
      }
    },
    {
      "scene_index": 2,
      "source": {
        "frontend_scene_id": 2,
        "prior_scene_index": 1,
        "prior_scene_last_frame_url": "https://cdn.app.com/renders/project123/scene1_lastframe.png"
      },
      "sora_prompt": {
        "prompt": "Continue from the previous shot, same small yellow umbrella with a blue stripe and smiley tag, camera behind the umbrella as it moves through the doorway into a magical neon-lit rainy city... [full text]",
        "negative_prompt": "realistic violence, gore, smoking, explicit content, low quality, text overlay",
        "duration": 10,
        "fps": 24,
        "resolution": "1920x1080",
        "aspect_ratio": "16:9",
        "seed": 123457,
        "guidance_scale": 7.0,
        "style_strength": 0.9,
        "motion_strength": 0.7,
        "input_image_url": "https://cdn.app.com/renders/project123/scene1_lastframe.png",
        "aux_seed_image_url": "https://cdn.app.com/user_uploads/project123/scene2_seed.png",
        "transition_in_strategy": "cut_from_prior_last_frame",
        "transition_out_strategy": "match_cut_to_next_scene",
        "metadata": {
          "role_in_story": "inciting_incident",
          "emotion_tone": "excited, wondrous"
        }
      }
    }
  ]
}
You can think of this as the “orchestrator output contract”: the only thing your FastAPI side needs to hand to the Replicate/Sora client.
3. Multi-agent workflow: who does what?
Here’s a clean agent layout for your orchestrator. You don’t need to overcomplicate it; you just need clear responsibilities and shared scratchpad state.
3.1. Agents
Story Structuring Agent
Input: raw frontend payload.
Output: normalized story outline (per-scene roles, beats, emotional arcs).
Tasks:
Validate that the scenes logically cover setup → conflict → resolution.
Auto-fill any missing scene descriptions (e.g., user gave only 3 scenes but wants 45s).
Ensure each scene has a “role_in_story” label and “key_story_events”.
Style & Brand Consistency Agent
Input: global_style + brand_constraints + each scene.
Output: enriched per-scene “style block”.
Tasks:
Inject consistent phrases into prompts (“3D Pixar-like…”) if missing.
Enforce forbidden elements and safety constraints.
Insert brand rules only into allowed scenes (e.g., logo only in final).
Prompt Synthesis Agent
Input: scene outline + style block + continuity info.
Output: final “sora_prompt.prompt” and “negative_prompt” per scene.
Tasks:
Merge: text_seed_prompt + global style + camera_direction + emotion_tone.
Add continuity language:
Scene 1: “Establish the umbrella character…”
Scene N>1: “Continue from previous scene, same characters + lighting…”
Manage creativity vs determinism:
determinism_level → guidance_scale, seed reuse strategy.
creativity_level → add variation phrases, camera motion richness.
Continuity / Back-Prop Agent
Input: previous scene outputs (once generated), last frame URLs, prompts.
Output: updated prompts for future scenes, plus updated seeds if needed.
Tasks:
For scene N, automatically plug in prior_scene_last_frame_url as input_image_url.
Optionally adjust seeds when prior scene had unexpected style drift.
Maintain a “continuity state”:



 {
  "current_palette": [...],
  "character_descriptions": "...",
  "camera_position_last_scene": "behind umbrella, low angle"
}




Back-prop gating: if scene N renders too far off-style, it can:
Request a variation of scene N–1, or
Tighten the description for scene N and regenerate.
Safety & Policy Agent
Input: proposed prompts + brand/safety rules.
Output: allowed / modified prompts.
Tasks:
Strip any disallowed content, add strong negative prompts.
Optionally simplify scenes with questionable edge cases (kids, sensitive topics).
JSON Schema Builder Agent
Input: all enriched per-scene objects.
Output: final orchestrator JSON (as above).
Tasks:
Validate required fields for Replicate/Sora.
Enforce consistent resolutions/aspect_ratio/fps.
Produce machine-readable plan + human-readable summary.
4. FastAPI orchestration flow (high-level)
Pseudo-flow (sketch):
# POST /api/generate-video-plan
def generate_video_plan(request: FrontendRequest):
    # 1. Validate & normalize input
    normalized = story_structuring_agent(request)
    # 2. Apply global style & brand rules
    styled = style_brand_agent(normalized)
    # 3. Draft prompts for all scenes (without continuity frames)
    drafted_prompts = prompt_synthesis_agent(styled)
    # 4. Build initial JSON plan (no last-frame chaining yet)
    plan = json_schema_builder_agent(drafted_prompts)
    return plan
Then a second endpoint / background worker that does the actual generation + back-prop chaining:
# Worker / background task
def execute_video_plan(plan: SoraPlan):
    for scene in plan["scenes_plan"]:
        # For scene_index > 1, inject last frame from prior scene
        if scene["scene_index"] > 1:
            prev_scene = get_prev_scene(scene, plan)
            last_frame_url = extract_last_frame(prev_scene["render_result"])
            scene["sora_prompt"]["input_image_url"] = last_frame_url
            scene = continuity_agent(scene, prev_scene, last_frame_url)
        # Call Replicate/Sora with scene["sora_prompt"]
        render_result = call_replicate_sora(scene["sora_prompt"])
        scene["render_result"] = render_result
        persist_scene_result(scene)
    # At the end, you can stitch the clips into a single final video
    return assemble_final_video(plan)
You can keep the user’s UX asynchronous (progress updates per scene).
5. Making it deterministic and creative
You’re juggling 3 knobs:
Determinism
Fix:
seeds per scene, or even a global project_seed + (scene_index offset).
resolution, fps, aspect ratio, duration.
Keep:
global style phrases constant.
identical character descriptors everywhere.
Creativity
Allow:
scene-specific “flourishes” (“magical neon bokeh”, “playful raindrops swirling”).
controlled camera variety (“low angle”, “over-the-shoulder”, “wide establishing shot”).
But keep them bounded by:
cameras still “cinematic, smooth, no shaky cam.”
lighting staying inside your palette.
Continuity
Use back-prop via last frame:
input_image_url = last_frame_of_previous_scene
Add explicit continuity instructions:
“Continue from the last frame where the umbrella is mid-step into the street.”
Maintain a continuity memory object that each agent reads/writes.
A good rule of thumb:
High determinism: reuse seeds, narrow prompts, higher guidance_scale.
High creativity: more descriptive variation, slightly lower guidance_scale, but never change the core identifying descriptors.
6. Concrete example of one scene’s generated Sora prompt
Suppose Scene 3 comes after umbrella entering the city.
Front-end scene:
{
  "scene_index": 3,
  "scene_title": "Dancing Lights",
  "text_seed_prompt": "The umbrella twirls in the middle of a reflective street crosswalk as neon signs shimmer in the puddles around it.",
  "seed_image_url": "https://cdn.app.com/user_uploads/project123/scene3_seed.png",
  "duration_seconds": 10,
  "role_in_story": "exploration",
  "key_story_events": [
    "Umbrella in middle of street",
    "Puddles reflecting neon signs",
    "No humans in frame"
  ],
  "camera_direction": "Orbit slowly around the umbrella in a smooth circular motion.",
  "emotion_tone": "playful, magical"
}
Orchestrator’s final Sora prompt:
{
  "prompt": "Continue directly from the previous scene where the small yellow umbrella with a blue stripe and smiley-face tag has just stepped into the magical rainy city. 3D Pixar-like style, soft global illumination, cinematic depth of field. The umbrella now twirls in the middle of a rain-soaked street crosswalk at night, surrounded by glowing neon signs whose colors reflect in puddles on the ground. No humans visible in the frame. Smooth, slow orbiting camera motion around the umbrella, preserving the same color palette and lighting mood as the previous scene. Playful, magical atmosphere.",
  "negative_prompt": "realistic violence, gore, smoking, explicit content, low resolution, text overlays, brand logos",
  "duration": 10,
  "fps": 24,
  "resolution": "1920x1080",
  "aspect_ratio": "16:9",
  "seed": 123458,
  "guidance_scale": 7.0,
  "style_strength": 0.85,
  "motion_strength": 0.7,
  "input_image_url": "https://cdn.app.com/renders/project123/scene2_lastframe.png",
  "aux_seed_image_url": "https://cdn.app.com/user_uploads/project123/scene3_seed.png",
  "transition_in_strategy": "match_cut_from_prior_scene",
  "transition_out_strategy": "soft hold for 0.5s on final twirl",
  "metadata": {
    "scene_index": 3,
    "role_in_story": "exploration",
    "emotion_tone": "playful, magical"
  }
}
If you like, next I can:
Turn this into a formal JSON Schema document for the orchestrator output, and/or
Sketch the actual FastAPI endpoint contracts + Pydantic models for request/response so you can drop them into your repo.


The style template of this entire app should use consistent and reused color palettes, themes and layouts.  Our app's icon is a bright yellow lightning bolt with a white cursor color, so use those colors as shocking highlights. Use glass morphism for all styles and designs throughout the entire app for a clean beautiful modern high-class :crown::gem: Use lucide React icons for all icons