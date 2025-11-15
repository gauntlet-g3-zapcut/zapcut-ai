# Zapcut AI: Technical Architecture

## System Overview

Zapcut is a **multi-agent AI video generation pipeline** that orchestrates multiple AI services (Claude, Sora, Suno, DALL-E) to produce professional-quality video advertisements from natural language prompts.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (Electron + React)                 │
│  - Single-page chat interface                                    │
│  - Real-time progress tracking                                   │
│  - Video preview & download                                      │
└────────────────────┬────────────────────────────────────────────┘
                     │ HTTPS (JWT Auth)
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                          │
│  - REST endpoints                                                │
│  - Authentication (AWS Cognito)                                  │
│  - Request validation                                            │
│  - WebSocket for progress                                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│PostgreSQL│  │  Redis   │  │   SQS    │
│   RDS    │  │  Cache   │  │  Queue   │
└──────────┘  └──────────┘  └──────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              Worker Tier (Celery Workers)                        │
│  - Video generation orchestration                                │
│  - Multi-agent coordination                                      │
│  - API polling & retries                                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬────────────┐
        ▼            ▼            ▼            ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  Claude  │  │   Sora   │  │   Suno   │  │  DALL-E  │
│Anthropic │  │Replicate │  │Replicate │  │  OpenAI  │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
                     │
                     ▼
              ┌──────────┐
              │    S3    │
              │ Storage  │
              └──────────┘
```

---

## Technology Stack

### Frontend
- **Framework**: Electron (cross-platform desktop app)
- **UI Library**: React 18 with TypeScript
- **State Management**: Zustand (global state)
- **Styling**: Tailwind CSS + Shadcn UI components
- **Icons**: Lucide React
- **Build Tool**: Vite
- **Video Player**: HTML5 `<video>` with custom controls

### Backend API
- **Framework**: FastAPI (Python 3.11+)
- **Authentication**: AWS Cognito (JWT)
- **Validation**: Pydantic v2
- **WebSocket**: FastAPI WebSocket for real-time progress
- **CORS**: Allow `https://app.zapcut.video` origin

### Task Queue
- **Queue**: Celery 5+ with Redis broker
- **Workers**: Python async workers
- **Scheduling**: Celery Beat (future: scheduled jobs)

### Database
- **Primary**: PostgreSQL 16 (AWS RDS)
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Schema**: See Database Schema section

### Infrastructure (AWS)
- **Compute**: Elastic Beanstalk (API servers)
- **Database**: RDS PostgreSQL
- **Queue**: SQS + Celery workers on EC2
- **Storage**: S3 (videos, images, audio)
- **CDN**: CloudFront (S3 content delivery)
- **Auth**: Cognito User Pools
- **Monitoring**: CloudWatch, Datadog

### AI Services
- **Orchestration**: Claude 3.5 Sonnet (Anthropic)
- **Video Generation**: Sora (via Replicate)
- **Music Generation**: Suno (via Replicate)
- **Image Generation**: DALL-E 3 (OpenAI)

### Video Processing
- **Composition**: FFmpeg (stitch scenes, add audio)
- **Encoding**: H.264 codec, 1080p, 30fps
- **Format**: MP4 (H.264 + AAC audio)

---

## Application Architecture

### Directory Structure

```
zapcut-ai/
├── app/                      # Electron frontend
│   ├── electron/            # Electron main process
│   │   ├── main.ts          # App entry point
│   │   ├── preload.ts       # IPC bridge
│   │   ├── ingest.ts        # Media ingestion
│   │   ├── export.ts        # Video export
│   │   └── ffmpeg.ts        # FFmpeg utilities
│   ├── src/                 # React frontend
│   │   ├── components/      # UI components
│   │   ├── store/           # Zustand stores
│   │   ├── lib/             # Utilities
│   │   └── types/           # TypeScript types
│   └── dist-electron/       # Compiled Electron code
│
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── main.py          # FastAPI app entry
│   │   ├── api/             # API routes
│   │   │   ├── auth.py      # Authentication
│   │   │   ├── projects.py  # Project CRUD
│   │   │   ├── generate.py  # Video generation
│   │   │   └── export.py    # Social media export
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── agents/          # Multi-agent system
│   │   │   ├── orchestrator.py
│   │   │   ├── story_agent.py
│   │   │   ├── style_agent.py
│   │   │   ├── prompt_agent.py
│   │   │   ├── safety_agent.py
│   │   │   └── continuity_agent.py
│   │   ├── services/        # Business logic
│   │   │   ├── sora.py      # Sora API client
│   │   │   ├── suno.py      # Suno API client
│   │   │   ├── dalle.py     # DALL-E API client
│   │   │   ├── claude.py    # Claude API client
│   │   │   └── ffmpeg.py    # Video composition
│   │   ├── workers/         # Celery workers
│   │   │   └── video_gen.py # Video generation task
│   │   └── utils/           # Helpers
│   ├── tests/               # Unit & integration tests
│   ├── alembic/             # DB migrations
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Container image
│
├── database/                 # Database management
│   ├── migrations/          # Alembic migration scripts
│   └── seeds/               # Seed data for dev
│
├── infrastructure/           # Terraform IaC
│   ├── main.tf              # AWS resources
│   ├── cognito.tf           # User authentication
│   ├── rds.tf               # PostgreSQL database
│   ├── s3.tf                # Storage buckets
│   ├── elasticbeanstalk.tf  # API servers
│   └── variables.tf         # Configuration
│
├── queue/                    # Celery configuration
│   ├── celeryconfig.py      # Celery settings
│   └── worker.py            # Worker entry point
│
├── s3/                       # S3 bucket structure
│   └── bucket-policy.json   # Access policies
│
└── docs/                     # Documentation
    ├── PRD/                 # Product requirements
    └── Architecture.md      # This file
```

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  cognito_user_id VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Profile
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  company_name VARCHAR(200),
  
  -- Subscription (future)
  subscription_tier VARCHAR(50) DEFAULT 'free',  -- free, pro, agency, enterprise
  videos_remaining INTEGER DEFAULT 3,
  
  -- Stats
  total_videos_generated INTEGER DEFAULT 0,
  total_spend_cents INTEGER DEFAULT 0,
  
  -- Social connections
  twitter_access_token TEXT,
  twitter_refresh_token TEXT,
  linkedin_access_token TEXT,
  linkedin_refresh_token TEXT,
  
  CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_cognito_id ON users(cognito_user_id);
