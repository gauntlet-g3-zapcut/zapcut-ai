# Product Requirements Document: AI Video Generation Pipeline for Ad Creation

## Executive Summary

### Product Vision
Transform Zapcut from a standalone video editor into an AI-powered ad generation platform that enables users to create professional video advertisements through conversational AI interactions, automated asset generation, and intelligent video composition.

### Core Value Proposition
Enable users to generate high-quality video advertisements by simply describing their product and campaign goals, with AI handling script creation, visual asset generation (via Sora), audio composition (via Suni), and video editing - culminating in a fully editable video in Zapcut's video editor.

### Success Metrics
- Time to create first ad: < 10 minutes (from brand creation to generated video)
- User satisfaction with AI-generated scripts: > 80% approval rate
- Video generation success rate: > 95%
- User retention after first ad creation: > 60%

---

## 1. Product Overview

### 1.1 Product Context
This product extends the existing Zapcut video editor (Electron-based application) with an AI-powered ad generation workflow. The video editor will become the final step in a comprehensive ad creation pipeline, allowing users to refine AI-generated content.

### 1.2 Target Users
- **Primary**: Small business owners and marketers creating social media ads
- **Secondary**: Content creators and agencies managing multiple brand campaigns
- **Tertiary**: E-commerce sellers needing product advertisement videos

### 1.3 User Problems Solved
1. **Time-intensive ad creation**: Traditional video editing requires hours; our solution generates ads in minutes
2. **Lack of creative expertise**: AI guides users through the creative process with intelligent questions
3. **Complex tooling**: Conversational interface replaces complex video editing workflows
4. **Asset creation bottleneck**: Automated generation of visuals and audio eliminates production delays

---

## 2. Technical Architecture

### 2.1 Tech Stack

#### Frontend
- **Framework**: React + TypeScript (existing)
- **UI Library**: Lucide React icons
- **Styling**: TailwindCSS with glassmorphism design system
- **State Management**: Zustand (existing)
- **Desktop**: Electron (existing)

#### Backend Services (New)
- **API Server**: Node.js/Express or Python/FastAPI
- **Database**: PostgreSQL (user data, brands, projects)
- **Queue**: Redis + Bull (video generation jobs)
- **Storage**: AWS S3 (media assets, generated videos)
- **Authentication**: Supabase Auth

#### AI/ML Services
- **LLM**: OpenAI GPT-4 (conversational interface, script generation)
- **Image Generation**: OpenAI DALL-E 3 (product imagery, b-roll)
- **Video Generation**: Sora via Replicate API
- **Audio Generation**: Suni (voiceover, background music)
- **Fine-tuning**: LoRA for brand-specific video style customization

### 2.2 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Electron + React)              │
│  ┌──────────┬──────────┬───────────┬──────────┬──────────┐ │
│  │ Landing  │  Auth    │  Brands   │   Chat   │  Editor  │ │
│  │  Page    │  Pages   │ Dashboard │   AI     │  Canvas  │ │
│  └──────────┴──────────┴───────────┴──────────┴──────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API / WebSocket
┌────────────────────────┴────────────────────────────────────┐
│                      Backend Services                        │
│  ┌─────────────┬──────────────┬─────────────┬────────────┐ │
│  │   API       │   Auth       │   Brand     │   Video    │ │
│  │  Gateway    │  Service     │  Service    │  Service   │ │
│  └─────────────┴──────────────┴─────────────┴────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    External AI Services                      │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ OpenAI   │  Sora    │  Suni    │  LoRA    │   S3     │  │
│  │ GPT-4    │(Replicate)│  Audio  │Fine-tune │ Storage  │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Data Models

#### User
```typescript
interface User {
  id: string;
  email: string;
  name: string;
  createdAt: Date;
  subscription: 'free' | 'pro' | 'enterprise';
}
```

#### Brand
```typescript
interface Brand {
  id: string;
  userId: string;
  title: string;
  description: string;
  productImages: string[]; // Min 2 required, S3 URLs
  brandGuidelines?: {
    colors: string[];
    fonts: string[];
    tone: string;
    additionalAssets: string[];
  };
  createdAt: Date;
  updatedAt: Date;
}
```

