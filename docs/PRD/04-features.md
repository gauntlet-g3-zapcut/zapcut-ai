# Features & Requirements

## MVP Features (Week 1: Phase 1)

### Must-Have Features (P0)

#### 1. User Authentication
**Status**: Required for MVP  
**Priority**: P0

- AWS Cognito integration for user accounts
- Email/password and Google OAuth sign-up
- JWT-based session management
- Secure token storage and refresh

**Acceptance Criteria**:
- [ ] User can sign up with email + password
- [ ] User can sign in with Google OAuth
- [ ] JWT persists across browser sessions
- [ ] Expired tokens refresh automatically

---

#### 2. Brand/Project Management
**Status**: Required for MVP  
**Priority**: P0

- Create new brand/project
- Store brand name, product description
- Upload 2-4 product images
- View list of user's projects
- Select existing project to create new ad

**Acceptance Criteria**:
- [ ] User can create a new project with name + description
- [ ] User can upload up to 4 images per project (5MB max each)
- [ ] Images uploaded to S3 and URLs stored in database
- [ ] User can view all their projects in a list
- [ ] User can select a project to create a new ad

---

#### 3. Creative Brief Chat Interface
**Status**: Required for MVP  
**Priority**: P0

- Single-page chat interface (ChatGPT-style)
- Orchestrator agent guides user through stages:
  1. Brand info collection
  2. Product details
  3. Visual assets upload
  4. Creative direction briefing
  5. Scene planning
  6. Final review