```

---

### Projects Table
```sql
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- Basic info
  name VARCHAR(200) NOT NULL,
  description TEXT,
  
  -- Product info
  product_name VARCHAR(200),
  product_description TEXT,
  target_audience TEXT,
  brand_benefit TEXT,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT name_not_empty CHECK (LENGTH(TRIM(name)) > 0)
);

CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_projects_created_at ON projects(created_at DESC);
```

---

### Assets Table
```sql
CREATE TABLE assets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  
  -- Asset info
  type VARCHAR(50) NOT NULL,  -- 'image', 'video', 'audio', 'logo'
  source VARCHAR(50) NOT NULL,  -- 'upload', 'generated', 'dalle', 'sora', 'suno'
  url TEXT NOT NULL,
  s3_key VARCHAR(500) NOT NULL,
  
  -- Metadata
  label VARCHAR(100),  -- 'hero_product', 'lifestyle', 'detail', 'logo'
  role VARCHAR(100),   -- 'primary_product', 'background', 'logo', 'reference'
  file_size_bytes BIGINT,
  mime_type VARCHAR(100),
  width INTEGER,
  height INTEGER,
  duration_seconds DECIMAL(10, 2),
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT valid_type CHECK (type IN ('image', 'video', 'audio', 'logo')),
  CONSTRAINT valid_source CHECK (source IN ('upload', 'generated', 'dalle', 'sora', 'suno'))
);

CREATE INDEX idx_assets_project_id ON assets(project_id);
CREATE INDEX idx_assets_type ON assets(type);
```

---

### Creative Bibles Table
```sql
CREATE TABLE creative_bibles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  
  -- Identification
  name VARCHAR(200) NOT NULL,  -- e.g., "modern_minimalist_v1", "energetic_dynamic_v2"
  
  -- Style parameters (JSONB)
  creative_bible JSONB NOT NULL,
  /*
  {
    "brand_style": "minimalist",
    "vibe": "sophisticated",
    "colors": ["#2c2c2c", "#ffffff", "#8b6f47"],
    "lighting": "soft, warm, studio",
    "camera": "smooth, deliberate movements",
    "motion": "slow, refined",
    "energy_level": "medium"
  }
  */
  
  -- Reference images (JSONB)
  reference_image_urls JSONB NOT NULL,
  /*
  {
    "hero": "https://s3.../hero.png",
    "detail": "https://s3.../detail.png",
    "lifestyle": "https://s3.../lifestyle.png",
    "alternate": "https://s3.../alternate.png"
  }
  */
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  UNIQUE(project_id, name)
);