#### AdProject
```typescript
interface AdProject {
  id: string;
  brandId: string;
  userId: string;
  conversationHistory: ChatMessage[];
  adDetails: {
    targetAudience?: string;
    adPlatform?: string; // 'instagram' | 'facebook' | 'tiktok' | 'youtube'
    adDuration?: number; // seconds
    callToAction?: string;
    keyMessage?: string;
  };
  script?: {
    storyline: string;
    scenes: Scene[];
    voiceoverText?: string;
    approvedAt?: Date;
  };
  videoGeneration?: {
    status: 'pending' | 'processing' | 'completed' | 'failed';
    replicateJobId?: string;
    generatedVideoUrl?: string;
    startedAt?: Date;
    completedAt?: Date;
    errorMessage?: string;
  };
  zapcutProjectId?: string; // Links to Zapcut editor project
  createdAt: Date;
  updatedAt: Date;
}
```

#### ChatMessage
```typescript
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}
```

#### Scene
```typescript
interface Scene {
  id: string;
  sceneNumber: number;
  description: string;
  duration: number; // seconds
  visualPrompt: string; // For Sora generation
  audioPrompt?: string; // For Suni generation
  generatedVideoUrl?: string;
  generatedAudioUrl?: string;
}
```

---

## 3. Feature Requirements

### 3.1 Authentication & Landing

#### 3.1.1 Landing Page
**Priority**: P0 (MVP)

**Requirements**:
- Clean, modern landing page showcasing the product value
- Glassmorphism design with yellow lightning bolt branding
- Hero section with compelling value proposition
- "Login" button in top-right navigation
- Responsive design (desktop-first, mobile-friendly)