- Natural language input for all questions
- Stage validation (can't skip required info)
- Safety filtering on all user inputs

**Acceptance Criteria**:
- [ ] Chat interface displays messages chronologically
- [ ] Orchestrator asks for brand name, product, images, creative direction
- [ ] User cannot proceed to generation without required inputs
- [ ] Unsafe or inappropriate requests are rejected with helpful alternatives
- [ ] Chat history persists for the session
- [ ] User can see current stage indicator

---

#### 4. Creative Bible Generation
**Status**: Required for MVP  
**Priority**: P0

- Analyze user's brief + product images
- Generate style parameters:
  - Visual style description
  - Color palette (4-6 colors)
  - Lighting rules
  - Camera language
  - Motion style
  - Energy level
- Store Creative Bible in database
- Allow reuse for future ads

**Acceptance Criteria**:
- [ ] Creative Bible generated from user brief in <30 seconds
- [ ] Contains all required fields (style, colors, lighting, camera, motion, energy)
- [ ] Stored in database linked to project
- [ ] User can see Creative Bible summary before generation
- [ ] Creative Bible can be reused for subsequent ads

---

#### 5. Reference Image Generation
**Status**: Required for MVP  
**Priority**: P0

- Generate 4 reference images using DALL-E 3:
  1. Hero product shot
  2. Detail/close-up shot
  3. Lifestyle/context shot
  4. Alternate angle
- Use Creative Bible to ensure style consistency
- Store image URLs in Creative Bible record

**Acceptance Criteria**:
- [ ] 4 reference images generated in parallel
- [ ] All images match Creative Bible style
- [ ] Product appearance consistent across all 4 images
- [ ] Generation completes in <60 seconds
- [ ] URLs stored and accessible for Sora prompts

---

#### 6. Scene Storyboard Generation
**Status**: Required for MVP  
**Priority**: P0

- Generate 5-scene storyboard for 30-second ad
- Each scene includes:
  - Scene title and description
  - Duration (seconds)
  - Role in story (setup, conflict, resolution)
  - Camera direction
  - Emotion tone
  - Key story events
- Validate total duration matches target (30s)

**Acceptance Criteria**:
- [ ] Storyboard generated in <15 seconds
- [ ] Contains 5 scenes totaling 30 seconds
- [ ] Each scene has complete required fields
- [ ] Scenes follow logical narrative progression
- [ ] User can review storyboard before approving generation

---

#### 7. Video Scene Generation (Sora)
**Status**: Required for MVP  
**Priority**: P0

- Generate 5 video scenes using Sora via Replicate
- Each scene: 6 seconds, 1920x1080, 30fps
- Include reference image URLs in prompts
- Use Creative Bible for style consistency
- Apply continuity back-propagation (scene N uses last frame of scene N-1)
- Parallel generation of all 5 scenes
- Retry logic for failed generations (3 attempts)

**Acceptance Criteria**:
- [ ] All 5 scenes generate successfully 90%+ of the time
- [ ] Visual style consistent across all scenes
- [ ] Product appearance matches reference images
- [ ] Scene transitions feel natural (last frame → first frame continuity)
- [ ] Generation completes in <3 minutes for all 5 scenes
- [ ] Failed scenes retry up to 3 times before surfacing error

---

#### 8. Music Generation (Suno)
**Status**: Required for MVP  
**Priority**: P0

- Generate 30-second background music using Suno
- Match energy progression of video scenes
- Style based on Creative Bible (e.g., "calm", "energetic", "premium")
- No vocals, royalty-free, commercial quality
- Generate in parallel with video scenes

**Acceptance Criteria**:
- [ ] Music generated in <2 minutes
- [ ] Audio length exactly 30 seconds
- [ ] Energy level matches storyboard progression
- [ ] No vocals, instrumental only
- [ ] Audio quality suitable for commercial use
- [ ] Generation starts in parallel with Sora calls

---

#### 9. Video Composition
**Status**: Required for MVP  
**Priority**: P0

- Stitch 5 video scenes using FFmpeg
- Add 0.5-second crossfade transitions between scenes
- Mix Suno audio track underneath
- Add text overlays:
  - Product name (appears at 24s)
  - CTA text "Learn More" (appears at 27s)
- Encode to H.264, 1080p, 30fps
- Upload final video to S3

**Acceptance Criteria**:
- [ ] All 5 scenes stitched correctly
- [ ] Crossfade transitions smooth (no jarring cuts)
- [ ] Audio synced properly (no drift)
- [ ] Text overlays appear at correct times
- [ ] Final video file size <50MB
- [ ] Composition completes in <45 seconds
- [ ] Video uploaded to S3 with public URL

---

#### 10. Progress Tracking & Status Updates
**Status**: Required for MVP  
**Priority**: P0

- Show real-time generation progress in UI
- Display current stage:
  - Creative Bible generation
  - Reference images
  - Scene 1-5 rendering
  - Music generation
  - Final composition
- Show estimated time remaining
- Handle errors gracefully with user-friendly messages

**Acceptance Criteria**:
- [ ] Progress bar updates in real-time
- [ ] User sees which scene is currently rendering
- [ ] Estimated time remaining displayed and accurate within 30s
- [ ] Errors explained clearly ("Scene 3 failed, retrying...")
- [ ] User can cancel generation mid-process

---

#### 11. Video Preview & Download
**Status**: Required for MVP  
**Priority**: P0

- Embedded video player to preview generated ad
- Play/pause controls, volume slider
- Download button (exports MP4)
- Display video metadata (duration, resolution, file size)

**Acceptance Criteria**:
- [ ] Video plays correctly in browser
- [ ] Play/pause and volume controls work
- [ ] Download button triggers file download
- [ ] Downloaded MP4 plays in any standard player
- [ ] User can preview video before downloading

---

#### 12. Safety & Content Moderation
**Status**: Required for MVP  
**Priority**: P0

- Safety Validation Agent checks all prompts before generation
- Block prohibited content:
  - Violence, gore, weapons
  - Sexual content, nudity
  - Drugs, smoking, alcohol (unless explicitly allowed)
  - Hate speech, extremism
  - Deepfakes, real people likenesses
  - Copyrighted characters
- Suggest safe alternatives when blocking content
- Validate all scene descriptions and prompts

**Acceptance Criteria**:
- [ ] Unsafe prompts blocked before reaching Sora
- [ ] User sees clear explanation of why content was blocked
- [ ] Alternative suggestions provided
- [ ] Safety check completes in <5 seconds
- [ ] False positive rate <5%

---

## Should-Have Features (P1)

### 13. Creative Bible Reuse
**Status**: Post-MVP Polish  
**Priority**: P1

- When generating a second ad for same project, reuse existing Creative Bible
- Skip reference image generation (use cached images)
- Faster generation (3 min instead of 5 min)
- Cost savings (40% cheaper)

**Acceptance Criteria**:
- [ ] System detects existing Creative Bible for project
- [ ] User can choose "Use existing style" or "Create new style"
- [ ] Generation time reduced by ~2 minutes
- [ ] Visual consistency maintained across ads

---

### 14. Scene Editing & Regeneration
**Status**: Post-MVP Polish  
**Priority**: P1

- User can request regeneration of specific scene
- Edit scene description via chat ("Make Scene 3 brighter")
- Regenerate just that scene without re-doing entire video
- Re-compose video with new scene

**Acceptance Criteria**:
- [ ] User can click on scene in preview to edit it
- [ ] Natural language edit commands work ("make this darker", "add more motion")
- [ ] Only selected scene regenerates
- [ ] Video recomposition takes <1 minute

---

### 15. Variation Generation
**Status**: Post-MVP Polish  
**Priority**: P1

- Generate 3-5 variations of same ad
- Vary specific elements (opening scene, product placement, camera angles)
- Keep Creative Bible and core narrative same
- Batch generation in parallel

**Acceptance Criteria**:
- [ ] User can request "Generate 3 variations"
- [ ] All variations maintain brand consistency
- [ ] Batch generation takes ~5 minutes for 3 ads
- [ ] User sees all variations side-by-side to compare

---

### 16. Social Media Direct Publishing
**Status**: Post-MVP Polish  
**Priority**: P1

- OAuth integration with X (Twitter) and LinkedIn
- One-click "Post to X" and "Post to LinkedIn"
- Custom caption editor
- Confirmation modal before posting
- Show published post URLs

**Acceptance Criteria**:
- [ ] User can connect X and LinkedIn accounts via OAuth
- [ ] "Post to X" uploads video and creates tweet
- [ ] "Post to LinkedIn" uploads video and creates post
- [ ] User can edit caption before posting
- [ ] Links to published posts shown after success

---

## Nice-to-Have Features (P2)

### 17. Aspect Ratio Options
**Status**: Future Enhancement  
**Priority**: P2

- Generate same ad in multiple aspect ratios:
  - 16:9 (landscape - YouTube, Twitter)
  - 9:16 (vertical - TikTok, Instagram Stories)
  - 1:1 (square - Instagram feed, LinkedIn)
- Batch export all formats at once

---

### 18. Advanced Text Overlay Customization
**Status**: Future Enhancement  
**Priority**: P2

- Custom text overlays beyond product name + CTA
- Choose font, color, position, animation
- Multiple text elements per scene
- Brand typography enforcement

---

### 19. Voiceover Generation
**Status**: Future Enhancement  
**Priority**: P2

- Text-to-speech voiceover using ElevenLabs or similar
- Choose voice style (friendly, professional, energetic)
- Sync voiceover to video timing
- Multiple language support

---

### 20. Brand Asset Library
**Status**: Future Enhancement  
**Priority**: P2

- Upload brand guidelines PDF
- Store logo variations (horizontal, stacked, icon-only)
- Color palette library with Pantone codes
- Font uploads
- Automatic brand rule enforcement

---

### 21. Cost Tracking & Budgets
**Status**: Future Enhancement  
**Priority**: P2

- Display generation cost per video
- Show total spend per project
- Set monthly budgets
- Alert when approaching limit

---

### 22. Analytics & Performance Tracking
**Status**: Future Enhancement  
**Priority**: P2

- Track video views, engagement from published posts
- A/B test results comparison
- Best-performing variations dashboard
- Export analytics reports

---

### 23. Team Collaboration
**Status**: Enterprise Phase  
**Priority**: P3

- Multi-user accounts
- Shared brand libraries
- Comment and approval workflows
- Version history
- Role-based permissions (admin, editor, viewer)

---

### 24. Custom LoRA Training
**Status**: Enterprise Phase  
**Priority**: P3

- Train custom LoRA models on brand assets
- Ultra-consistent product appearance
- Brand-specific visual style
- Character/mascot consistency

---

### 25. API Access
**Status**: Enterprise Phase  
**Priority**: P3

- REST API for programmatic video generation
- Webhook notifications for completion
- Batch job management
- White-label embedding

---

## Technical Requirements

### Performance Targets
- **Generation Speed**: <5 minutes for 30-second ad (MVP)
- **API Response Time**: <200ms for chat interactions
- **Video Composition**: <45 seconds for 5-scene stitch
- **Uptime**: 99.5% availability

### Cost Targets
- **Per Video Cost**: <$2.50 for 30-second ad (MVP)
- **Infrastructure**: <$500/month for MVP deployment
- **Scalability**: Support 100 concurrent generation jobs

### Quality Targets
- **Visual Consistency**: 90%+ user satisfaction
- **Generation Success Rate**: 90%+ first-try success
- **Audio-Visual Sync**: Zero drift, proper fade-in/fade-out

### Security Requirements
- **Authentication**: JWT with 1-hour expiration, refresh tokens
- **Data Encryption**: TLS 1.3 for all API calls, S3 encryption at rest
- **PII Protection**: No storage of payment info (Stripe handles)
- **Content Safety**: 100% of prompts pass safety check before generation

---

## Out of Scope (Not Building)

### ❌ Manual Video Editing Tools
We're not building a timeline editor with manual clip trimming, transitions, effects. Users who need frame-by-frame control should use Premiere Pro or DaVinci Resolve.

### ❌ Stock Footage Library
We're not hosting stock video or image libraries. Everything is AI-generated or user-uploaded.

### ❌ Real-Time Collaboration
MVP won't have multi-user editing sessions or live collaboration features. Focus is on single-user generation speed.

### ❌ Mobile Apps
MVP is web-only. Mobile apps (iOS/Android) are Phase 3+.

### ❌ Email Marketing Integration
No direct integration with Mailchimp, Constant Contact, etc. Users download and upload manually.

---

**Last Updated**: November 15, 2025  
**Status**: Active Development  
**Next Review**: November 20, 2025