CREATE INDEX idx_creative_bibles_project_id ON creative_bibles(project_id);
```

---

### Generated Ads Table
```sql
CREATE TABLE generated_ads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  creative_bible_id UUID NOT NULL REFERENCES creative_bibles(id) ON DELETE RESTRICT,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- Generation plan
  storyboard JSONB NOT NULL,  -- 5-scene breakdown
  sora_prompts JSONB NOT NULL,  -- Array of prompts for each scene
  suno_prompt TEXT NOT NULL,  -- Single music prompt
  
  -- Generated assets
  video_urls JSONB,  -- {"scene_1": "s3://...", "scene_2": "s3://...", ...}
  music_url VARCHAR(500),
  final_video_url VARCHAR(500) NOT NULL,
  thumbnail_url VARCHAR(500),
  
  -- Metadata
  duration_seconds DECIMAL(10, 2),
  aspect_ratio VARCHAR(10),  -- "16:9", "9:16", "1:1"
  resolution VARCHAR(20),  -- "1920x1080"
  file_size_bytes BIGINT,
  
  -- Generation stats
  generation_started_at TIMESTAMP WITH TIME ZONE,
  generation_completed_at TIMESTAMP WITH TIME ZONE,
  generation_duration_seconds INTEGER,
  
  -- Cost tracking
  api_cost_cents INTEGER,  -- Total API cost in cents
  cost_breakdown JSONB,
  /*
  {
    "claude": 15,
    "dalle": 40,
    "sora": 150,
    "suno": 25,
    "infrastructure": 20
  }
  */
  
  -- Status
  status VARCHAR(50) NOT NULL DEFAULT 'queued',  -- queued, generating, completed, failed
  error_message TEXT,
  retry_count INTEGER DEFAULT 0,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT valid_status CHECK (status IN ('queued', 'generating', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX idx_generated_ads_project_id ON generated_ads(project_id);
CREATE INDEX idx_generated_ads_user_id ON generated_ads(user_id);
CREATE INDEX idx_generated_ads_status ON generated_ads(status);
CREATE INDEX idx_generated_ads_created_at ON generated_ads(created_at DESC);
```

---

### Generation Jobs Table (Queue State)
```sql
CREATE TABLE generation_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ad_id UUID NOT NULL REFERENCES generated_ads(id) ON DELETE CASCADE,
  
  -- Celery task info
  celery_task_id VARCHAR(255) UNIQUE NOT NULL,
  
  -- Progress tracking
  current_stage VARCHAR(100),  -- 'creative_bible', 'reference_images', 'scene_1', 'music', 'composition'
  progress_percentage INTEGER DEFAULT 0,
  estimated_remaining_seconds INTEGER,
  
  -- Stage completion
  stages_completed JSONB DEFAULT '[]'::JSONB,
  /*
  [
    {"stage": "creative_bible", "completed_at": "2025-11-15T10:30:00Z"},
    {"stage": "reference_images", "completed_at": "2025-11-15T10:31:00Z"},
    ...
  ]
  */
  
  -- Status
  status VARCHAR(50) NOT NULL DEFAULT 'queued',
  error_message TEXT,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT valid_progress CHECK (progress_percentage BETWEEN 0 AND 100),
  CONSTRAINT valid_status CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX idx_generation_jobs_ad_id ON generation_jobs(ad_id);
CREATE INDEX idx_generation_jobs_celery_task_id ON generation_jobs(celery_task_id);
CREATE INDEX idx_generation_jobs_status ON generation_jobs(status);
```

---

### Safety Violations Table
```sql
CREATE TABLE safety_violations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
  
  -- Violation details
  violation_category VARCHAR(100) NOT NULL,  -- 'violence', 'nudity', 'drugs', 'hate', 'copyright', etc.
  severity VARCHAR(20) NOT NULL,  -- 'low', 'medium', 'high', 'critical'
  
  -- Context
  user_input TEXT,  -- The unsafe prompt/request
  safe_alternative TEXT,  -- Suggested safe alternative
  blocked BOOLEAN DEFAULT true,  -- Was generation blocked?
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT valid_severity CHECK (severity IN ('low', 'medium', 'high', 'critical'))
);

CREATE INDEX idx_safety_violations_user_id ON safety_violations(user_id);
CREATE INDEX idx_safety_violations_category ON safety_violations(violation_category);
CREATE INDEX idx_safety_violations_created_at ON safety_violations(created_at DESC);
```

---

## API Endpoints

### Base URL
- **Production**: `https://api.zapcut.video/v1`
- **Staging**: `https://staging-api.zapcut.video/v1`
- **Local**: `http://localhost:8000/v1`

### Authentication
All endpoints (except `/auth/login` and `/auth/signup`) require JWT token:

```
Authorization: Bearer <JWT_TOKEN>
```

---

### Authentication Endpoints

#### POST `/auth/signup`
**Description**: Create new user account  
**Auth**: None  
**Request**:
```json
{
  "email": "sarah@example.com",
  "password": "SecurePassword123!",
  "first_name": "Sarah",
  "last_name": "Chen",
  "company_name": "GlowUp Cosmetics"
}
```

**Response** (201):
```json
{
  "user_id": "uuid-123",
  "email": "sarah@example.com",
  "access_token": "eyJhbGciOiJSUzI1...",
  "refresh_token": "eyJhbGciOiJSUzI1...",
  "expires_in": 3600
}
```

---

#### POST `/auth/login`
**Description**: Sign in existing user  
**Auth**: None  
**Request**:
```json
{
  "email": "sarah@example.com",
  "password": "SecurePassword123!"
}
```

**Response** (200):
```json
{
  "user_id": "uuid-123",
  "email": "sarah@example.com",
  "access_token": "eyJhbGciOiJSUzI1...",
  "refresh_token": "eyJhbGciOiJSUzI1...",
  "expires_in": 3600
}
```

---

#### POST `/auth/refresh`
**Description**: Refresh expired access token  
**Auth**: Refresh token  
**Request**:
```json
{
  "refresh_token": "eyJhbGciOiJSUzI1..."
}
```

**Response** (200):
```json
{
  "access_token": "eyJhbGciOiJSUzI1...",
  "expires_in": 3600
}
```

---

### Project Endpoints

#### GET `/projects`
**Description**: List user's projects  
**Auth**: Required  
**Query Params**:
- `limit` (default: 20)
- `offset` (default: 0)

**Response** (200):
```json
{
  "projects": [
    {
      "id": "uuid-proj-1",
      "name": "Luna Coffee",
      "description": "Cold brew concentrate ads",
      "created_at": "2025-11-15T10:00:00Z",
      "total_ads": 5,
      "last_generated_at": "2025-11-16T14:30:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

#### POST `/projects`
**Description**: Create new project  
**Auth**: Required  
**Request**:
```json
{
  "name": "Luna Coffee",
  "description": "Organic cold brew concentrate ads",
  "product_name": "Luna Coffee Cold Brew",
  "product_description": "Smooth, organic cold brew concentrate...",
  "target_audience": "25-40 year olds, health-conscious professionals",
  "brand_benefit": "Calm energy, morning ritual, premium but approachable"
}
```

**Response** (201):
```json
{
  "id": "uuid-proj-1",
  "name": "Luna Coffee",
  "description": "Organic cold brew concentrate ads",
  "created_at": "2025-11-15T10:00:00Z"
}
```

---

#### GET `/projects/{project_id}`
**Description**: Get project details  
**Auth**: Required  
**Response** (200):
```json
{
  "id": "uuid-proj-1",
  "name": "Luna Coffee",
  "description": "Organic cold brew concentrate ads",
  "product_name": "Luna Coffee Cold Brew",
  "product_description": "Smooth, organic...",
  "assets": [
    {
      "id": "uuid-asset-1",
      "type": "image",
      "url": "https://cdn.zapcut.video/...",
      "label": "hero_product"
    }
  ],
  "creative_bibles": [
    {
      "id": "uuid-bible-1",
      "name": "modern_minimalist_v1",
      "created_at": "2025-11-15T10:15:00Z"
    }
  ],
  "total_ads": 5
}
```

---

### Asset Endpoints

#### POST `/projects/{project_id}/assets/upload`
**Description**: Upload asset (image, video, audio)  
**Auth**: Required  
**Content-Type**: `multipart/form-data`  
**Request**:
```
file: [binary]
type: "image"
label: "hero_product"
role: "primary_product"
```

**Response** (201):
```json
{
  "id": "uuid-asset-1",
  "type": "image",
  "url": "https://cdn.zapcut.video/projects/uuid-proj-1/hero.png",
  "s3_key": "projects/uuid-proj-1/assets/hero.png",
  "file_size_bytes": 2048576,
  "mime_type": "image/png",
  "width": 1920,
  "height": 1080
}
```

---

### Video Generation Endpoints

#### POST `/generate/video`
**Description**: Generate video ad  
**Auth**: Required  
**Request**:
```json
{
  "project_id": "uuid-proj-1",
  "creative_direction": "Clean and modern, soft morning light, warm earth tones, calm and serene",
  "duration_seconds": 30,
  "aspect_ratio": "16:9",
  "scenes": [
    {
      "prompt": "Close-up of Luna Coffee bottle on kitchen counter, morning sunlight",
      "media": [
        {
          "asset_id": "uuid-asset-1",
          "role": "primary_product"
        }
      ]
    }
  ],
  "reuse_creative_bible_id": null  // or UUID to reuse existing Creative Bible
}
```

**Response** (202):
```json
{
  "job_id": "uuid-job-1",
  "ad_id": "uuid-ad-1",
  "status": "queued",
  "estimated_duration_seconds": 300
}
```

---

#### GET `/generate/video/job/{job_id}`
**Description**: Get generation job status  
**Auth**: Required  
**Response** (200):
```json
{
  "job_id": "uuid-job-1",
  "ad_id": "uuid-ad-1",
  "status": "generating",
  "current_stage": "scene_3",
  "progress_percentage": 60,
  "estimated_remaining_seconds": 120,
  "stages_completed": [
    {"stage": "creative_bible", "completed_at": "2025-11-15T10:16:00Z"},
    {"stage": "reference_images", "completed_at": "2025-11-15T10:17:00Z"},
    {"stage": "scene_1", "completed_at": "2025-11-15T10:18:30Z"},
    {"stage": "scene_2", "completed_at": "2025-11-15T10:19:45Z"}
  ],
  "created_at": "2025-11-15T10:15:00Z",
  "updated_at": "2025-11-15T10:19:50Z"
}
```

**When Completed** (200):
```json
{
  "job_id": "uuid-job-1",
  "ad_id": "uuid-ad-1",
  "status": "completed",
  "progress_percentage": 100,
  "video_url": "https://cdn.zapcut.video/ads/uuid-ad-1/final.mp4",
  "thumbnail_url": "https://cdn.zapcut.video/ads/uuid-ad-1/thumb.jpg",
  "duration_seconds": 30,
  "file_size_bytes": 45678900,
  "generation_duration_seconds": 285,
  "api_cost_cents": 250
}
```

---

#### GET `/ads/{ad_id}`
**Description**: Get generated ad details  
**Auth**: Required  
**Response** (200):
```json
{
  "id": "uuid-ad-1",
  "project_id": "uuid-proj-1",
  "creative_bible_id": "uuid-bible-1",
  "video_url": "https://cdn.zapcut.video/ads/uuid-ad-1/final.mp4",
  "thumbnail_url": "https://cdn.zapcut.video/ads/uuid-ad-1/thumb.jpg",
  "duration_seconds": 30,
  "aspect_ratio": "16:9",
  "resolution": "1920x1080",
  "file_size_bytes": 45678900,
  "storyboard": [
    {
      "scene_index": 1,
      "title": "Product Reveal",
      "description": "Close-up of Luna Coffee bottle...",
      "duration": 6
    }
  ],
  "generation_duration_seconds": 285,
  "api_cost_cents": 250,
  "created_at": "2025-11-15T10:15:00Z"
}
```

---

### Export Endpoints

#### POST `/export/twitter`
**Description**: Post video to X (Twitter)  
**Auth**: Required  
**Request**:
```json
{
  "ad_id": "uuid-ad-1",
  "caption": "Introducing Luna Coffee ☕️ - Your perfect morning ritual. #ColdBrew",
  "twitter_account_id": "optional-if-multiple-accounts"
}
```

**Response** (200):
```json
{
  "tweet_id": "1234567890",
  "tweet_url": "https://twitter.com/user/status/1234567890",
  "posted_at": "2025-11-15T10:30:00Z"
}
```

---

#### POST `/export/linkedin`
**Description**: Post video to LinkedIn  
**Auth**: Required  
**Request**:
```json
{
  "ad_id": "uuid-ad-1",
  "caption": "Introducing Luna Coffee - organic cold brew for busy professionals.",
  "visibility": "public"  // "public", "connections"
}
```

**Response** (200):
```json
{
  "post_id": "urn:li:share:1234567890",
  "post_url": "https://www.linkedin.com/feed/update/urn:li:share:1234567890",
  "posted_at": "2025-11-15T10:31:00Z"
}
```

---

## Multi-Agent System

### Agent Architecture

```
                    ┌──────────────────┐
                    │  Master          │
                    │  Orchestrator    │
                    │  Agent           │
                    └────────┬─────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
       ▼                     ▼                     ▼
┌────────────┐      ┌────────────┐      ┌────────────┐
│ Story      │      │ Style &    │      │ Safety     │
│ Structuring│──────│ Brand      │──────│ Validation │
│ Agent      │      │ Agent      │      │ Agent      │
└────────────┘      └────────────┘      └────────────┘
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             ▼
                    ┌────────────┐
                    │ Prompt     │
                    │ Synthesis  │
                    │ Agent      │
                    └────────────┘
                             │
                             ▼
                    ┌────────────┐
                    │ Continuity │
                    │ Back-Prop  │
                    │ Agent      │
                    └────────────┘
```

---

### Agent 1: Master Orchestrator

**Responsibility**: Guide user through workflow stages, enforce state transitions

**Stages**:
1. `collect_brand_info`
2. `collect_product_info`
3. `collect_assets`
4. `collect_scenes`
5. `final_review`
6. `generate_video`
7. `export_video`

**System Prompt**:
```
You are the Zapcut Orchestrator, the main OS for the app.

Your job:
- Maintain a stage-based workflow for creating AI-generated video ads
- Never skip forward if required info is missing
- Always respond in a chat style, like ChatGPT
- Control the following stages: [list]
- When ready to move to next stage, state: "NEXT_STAGE: <stage_name>"

If user asks for anything unsafe or inappropriate (NSFW, violence, hate, etc.),
refuse kindly and redirect them back to ad-building tasks.

Current Stage: {current_stage}
State: {state_json}
```

**State Object**:
```json
{
  "stage": "collect_scenes",
  "brand": {
    "name": "Luna Coffee",
    "product": "Cold brew concentrate"
  },
  "product": {
    "description": "Smooth, organic...",
    "target_audience": "25-40 professionals",
    "benefit": "Calm energy"
  },
  "assets": [
    {"id": "uuid-asset-1", "type": "image", "label": "hero_product"}
  ],
  "scenes": [],
  "safety_flags": []
}
```

---

### Agent 2: Story Structuring Agent

**Responsibility**: Normalize story outline, validate narrative progression

**Input**: Raw user brief + scenes  
**Output**: Structured storyboard with scene roles

**System Prompt**:
```
You are the Story Structuring Agent.

Analyze the user's brief and create a 5-scene storyboard for a 30-second ad.

Each scene must have:
- scene_index (1-5)
- scene_title
- description (2-3 sentences)
- duration_seconds (total must equal 30)
- role_in_story ('setup', 'exploration', 'conflict', 'resolution', 'cta')
- camera_direction
- emotion_tone
- key_story_events (array of 3-5 events)

Ensure logical narrative progression:
- Scene 1: Setup (introduce product/problem)
- Scenes 2-3: Exploration/Development
- Scene 4: Climax/Key benefit
- Scene 5: Resolution + CTA

Output JSON only.
```

**Example Output**:
```json
{
  "scenes": [
    {
      "scene_index": 1,
      "scene_title": "Morning Awakening",
      "description": "Close-up of Luna Coffee bottle on kitchen counter as morning sunlight streams through window. Warm, cozy interior.",
      "duration_seconds": 6,
      "role_in_story": "setup",
      "camera_direction": "Static shot with subtle push-in towards bottle",
      "emotion_tone": "calm, inviting",
      "key_story_events": [
        "Introduce Luna Coffee bottle",
        "Establish morning setting",
        "Soft lighting creates warmth"
      ]
    }
    // ... scenes 2-5
  ]
}
```

---

### Agent 3: Style & Brand Consistency Agent

**Responsibility**: Generate Creative Bible, enforce brand compliance

**Input**: User brief + product images + brand info  
**Output**: Creative Bible parameters

**System Prompt**:
```
You are the Style & Brand Consistency Agent.

Analyze the user's brand assets and creative direction to generate a Creative Bible.

Extract:
1. brand_style (e.g., "minimalist", "energetic", "premium")
2. vibe (e.g., "calm", "exciting", "sophisticated")
3. colors (array of 4-6 hex codes from product images)
4. lighting (e.g., "soft natural light", "dramatic studio lighting")
5. camera (e.g., "smooth slow motion", "dynamic handheld")
6. motion (e.g., "slow and deliberate", "fast and energetic")
7. energy_level (1-10 scale, where 5 is medium)

Brand constraints:
- Only use colors present in uploaded product images
- Match tone to user's stated brand benefit
- Ensure safety compliance (no prohibited elements)

Output JSON only.
```

**Example Output**:
```json
{
  "brand_style": "modern minimalist",
  "vibe": "calm and serene",
  "colors": ["#8B7355", "#F5E6D3", "#4A4A4A", "#FFFFFF"],
  "lighting": "soft natural morning light, warm tones",
  "camera": "smooth, slow dolly movements, stable shots",
  "motion": "slow, refined, no fast cuts",
  "energy_level": 4
}
```

---

### Agent 4: Safety Validation Agent

**Responsibility**: Scan for violations before generation

**Input**: Script + scene descriptions + prompts  
**Output**: Approval or block with alternatives

**System Prompt**:
```
You are the Safety Validation Agent for Zapcut.

Scan all scripts, scene descriptions, and prompts for:
1. Prohibited content (violence, nudity, drugs, hate, deepfakes, copyright)
2. Brand compliance violations
3. Legal/regulatory issues
4. Misleading claims

If ANY violation exists:
- Output "status": "blocked"
- List all violations with severity (low, medium, high, critical)
- Provide safe rewrite alternatives when possible

If content is safe:
- Output "status": "approved"
- Add comprehensive negative_prompt for generation

Never allow:
- Real people likenesses
- Copyrighted characters
- Competitor brands
- Unsafe behavior
- Misleading claims

Always enforce:
- Brand-safe content
- Synthetic humans only
- Royalty-free assets
```

**Example Output (Blocked)**:
```json
{
  "status": "blocked",
  "violations": [
    {
      "category": "violence",
      "severity": "high",
      "scene": 3,
      "description": "Scene contains weapon reference",
      "line": "Person holding gun while drinking coffee"
    }
  ],
  "safe_alternative": {
    "scene_3_rewritten": "Person confidently holding Luna Coffee bottle while at work desk, conveying empowerment without weapons"
  }
}
```

**Example Output (Approved)**:
```json
{
  "status": "approved",
  "negative_prompt": "realistic violence, gore, weapons, nudity, sexual content, drugs, smoking, alcohol, hate symbols, real people, copyrighted characters, trademarked brands, low quality",
  "timestamp": "2025-11-15T10:16:00Z"
}
```

---

### Agent 5: Prompt Synthesis Agent

**Responsibility**: Create optimal Sora prompts from scene descriptions

**Input**: Scene + Creative Bible + reference images + continuity info  
**Output**: Final Sora prompt with all parameters

**System Prompt**:
```
You are the Prompt Synthesis Agent.

For each scene, create a complete Sora prompt that includes:

1. Creative Bible style enforcement
2. Scene description from storyboard
3. Reference image URLs for style consistency
4. Continuity instructions (for scenes 2+)
5. Camera direction
6. Emotion tone
7. Safety constraints

Prompt structure:
"[Creative Bible style], [scene description], [camera direction], [continuity note if scene > 1], [emotion tone]"

Example:
"3D Pixar-like style, soft global illumination, cinematic depth of field. Close-up shot of Luna Coffee bottle on kitchen counter with morning sunlight streaming through window. Smooth slow push-in camera movement. Warm, inviting atmosphere. Product appearance must match reference image at [URL]. No text overlays, no logos, synthetic environment only."

Include these parameters:
- negative_prompt (from Safety Agent)
- duration (from storyboard)
- fps (30)
- resolution (1920x1080)
- aspect_ratio (16:9)
- seed (project_seed + scene_index for consistency)
- guidance_scale (7.0-8.0 for balance)
- style_strength (0.8-0.9 for consistency)
- motion_strength (based on Creative Bible energy_level)
- input_image_url (last frame of previous scene for scenes 2+)
- aux_seed_image_url (reference image from Creative Bible)

Output JSON only.
```

**Example Output**:
```json
{
  "scene_index": 2,
  "prompt": "Modern minimalist style, soft natural morning light, warm earth tones. Medium shot of hand pouring Luna Coffee concentrate into glass with ice. Smooth dolly camera movement following the pour. Product matches reference image. Calm, serene atmosphere. No text, no logos, synthetic hands only.",
  "negative_prompt": "violence, gore, weapons, nudity, drugs, smoking, real people, copyrighted characters, low quality, text overlay",
  "duration": 6,
  "fps": 30,
  "resolution": "1920x1080",
  "aspect_ratio": "16:9",
  "seed": 123457,
  "guidance_scale": 7.5,
  "style_strength": 0.85,
  "motion_strength": 0.6,
  "input_image_url": "https://cdn.zapcut.video/renders/scene1_lastframe.png",
  "aux_seed_image_url": "https://cdn.zapcut.video/creative_bibles/hero.png"
}
```

---

### Agent 6: Continuity Back-Propagation Agent

**Responsibility**: Maintain visual consistency across scenes

**Input**: Previous scene output + next scene prompt  
**Output**: Updated prompt with continuity instructions

**System Prompt**:
```
You are the Continuity Back-Propagation Agent.

For scene N > 1, analyze the last frame of scene N-1 and update the prompt for scene N to ensure:

1. Visual continuity (lighting, color palette, product appearance)
2. Logical narrative flow
3. Camera position continuity
4. Character/product consistency

Extract from previous scene:
- Last frame URL
- Color palette analysis
- Lighting conditions
- Product position/angle
- Camera position

Inject into next scene prompt:
"Continue from previous scene where [describe last frame]. Maintain [color palette], [lighting], [product appearance]. Product is now [new position/action]."

If style drift detected (colors/lighting changed unexpectedly), tighten the prompt:
- Increase style_strength to 0.9+
- Add explicit color references
- Reference specific product details

Output JSON with updated prompt.
```

**Example Output**:
```json
{
  "scene_index": 3,
  "updated_prompt": "Continue from previous scene where Luna Coffee was being poured into glass. Modern minimalist style, same soft morning light, warm earth tones (#8B7355, #F5E6D3). Now showing the finished drink with product visible in background. Smooth camera orbit around glass. Maintain product appearance from reference image. Calm, serene atmosphere.",
  "input_image_url": "https://cdn.zapcut.video/renders/scene2_lastframe.png",
  "continuity_notes": "Preserved color palette, lighting, and product design from scene 2",
  "style_strength_adjustment": 0.88
}
```

---

## Video Generation Pipeline

### Workflow Diagram

```
User Clicks "Generate Video"
          │
          ▼
┌─────────────────────┐
│ 1. API Request      │ → Validate, create job, enqueue
│    (FastAPI)        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. Celery Worker    │ → Picks up job from SQS
│    Starts Task      │
└──────────┬──────────┘
           │
           ├─────────────────────────────────────────┐
           │                                         │
           ▼                                         ▼
┌──────────────────────┐                  ┌──────────────────────┐
│ 3a. Creative Bible   │ ─────┐           │ 3b. Reference Images │
│     Generation       │      │           │     (DALL-E)         │
│     (Claude)         │      │           │                      │
│     30s              │      │           │     4 images, 45s    │
└──────────┬───────────┘      │           └──────────┬───────────┘
           │                  │                      │
           │                  ▼                      │
           │         ┌──────────────────────┐       │
           │         │ 4. Storyboard        │       │
           │         │    Generation        │       │
           │         │    (Claude)          │       │
           │         │    15s               │       │
           │         └──────────┬───────────┘       │
           │                    │                   │
           └────────────────────┼───────────────────┘
                                │
                                ▼
                       ┌──────────────────────┐
                       │ 5. Prompt Synthesis  │
                       │    (Claude)          │
                       │    5 Sora + 1 Suno   │
                       │    10s               │
                       └──────────┬───────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │                           │
                    ▼                           ▼
        ┌────────────────────┐      ┌────────────────────┐
        │ 6a. Video Scenes   │      │ 6b. Music Track    │
        │     (Sora)         │      │     (Suno)         │
        │     5 scenes       │      │     1 track        │
        │     Parallel       │      │                    │
        │     2-3 minutes    │      │     1-2 minutes    │
        └────────────┬───────┘      └────────┬───────────┘
                     │                       │
                     └───────────┬───────────┘
                                 ▼
                        ┌──────────────────────┐
                        │ 7. Video Composition │
                        │    (FFmpeg)          │
                        │    - Stitch 5 scenes │
                        │    - Add music       │
                        │    - Text overlays   │
                        │    - Encode H.264    │
                        │    45s               │
                        └──────────┬───────────┘
                                   │
                                   ▼
                          ┌──────────────────────┐
                          │ 8. Upload to S3      │
                          │    - Final video MP4 │
                          │    - Thumbnail JPG   │
                          │    10s               │
                          └──────────┬───────────┘
                                     │
                                     ▼
                            ┌──────────────────────┐
                            │ 9. Update Database   │
                            │    - Mark completed  │
                            │    - Store URLs      │
                            │    - Notify frontend │
                            └──────────────────────┘

Total Time: 4-5 minutes
```

---

### Celery Task Implementation

**File**: `backend/app/workers/video_gen.py`

```python
from celery import Task, shared_task
from app.agents import (
    orchestrator, story_agent, style_agent, 
    safety_agent, prompt_agent, continuity_agent
)
from app.services import sora, suno, dalle, ffmpeg
from app.models import GeneratedAd, GenerationJob
import asyncio

@shared_task(bind=True, max_retries=3)
def generate_video_task(self: Task, ad_id: str):
    """
    Main video generation task.
    Orchestrates multi-agent pipeline.
    """
    
    # 1. Load job and ad
    job = GenerationJob.get_by_ad_id(ad_id)
    ad = GeneratedAd.get(ad_id)
    
    try:
        # 2. Update job status
        job.update(status='running', current_stage='creative_bible')
        
        # 3. Creative Bible Generation (if new)
        if not ad.creative_bible_id:
            creative_bible = await style_agent.generate_creative_bible(
                project_id=ad.project_id,
                user_brief=ad.user_brief
            )
            ad.update(creative_bible_id=creative_bible.id)
            job.mark_stage_completed('creative_bible')
        
        # 4. Reference Image Generation (if new Creative Bible)
        if not creative_bible.reference_image_urls:
            job.update(current_stage='reference_images')
            ref_images = await dalle.generate_reference_images(
                creative_bible=creative_bible,
                product_images=ad.project.assets
            )
            creative_bible.update(reference_image_urls=ref_images)
            job.mark_stage_completed('reference_images')
        
        # 5. Storyboard Generation
        job.update(current_stage='storyboard')
        storyboard = await story_agent.generate_storyboard(
            user_brief=ad.user_brief,
            creative_bible=creative_bible,
            duration=ad.duration_seconds
        )
        ad.update(storyboard=storyboard)
        job.mark_stage_completed('storyboard')
        
        # 6. Safety Validation
        safety_check = await safety_agent.validate(
            storyboard=storyboard,
            creative_bible=creative_bible
        )
        if safety_check['status'] == 'blocked':
            job.update(status='failed', error_message=safety_check['message'])
            return
        
        # 7. Prompt Synthesis
        job.update(current_stage='prompt_synthesis')
        sora_prompts = []
        for scene in storyboard['scenes']:
            prompt = await prompt_agent.synthesize_prompt(
                scene=scene,
                creative_bible=creative_bible,
                reference_images=creative_bible.reference_image_urls,
                negative_prompt=safety_check['negative_prompt']
            )
            sora_prompts.append(prompt)
        
        suno_prompt = await prompt_agent.synthesize_music_prompt(
            storyboard=storyboard,
            creative_bible=creative_bible
        )
        
        ad.update(sora_prompts=sora_prompts, suno_prompt=suno_prompt)
        job.mark_stage_completed('prompt_synthesis')
        
        # 8. Parallel Video + Music Generation
        scene_urls = []
        for i, prompt in enumerate(sora_prompts, start=1):
            job.update(current_stage=f'scene_{i}', progress_percentage=40 + (i * 10))
            
            # For scene 2+, inject last frame of previous scene
            if i > 1:
                prev_scene_last_frame = await extract_last_frame(scene_urls[i-2])
                prompt = await continuity_agent.update_prompt(
                    prompt=prompt,
                    previous_frame=prev_scene_last_frame
                )
            
            # Generate scene
            scene_video_url = await sora.generate_video(prompt)
            scene_urls.append(scene_video_url)
            job.mark_stage_completed(f'scene_{i}')
        
        # Generate music (parallel with scenes 3-5)
        job.update(current_stage='music')
        music_url = await suno.generate_music(suno_prompt)
        job.mark_stage_completed('music')
        
        ad.update(video_urls={'scenes': scene_urls}, music_url=music_url)
        
        # 9. Video Composition
        job.update(current_stage='composition', progress_percentage=90)
        final_video_path = await ffmpeg.compose_video(
            scene_urls=scene_urls,
            music_url=music_url,
            storyboard=storyboard,
            product_name=ad.project.product_name
        )
        
        # 10. Upload to S3
        final_video_url = await upload_to_s3(final_video_path, ad_id)
        thumbnail_url = await generate_and_upload_thumbnail(final_video_path, ad_id)
        
        # 11. Update database
        ad.update(
            final_video_url=final_video_url,
            thumbnail_url=thumbnail_url,
            status='completed',
            generation_completed_at=datetime.utcnow()
        )
        job.update(status='completed', progress_percentage=100)
        
    except Exception as e:
        # Handle errors, retry logic
        job.update(status='failed', error_message=str(e))
        self.retry(countdown=60)  # Retry after 60s
```

---

## Infrastructure as Code (Terraform)

### AWS Resources

**File**: `infrastructure/main.tf`

```hcl
terraform {
  required_version = ">= 1.5"
  
  backend "s3" {
    bucket = "zapcut-terraform-state"
    key    = "production/terraform.tfstate"
    region = "us-east-1"
  }
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC & Networking
module "vpc" {
  source = "./modules/vpc"
  
  cidr_block = "10.0.0.0/16"
  name       = "zapcut-vpc"
}

# Cognito User Pool
resource "aws_cognito_user_pool" "zapcut_users" {
  name = "zapcut-user-pool"
  
  auto_verified_attributes = ["email"]
  
  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }
  
  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = false
  }
  
  schema {
    name                = "first_name"
    attribute_data_type = "String"
    mutable             = true
  }
  
  schema {
    name                = "last_name"
    attribute_data_type = "String"
    mutable             = true
  }
}