**Design Guidelines**:
- Background: Gradient cosmic/dark theme (existing from video editor)
- Primary CTA: Bright yellow (#FFEB3B or similar)
- Accent: White cursor/pointer elements
- Glass cards with backdrop-blur for feature sections

#### 3.1.2 Authentication System
**Priority**: P0 (MVP)

**Requirements**:
- Email/password authentication
- OAuth integration (Google, at minimum)
- Protected route middleware
- Session management
- Password reset flow

**Post-login Behavior**:
- Redirect to Brands Dashboard
- Persist authentication state across app restarts

---

### 3.2 Brands Dashboard (Projects Page)

#### 3.2.1 Layout
**Priority**: P0 (MVP)

**Requirements**:
- **Left Sidebar**: Navigation and user info
  - User avatar and name
  - Navigation items: "Brands", "Projects", "Settings"
  - Credits/usage indicator (future: subscription tier)
- **Main Area**: Brands grid
  - Header: "Brands" with "Create Brand" button (primary yellow CTA)
  - Grid of brand cards (2-3 columns)
  - Each card shows: brand thumbnail (from product images), brand name, creation date, project count
  - Empty state: Centered illustration with "No brands yet" + "Create Brand" button

**Interactions**:
- Click on brand card → Navigate to Chat Interface for that brand
- Click "Create Brand" → Open brand creation modal

#### 3.2.2 Brand Creation
**Priority**: P0 (MVP)

**Requirements**:
- Modal/page with glassmorphism container
- **Required Fields**:
  1. Brand Title (text input)
  2. Brand Description (textarea, 500 char max)
  3. Product Images (file upload, minimum 2, maximum 10)
     - Accepted formats: JPG, PNG, WEBP
     - Max file size: 10MB per image
     - Image preview grid
- **Optional Fields** (expandable section):
  - Brand colors (color picker, up to 5 colors)
  - Brand fonts (text input or dropdown)
  - Tone of voice (text input)
  - Additional brand assets (file upload)
- **Validation**:
  - All required fields must be filled
  - At least 2 product images required
- **Actions**:
  - "Cancel" button (secondary)
  - "Create Brand" button (primary yellow, disabled until valid)

**Backend**:
- Upload images to S3
- Store brand metadata in PostgreSQL
- Generate brand ID and link to user

---

### 3.3 Chat Interface (AI Conversation)

#### 3.3.1 Layout
**Priority**: P0 (MVP)

**Requirements**:
- **Header**:
  - Brand name and thumbnail (top-left)
  - Back button to Brands Dashboard
  - Current step indicator (e.g., "Step 1 of 3: Gathering Details")
- **Main Area**: Chat messages
  - Scrollable message list
  - Messages styled with glassmorphism
  - User messages: Right-aligned, white background with opacity
  - Assistant messages: Left-aligned, yellow tint with opacity
  - Typing indicator while AI is responding
- **Input Area** (bottom):
  - Text input with glassmorphism
  - Send button (yellow, lucide-react send icon)
  - Character counter (optional)

**Initial Message**:
```
Hi! I'm excited to help you create an amazing ad for [Brand Name].
To get started, could you tell me a bit about what you want to achieve with this ad?
```

#### 3.3.2 Conversational Flow
**Priority**: P0 (MVP)

**AI Behavior**:
- Use OpenAI GPT-4 for conversation
- Ask exactly 5 follow-up questions to gather details
- Questions should cover:
  1. Target audience (demographics, interests)
  2. Ad platform and format (Instagram Story, Facebook Feed, TikTok, YouTube, etc.)
  3. Ad duration preference (15s, 30s, 60s)
  4. Key message or unique selling proposition
  5. Desired call-to-action

**System Prompt** (Master Prompt):
```
You are an expert ad strategist helping users create video advertisements.
You have access to their brand information: {brand.title}, {brand.description},
and {brand.productImages.length} product images.

Your goal is to ask exactly 5 thoughtful follow-up questions to gather the
information needed to create a compelling ad script. Ask about:
- Target audience
- Ad platform and format
- Ad duration
- Key message or USP
- Call-to-action

Be conversational, friendly, and concise. After 5 questions, confirm you have
all the information and transition to script generation.
```

**Transition to Script**:
- After 5 questions answered, AI says: "Perfect! I have everything I need. Let me create a storyline for your ad..."
- Navigate to Script Review page

---

### 3.4 Script Review & Approval

#### 3.4.1 Script Generation
**Priority**: P0 (MVP)

**Backend Process**:
1. Compile conversation context + brand info
2. Call OpenAI GPT-4 with prompt:
```
Based on the brand information and user requirements, create a detailed video ad script
with the following structure:

1. Overall storyline (2-3 sentences)
2. Scene-by-scene breakdown (3-5 scenes)
   - Scene number
   - Duration (in seconds)
   - Visual description (what's on screen)
   - Voiceover text (what's being said)
   - Visual prompt for Sora (detailed description for video generation)

The total duration should be {adDuration} seconds.
Output in structured JSON format.
```

3. Parse GPT-4 response into structured `Script` object
4. Store in database linked to AdProject

#### 3.4.2 Script Review UI
**Priority**: P0 (MVP)

**Requirements**:
- **Header**: Brand info + "Script Review" title
- **Storyline Section**:
  - Display overall storyline in large, readable text
  - Glassmorphism card
- **Scenes Section**:
  - Scrollable list of scene cards
  - Each scene shows:
    - Scene number badge
    - Duration badge
    - Visual description
    - Voiceover text (if any)
  - Accordion/expandable to show full Sora prompt
- **Actions** (bottom):
  - "Regenerate Script" button (secondary, requests new script)
  - "Approve & Generate Video" button (primary yellow)

**Interactions**:
- Click "Regenerate Script" → Call GPT-4 again with slightly modified prompt
- Click "Approve & Generate Video" → Start video generation process, navigate to generation status page

---

### 3.5 Video Generation Pipeline

#### 3.5.1 Video Generation Process
**Priority**: P0 (MVP)

**Backend Workflow**:
1. User approves script
2. Backend creates video generation job in Redis queue
3. Worker process picks up job:
   - For each scene:
     a. Call Replicate API with Sora model
        - Input: Scene visual prompt
        - Parameters: Duration, aspect ratio, quality settings
     b. Poll Replicate for job completion
     c. Download generated video from Replicate
     d. Upload to S3
     e. Store S3 URL in database
   - Generate audio (parallel or sequential):
     a. Call Suni API with audio prompt (if voiceover/music needed)
     b. Download audio files
     c. Upload to S3
   - Composite final video:
     a. Use FFmpeg to stitch scenes together
     b. Overlay audio tracks
     c. Add brand product images as overlays/inserts
     d. Apply transitions
     e. Export final video
     f. Upload to S3
4. Update AdProject status to 'completed'
5. Notify frontend (WebSocket or polling)

**Constraints**:
- Generated videos must incorporate the 2+ product images uploaded by user
- Videos should align with brand guidelines (colors, tone)
- Fallback: If Sora generation fails, use stock footage + product images

#### 3.5.2 Generation Status UI
**Priority**: P0 (MVP)

**Requirements**:
- Full-screen status page
- Animated loading indicator (yellow lightning bolt pulsing)
- Progress stages:
  1. "Generating visual scenes..." (0-40%)
  2. "Creating audio..." (40-60%)
  3. "Compositing final video..." (60-90%)
  4. "Finalizing..." (90-100%)
- Real-time progress bar
- Estimated time remaining (e.g., "About 2 minutes left")
- **On Completion**:
  - Success message: "Your ad is ready!"
  - "Open in Editor" button (primary yellow)
  - "Download Video" button (secondary)

**Error Handling**:
- If generation fails, show error message with retry option
- "Contact Support" link for persistent failures

---

### 3.6 Video Editor Integration

#### 3.6.1 Editor Launch
**Priority**: P0 (MVP)

**Requirements**:
- When user clicks "Open in Editor", load the existing Zapcut video editor
- Pre-populate editor with:
  - Generated video as a clip on the timeline
  - Audio tracks (if separate)
  - Product images as assets in the library
- User can now edit the video using full Zapcut capabilities:
  - Trim/split clips
  - Add transitions, effects
  - Adjust audio levels
  - Add text overlays
  - Export in various formats

**Technical Implementation**:
- Ingest generated video URL from S3 into Zapcut's asset system
- Use existing `addAssetsFromPaths` to load remote S3 URLs
- Automatically create clips on timeline
- Link AdProject to Zapcut ProjectState via `zapcutProjectId`

#### 3.6.2 Editor as Final Step
**Priority**: P0 (MVP)

**Concept**:
- The video editor is the **last screen** of the ad creation flow
- Users can make manual adjustments to AI-generated content
- Editor provides full creative control for refinement

**Navigation**:
- "Back to Brands" button in TopBar
- "Save & Export" workflow unchanged from current Zapcut

---

## 4. Design System

### 4.1 Brand Identity

**Primary Colors**:
- **Lightning Yellow**: `#FFEB3B` (primary CTA, accents)
- **Cursor White**: `#FFFFFF` (text, icons, overlays)
- **Cosmic Dark**: `#0A0E27` (backgrounds)
- **Mid Navy**: `#1A2332` (secondary backgrounds)
- **Light Blue**: `#4FC3F7` (interactive elements, highlights)

**Typography**:
- System font stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial`
- Headings: Bold, larger sizes
- Body: Regular weight, 14-16px

**Icons**:
- Use **Lucide React** icons exclusively
- Consistent sizing: 16px (small), 20px (medium), 24px (large)

### 4.2 Glassmorphism Guidelines

**Card Styling**:
```css
.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}
```

**Input Styling**:
```css
.glass-input {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  color: #FFFFFF;
}

.glass-input:focus {
  border-color: #FFEB3B;
  outline: none;
  box-shadow: 0 0 0 2px rgba(255, 235, 59, 0.2);
}
```

**Button Styling**:
```css
/* Primary CTA */
.btn-primary {
  background: linear-gradient(135deg, #FFEB3B 0%, #FFC107 100%);
  color: #0A0E27;
  font-weight: 600;
  border-radius: 8px;
  padding: 12px 24px;
  box-shadow: 0 4px 16px rgba(255, 235, 59, 0.3);
}

/* Secondary */
.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(8px);
  color: #FFFFFF;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 12px 24px;
}
```

### 4.3 Component Library

**Reusable Components to Build**:
1. `GlassCard` - Base glassmorphism container
2. `GlassInput` - Text input with glass styling
3. `GlassButton` - Primary and secondary button variants
4. `BrandCard` - Brand thumbnail + info card
5. `ChatMessage` - Message bubble with glass effect
6. `SceneCard` - Script scene display card
7. `ProgressIndicator` - Animated progress with stages
8. `FileUploader` - Drag-and-drop image uploader

---

## 5. User Flows

### 5.1 First-Time User Flow

```
Landing Page
    ↓ (Click "Login")
Login/Sign Up
    ↓ (Authenticate)
Brands Dashboard (Empty State)
    ↓ (Click "Create Brand")