resource "aws_cognito_user_pool_client" "zapcut_app_client" {
  name         = "zapcut-app-client"
  user_pool_id = aws_cognito_user_pool.zapcut_users.id
  
  generate_secret = false
  
  allowed_oauth_flows       = ["code"]
  allowed_oauth_scopes      = ["email", "openid", "profile"]
  callback_urls             = ["https://app.zapcut.video"]
  logout_urls               = ["https://zapcut.video"]
  
  allowed_oauth_flows_user_pool_client = true
  supported_identity_providers         = ["COGNITO"]
}

# RDS PostgreSQL
resource "aws_db_instance" "zapcut_postgres" {
  identifier        = "zapcut-db"
  engine            = "postgres"
  engine_version    = "16.1"
  instance_class    = "db.t3.micro"  # MVP: upgrade to db.r6g.large for production
  allocated_storage = 20
  storage_type      = "gp3"
  
  db_name  = "zapcut"
  username = "zapcut_admin"
  password = var.db_password  # Store in AWS Secrets Manager
  
  db_subnet_group_name   = module.vpc.database_subnet_group
  vpc_security_group_ids = [aws_security_group.database.id]
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"
  
  publicly_accessible = false
  skip_final_snapshot = false
  final_snapshot_identifier = "zapcut-db-final-snapshot"
  
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  
  tags = {
    Name        = "zapcut-db"
    Environment = "production"
  }
}