Brand Creation Modal
    ↓ (Fill title, description, upload 2+ images)
Brands Dashboard (Shows new brand)
    ↓ (Click on brand card)
Chat Interface
    ↓ (Answer 5 AI questions)
Script Review
    ↓ (Approve script)
Video Generation (Loading)
    ↓ (Wait for completion)
Video Editor (Zapcut)
    ↓ (Edit and export)
Done
```

### 5.2 Returning User Flow

```
Login
    ↓
Brands Dashboard (Existing brands shown)
    ↓ (Option 1: Create new brand)
    └─→ Brand Creation Modal → ...
    ↓ (Option 2: Click existing brand)
Chat Interface (New conversation for existing brand)
    ↓
Script Review
    ↓
Video Generation
    ↓
Video Editor
```

---

## 6. API Endpoints

### 6.1 Authentication
- `POST /api/auth/signup` - Create account
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `POST /api/auth/reset-password` - Request password reset
- `GET /api/auth/me` - Get current user

### 6.2 Brands
- `GET /api/brands` - List user's brands
- `POST /api/brands` - Create new brand
- `GET /api/brands/:brandId` - Get brand details
- `PUT /api/brands/:brandId` - Update brand
- `DELETE /api/brands/:brandId` - Delete brand

### 6.3 Ad Projects
- `GET /api/brands/:brandId/projects` - List projects for brand
- `POST /api/brands/:brandId/projects` - Create new ad project
- `GET /api/projects/:projectId` - Get project details
- `PUT /api/projects/:projectId` - Update project
- `DELETE /api/projects/:projectId` - Delete project

### 6.4 Chat
- `POST /api/projects/:projectId/chat` - Send message, get AI response
- `GET /api/projects/:projectId/chat/history` - Get conversation history

### 6.5 Script
- `POST /api/projects/:projectId/script/generate` - Generate script from conversation
- `GET /api/projects/:projectId/script` - Get current script
- `POST /api/projects/:projectId/script/regenerate` - Regenerate script

### 6.6 Video Generation
- `POST /api/projects/:projectId/generate-video` - Start video generation
- `GET /api/projects/:projectId/generation-status` - Get generation status (polling)
- `WS /api/projects/:projectId/generation-updates` - WebSocket for real-time updates

### 6.7 Assets
- `POST /api/upload` - Upload files (images, videos)
- `GET /api/assets/:assetId` - Get asset URL (signed S3 URL)

---

## 7. Non-Functional Requirements

### 7.1 Performance
- **Page Load**: All pages should load within 2 seconds
- **Video Generation**: Complete within 5 minutes for 30-second ad
- **API Response Time**: < 500ms for CRUD operations
- **Chat Latency**: AI responses within 3 seconds (streaming preferred)

### 7.2 Security
- **Authentication**: Secure JWT or session-based auth
- **File Uploads**: Validate file types and sizes on backend
- **API Rate Limiting**: Prevent abuse (e.g., 100 requests/minute per user)
- **S3 Access**: Use signed URLs with expiration for media assets
- **Secrets Management**: Store API keys in environment variables or secret manager

### 7.3 Scalability
- **Horizontal Scaling**: Backend API should scale horizontally
- **Queue Processing**: Video generation workers should scale based on queue depth
- **Database**: Use connection pooling, indexes on frequent queries
- **CDN**: Serve static assets and media through CDN

### 7.4 Reliability
- **Uptime**: 99.9% uptime SLA
- **Error Handling**: Graceful degradation, user-friendly error messages
- **Retry Logic**: Automatic retries for transient failures (API calls, video generation)
- **Data Backup**: Daily backups of database

### 7.5 Monitoring & Logging
- **Application Monitoring**: Track errors, performance metrics (e.g., Sentry, Datadog)
- **Video Generation**: Log all generation jobs, track success/failure rates
- **User Analytics**: Track user flows, conversion rates (brand creation → video generation)

---

## 8. Dependencies & Integrations

### 8.1 External Services

| Service | Purpose | API Documentation |
|---------|---------|-------------------|
| OpenAI GPT-4 | Conversational AI, script generation | https://platform.openai.com/docs |
| OpenAI DALL-E 3 | Product imagery, b-roll generation | https://platform.openai.com/docs/guides/images |
| Replicate (Sora) | Text-to-video generation | https://replicate.com/sora |
| Suni | Audio/voiceover generation | (TBD - confirm API availability) |
| AWS S3 | Media storage | https://aws.amazon.com/s3/ |
| Redis | Job queue, caching | https://redis.io/docs/ |
| PostgreSQL | Primary database | https://www.postgresql.org/docs/ |

### 8.2 Development Dependencies
- **Frontend**: React, TypeScript, TailwindCSS, Zustand, Lucide React, Electron
- **Backend**: Node.js/Express (or Python/FastAPI), Bull, Prisma (or TypeORM)
- **DevOps**: Docker, GitHub Actions (CI/CD), AWS (hosting)

---

## 9. Development Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Set up backend API server (Node.js/Express)
- [ ] Database schema and migrations (PostgreSQL)
- [ ] Authentication system (sign up, login, session management)
- [ ] S3 integration for file uploads
- [ ] Landing page UI
- [ ] Login/signup UI

### Phase 2: Brand Management (Week 3)
- [ ] Brands Dashboard UI (glassmorphism design)
- [ ] Brand creation modal with image upload
- [ ] Backend: Brand CRUD APIs
- [ ] Brand card component with empty state

### Phase 3: Chat Interface (Week 4)
- [ ] Chat UI with glassmorphism styling
- [ ] OpenAI GPT-4 integration
- [ ] Conversation flow (5 follow-up questions)
- [ ] Backend: Chat API, conversation storage
- [ ] WebSocket for real-time chat (optional enhancement)

### Phase 4: Script Generation (Week 5)
- [ ] Script generation logic (GPT-4 prompt engineering)
- [ ] Script review UI (storyline + scenes)
- [ ] Backend: Script storage, regeneration API
- [ ] Scene card component

### Phase 5: Video Generation Pipeline (Week 6-8)
- [ ] Redis queue setup
- [ ] Video generation worker
- [ ] Replicate (Sora) API integration
- [ ] Suni audio API integration (or placeholder)
- [ ] FFmpeg video composition
- [ ] Generation status UI with progress tracking
- [ ] Backend: Generation status API, WebSocket updates

### Phase 6: Editor Integration (Week 9)
- [ ] Load generated video into Zapcut editor
- [ ] Pre-populate assets and timeline
- [ ] Link AdProject to Zapcut ProjectState
- [ ] Navigation between ad creation and editor

### Phase 7: Polish & Testing (Week 10-11)
- [ ] End-to-end testing
- [ ] Error handling and edge cases
- [ ] Performance optimization
- [ ] UI/UX refinements
- [ ] Documentation

### Phase 8: Launch Prep (Week 12)
- [ ] Production deployment (AWS)
- [ ] Monitoring and logging setup
- [ ] Beta testing with select users
- [ ] Bug fixes and feedback implementation
- [ ] Public launch

---

## 10. Open Questions & Future Enhancements

### 10.1 Open Questions
1. **Suni API Availability**: Is Suni publicly available? If not, what's the alternative for audio generation? (ElevenLabs, Descript, or stock music)
2. **LoRA Fine-tuning**: When and how will brand-specific LoRA models be trained? On first brand creation? After N videos?
3. **Pricing Model**: Free tier? Credit system? Subscription tiers?
4. **Video Length Limits**: What's the maximum ad duration? (30s for MVP, expand later?)
5. **Multi-language Support**: Should the first version support multiple languages for voiceover?

### 10.2 Future Enhancements (Post-MVP)
- **Templates**: Pre-built ad templates for common use cases (product launch, seasonal sale, etc.)
- **A/B Testing**: Generate multiple versions of ads for testing
- **Analytics Dashboard**: Track ad performance metrics (if integrated with platforms)
- **Collaboration**: Multi-user access to brands and projects
- **Advanced Editing**: More AI-powered editing features in Zapcut (auto-captions, smart cuts)
- **Mobile App**: iOS/Android app for on-the-go ad creation
- **White-label**: Allow agencies to white-label the platform
- **API Access**: Public API for developers to integrate ad generation

---

## 11. Success Criteria

### 11.1 Launch Criteria
- [ ] User can sign up and create a brand
- [ ] User can complete chat flow and receive a script
- [ ] Video generation completes successfully > 95% of the time
- [ ] Generated video includes user's product images
- [ ] User can open video in editor and make edits
- [ ] User can export final video
- [ ] No critical bugs in production

### 11.2 Post-Launch Metrics (First 30 Days)
- **Activation**: 50+ users create their first brand
- **Engagement**: 30+ users complete full flow (brand → video generation)
- **Quality**: Average script approval rate > 70%
- **Performance**: Video generation avg time < 5 minutes
- **Retention**: 50% of users return to create a second ad

---

## Appendix A: Glossary

- **Brand**: A user-created entity representing their business/product, containing images and guidelines
- **Ad Project**: A single ad creation workflow linked to a brand
- **Script**: AI-generated storyline and scene breakdown for an ad
- **Scene**: Individual segment of the ad with visual and audio descriptions
- **Sora**: OpenAI's text-to-video generation model (accessed via Replicate)
- **Suni**: Audio generation service for voiceovers and music
- **LoRA**: Low-Rank Adaptation, fine-tuning technique for customizing AI models
- **Zapcut**: The existing video editor application being extended
- **Glassmorphism**: UI design trend using frosted glass effect with transparency

---

## Appendix B: Reference Screenshots

The following screenshots provided inspiration for the UI/UX design:

1. **Brand Guidelines Upload** (`Screenshot 2025-11-14 at 7.22.02 PM.png`)
   - Inspiration for brand creation flow

2. **Brand List** (`Screenshot 2025-11-14 at 7.21.40 PM.png`, `Screenshot 2025-11-14 at 7.12.52 PM.png`)
   - Reference for brands dashboard layout

3. **Ad Campaign Dashboard** (`Screenshot 2025-11-14 at 7.21.24 PM.png`)
   - Inspiration for project/campaign organization (similar to Adobe GenStudio)

4. **Creative Format Selection** (`Screenshot 2025-11-14 at 7.14.02 PM.png`)
   - Reference for ad format/size selection (potential future feature)

5. **Video Editor UI** (`image (3).png`, `image (4).png`, `image (5).png`)
   - Captions.ai interface showing video editing with AI features

6. **Onboarding/Input Flow** (`image (1).png`, `image (2).png`)
   - Reference for conversational input gathering and user details

---

**Document Version**: 1.0
**Last Updated**: 2025-11-14
**Author**: Product Team
**Status**: Draft for Review