# S3 Buckets
resource "aws_s3_bucket" "zapcut_assets" {
  bucket = "zapcut-assets-${var.environment}"
  
  tags = {
    Name        = "zapcut-assets"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "zapcut_assets_versioning" {
  bucket = aws_s3_bucket.zapcut_assets.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "zapcut_assets_encryption" {
  bucket = aws_s3_bucket.zapcut_assets.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "zapcut_assets_cors" {
  bucket = aws_s3_bucket.zapcut_assets.id
  
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["https://app.zapcut.video"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# CloudFront CDN
resource "aws_cloudfront_distribution" "zapcut_cdn" {
  origin {
    domain_name = aws_s3_bucket.zapcut_assets.bucket_regional_domain_name
    origin_id   = "S3-zapcut-assets"
  }
  
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  
  aliases = ["cdn.zapcut.video"]
  
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-zapcut-assets"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  viewer_certificate {
    acm_certificate_arn = var.acm_certificate_arn
    ssl_support_method  = "sni-only"
  }
}

# SQS Queue for Video Jobs
resource "aws_sqs_queue" "video_jobs" {
  name                      = "zapcut-video-jobs"
  delay_seconds             = 0
  max_message_size          = 262144  # 256 KB
  message_retention_seconds = 86400   # 24 hours
  visibility_timeout_seconds = 900    # 15 minutes
  
  tags = {
    Name        = "zapcut-video-jobs"
    Environment = var.environment
  }
}

# Elastic Beanstalk Application
resource "aws_elastic_beanstalk_application" "zapcut_api" {
  name        = "zapcut-api"
  description = "Zapcut FastAPI backend"
}

resource "aws_elastic_beanstalk_environment" "zapcut_api_env" {
  name                = "zapcut-api-${var.environment}"
  application         = aws_elastic_beanstalk_application.zapcut_api.name
  solution_stack_name = "64bit Amazon Linux 2 v3.5.7 running Docker"
  
  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "InstanceType"
    value     = "t3.medium"  # MVP: upgrade to c6i.xlarge for production
  }
  
  setting {
    namespace = "aws:autoscaling:asg"
    name      = "MinSize"
    value     = "2"
  }
  
  setting {
    namespace = "aws:autoscaling:asg"
    name      = "MaxSize"
    value     = "10"
  }
  
  setting {
    namespace = "aws:elasticbeanstalk:environment"
    name      = "EnvironmentType"
    value     = "LoadBalanced"
  }
  
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "DATABASE_URL"
    value     = "postgresql://${aws_db_instance.zapcut_postgres.username}:${var.db_password}@${aws_db_instance.zapcut_postgres.address}:5432/zapcut"
  }
  
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "COGNITO_USER_POOL_ID"
    value     = aws_cognito_user_pool.zapcut_users.id
  }
  
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "SQS_QUEUE_URL"
    value     = aws_sqs_queue.video_jobs.id
  }
  
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "S3_BUCKET"
    value     = aws_s3_bucket.zapcut_assets.id
  }
}

# Outputs
output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.zapcut_users.id
}

output "cognito_client_id" {
  value = aws_cognito_user_pool_client.zapcut_app_client.id
}

output "database_endpoint" {
  value     = aws_db_instance.zapcut_postgres.address
  sensitive = true
}

output "s3_bucket_name" {
  value = aws_s3_bucket.zapcut_assets.id
}

output "cdn_domain" {
  value = aws_cloudfront_distribution.zapcut_cdn.domain_name
}
```

---

## Deployment Strategy

### Environments
1. **Local**: Developer machines
2. **Staging**: Pre-production testing
3. **Production**: Live environment

### CI/CD Pipeline (GitHub Actions)

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Elastic Beanstalk
        uses: einaregilsson/beanstalk-deploy@v21
        with:
          aws_access_key: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws_secret_key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          application_name: zapcut-api
          environment_name: zapcut-api-production
          version_label: ${{ github.sha }}
          region: us-east-1
          deployment_package: backend.zip

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Electron app
        run: |
          cd app
          npm install
          npm run electron:build
      - name: Upload to S3
        run: |
          aws s3 sync app/dist s3://zapcut-releases/
```

---

## Security Considerations

### Authentication
- AWS Cognito JWT tokens (1-hour expiration)
- Refresh tokens stored securely
- HTTPS only (TLS 1.3)

### API Security
- Rate limiting: 100 requests/minute per user
- CORS: Whitelist `https://app.zapcut.video` only
- Input validation: Pydantic schemas
- SQL injection prevention: SQLAlchemy ORM

### Data Protection
- Database encryption at rest (RDS)
- S3 encryption at rest (AES-256)
- Secrets in AWS Secrets Manager (not env vars)
- PII redaction in logs

### Content Safety
- Multi-layer safety checks (orchestrator, safety agent, prompts)
- User violation tracking and banning
- Automated content moderation

---

## Monitoring & Observability

### Metrics (CloudWatch + Datadog)
- API request rate, latency, error rate
- Video generation success rate
- Average generation time
- Cost per video
- Active users, MAU

### Logging
- Structured JSON logs
- Log levels: DEBUG, INFO, WARN, ERROR
- Centralized logging (CloudWatch Logs)
- Request tracing with correlation IDs

### Alerts
- Generation success rate < 90%
- Average generation time > 10 minutes
- API error rate > 5%
- Cost per video > $5.00

---

## Cost Optimization

### Strategies
1. **Caching**: Reuse Creative Bibles and reference images
2. **Batching**: Generate multiple ads in parallel
3. **Cheaper Models**: Use GPT-4 Turbo instead of GPT-4 for non-critical tasks
4. **S3 Lifecycle**: Move old videos to Glacier after 90 days
5. **CDN**: CloudFront reduces S3 bandwidth costs

### Cost Breakdown (Per Video)
- Claude API: $0.15
- DALL-E (4 images): $0.40
- Sora (5 scenes): $1.50
- Suno (1 track): $0.25
- Infrastructure: $0.20
- **Total**: ~$2.50/video

---

**Last Updated**: November 15, 2025  
**Status**: Active Development  
**Next Review**: December 1, 2025  
**Owner**: Engineering Team

