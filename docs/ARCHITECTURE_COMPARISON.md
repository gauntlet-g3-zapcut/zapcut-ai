# Architecture Comparison: Current Implementation vs AIVP Documentation

**Date:** 2025-11-15
**Status:** Analysis of technical and architectural differences

---

## Executive Summary

The current implementation deviates from the AIVP documentation in several key areas, particularly around authentication, job queuing, database schema, and video generation workflow. This document identifies these differences and their implications.

---

## 1. Authentication & User Management

### AIVP Specification
- **Auth Provider**: Firebase Authentication
- **Backend**: Firebase Admin SDK for token verification
- **Schema**: User model with Firebase UID reference

### Current Implementation
- **Auth Provider**: ✅ Supabase Authentication
- **Backend**: Supabase JWT (RS256) with JWKS verification
- **Schema**: User model with `supabase_uid` field

### Impact
- ✅ **POSITIVE**: Supabase provides auth + database in one service
- ⚠️ **DEVIATION**: Firebase dependency removed entirely
- 📝 **NOTE**: Supabase URL configured in `.env`

**Recommendation**: Document Supabase as the official auth provider in updated AIVP docs.

---

## 2. Job Queue System

### AIVP Specification (Decision #11)
- **Queue System**: RQ (Redis Queue)
- **Rationale**: Simpler than Celery, perfect for sequential workflows
- **Workers**: Can scale horizontally

### Current Implementation
- **Queue System**: ✅ Celery + Redis
- **Task**: `generate_campaign_video` (video_generation.py:36-184)
- **Concurrency**: 14 workers (prefork)

### Impact
- ⚠️ **DEVIATION**: Using Celery instead of RQ
- ✅ **FEATURE PARITY**: Both support background jobs, Redis backend
- 📊 **DIFFERENCE**: Celery is more complex but more powerful
- ⚠️ **CONFIG ISSUE**: Deprecation warning about `broker_connection_retry_on_startup`

**Recommendation**: Either update AIVP to specify Celery, or migrate to RQ as specified.

---

## 3. Database Schema

### AIVP Specification (Decision #9)
```sql
users (id, email, name, password_hash, subscription_tier, credits, free_videos_used)
brands (id, user_id, title, description, product_images[], brand_guidelines JSONB)
ad_projects (id, user_id, brand_id, status, ad_details JSONB, zapcut_project_id)
chat_messages (id, ad_project_id, role, content)
scripts (id, ad_project_id, storyline, scenes JSONB, approved_at)
generation_jobs (id, ad_project_id, job_type, status, replicate_job_id, input_params JSONB, output_url)
lora_models (id, brand_id, status, model_url, preview_image_url, user_approved)
```

### Current Implementation
```python
users (id, supabase_uid, email, created_at, updated_at)
brands (id, user_id, title, description, product_image_1_url, product_image_2_url)
creative_bibles (id, brand_id, name, creative_bible JSONB, reference_image_urls JSONB, conversation_history JSONB)
campaigns (id, brand_id, creative_bible_id, storyline JSONB, sora_prompts JSONB, suno_prompt, video_urls JSONB, music_url, final_video_url, status)
```

### Major Differences

#### ❌ MISSING TABLES
- `chat_messages` - No separate table for conversation history
  - **Current**: Stored as JSONB in `creative_bibles.conversation_history`
  - **Impact**: Harder to query individual messages, no indexing

- `scripts` - No separate scripts table
  - **Current**: Storyline stored directly in `campaigns.storyline`
  - **Impact**: No approval workflow tracking

- `generation_jobs` - No job tracking table
  - **Current**: Status tracked only in `campaigns.status`
  - **Impact**: No granular job progress, no Replicate job ID tracking

- `lora_models` - LoRA training not implemented
  - **Current**: No LoRA model support
  - **Impact**: Missing key differentiation feature

#### ✅ ADDED TABLES
- `creative_bibles` - New concept not in AIVP
  - **Purpose**: Stores brand visual guidelines and reference images
  - **Impact**: Better separation of brand style from individual campaigns

#### 🔄 SCHEMA CHANGES
- **Users**: Missing fields
  - ❌ No `subscription_tier`
  - ❌ No `credits`
  - ❌ No `free_videos_used`
  - ✅ Has `supabase_uid` instead of Firebase UID

- **Brands**: Different image storage
  - ❌ `product_image_1_url` + `product_image_2_url` instead of `product_images[]`
  - ❌ No `brand_guidelines` JSONB (moved to `creative_bibles`)

- **Campaigns**: Denormalized structure
  - ✅ Has `creative_bible_id` FK
  - ✅ Has `video_urls` JSONB for all scenes
  - ⚠️ Missing individual `generation_jobs` tracking
  - ⚠️ No `zapcutProjectId` link

**Recommendation**: Add missing tables for production-ready system, especially `generation_jobs` for progress tracking.

---

## 4. Video Generation Workflow

### AIVP Specification (Decision #10 - Sequential Pipeline)
```
Scene 1 video (with prompt) →
Scene 2 video (with Scene 1 reference) →
Scene 3 video (with Scene 1+2 reference) →
Voiceover (all scenes) →
Music (full ad) →
SFX (optional) →
Composite (stitch everything)
```
**Duration**: 6-8 minutes
**Approach**: Sequential for visual continuity

### Current Implementation
```python
# video_generation.py:112-136
video_results = generate_videos_parallel(campaign.sora_prompts)
```
**Approach**: ❌ **PARALLEL** video generation

### Impact
- ⚠️ **CRITICAL DEVIATION**: Violates AIVP Decision #10
- ❌ **QUALITY RISK**: Parallel generation sacrifices scene-to-scene continuity
- ❌ **MISSING FEATURES**:
  - No voiceover generation
  - No SFX support
  - Only music generation implemented

**Recommendation**: **URGENT** - Refactor to sequential generation as specified in AIVP.

---

## 5. Audio Architecture

### AIVP Specification (Decision #1)
- **Voiceover**: Replicate TTS (Bark/Coqui XTTS) - $0.05-0.10 per 30s
- **Music**: Suno AI (standalone API) - $10-30/mo subscription
- **SFX**: Replicate audio or Freesound API - $0.01-0.05 per ad

### Current Implementation
- **Voiceover**: ❌ NOT IMPLEMENTED
- **Music**: ✅ Suno via Replicate (`generate_music_with_suno`)
- **SFX**: ❌ NOT IMPLEMENTED

### Impact
- ⚠️ **INCOMPLETE**: Only 1 of 3 audio components implemented
- ❌ **MISSING MVP FEATURES**: Professional ads require voiceover

**Recommendation**: Implement voiceover as P0 for MVP.

---

## 6. FFmpeg Composition Pipeline

### AIVP Specification (Decision #15)
```python
1. Download assets from S3
2. Stitch scenes (1s crossfade transitions)
3. Overlay product images at timestamps
4. Mix audio (VO 100%, Music 30%, SFX 50%)
5. Export H.264 1080p/4K
6. Upload to S3
```

### Current Implementation
```python
# video_generation.py:218-289
def compose_video(video_urls, music_url, brand_title):
    # 1. Download videos
    # 2. Concatenate with ffmpeg -f concat (NO crossfades)
    # 3. Mix music (NO voiceover, NO SFX)
    # 4. NO product image overlays
    # 5. Basic export
```

### Missing Features
- ❌ 1-second crossfade transitions (AIVP specifies crossfades for polish)
- ❌ Product image overlays
- ❌ Multi-layer audio mixing (only music, no VO/SFX)
- ❌ Proper volume levels (VO 100%, Music 30%, SFX 50%)

**Recommendation**: Implement full FFmpeg pipeline as specified in AIVP Decision #15.

---

## 7. Frontend Architecture

### AIVP Specification
- **Desktop**: Electron + React + TypeScript
- **Integration**: Zapcut video editor (local)
- **State**: Zustand persist

### Current Implementation
- **Desktop**: ❌ Web-only (React + Vite)
- **Integration**: ❌ No Zapcut editor integration
- **State**: ⚠️ AuthContext only (no global Zustand store visible)

### Impact
- ⚠️ **MAJOR DEVIATION**: No Electron wrapper
- ❌ **MISSING CORE FEATURE**: No video editor integration
- 📝 **NOTE**: Product name is "AdCraft" not "Zapcut AI"

**Recommendation**: Determine if Electron is still required, or update AIVP to reflect web-first approach.

---

## 8. LoRA Fine-Tuning

### AIVP Specification (Decision #2)
- **Strategy**: Progressive training after first video
- **Training**: 30-45 minutes background job
- **Preview**: Side-by-side comparison before second video
- **Schema**: `lora_models` table with status tracking

### Current Implementation
- ❌ **NOT IMPLEMENTED**
- No `lora_models` table
- No training jobs
- No preview UI

### Impact
- ❌ **MISSING DIFFERENTIATION**: This is a key competitive feature
- ❌ **NO BRAND CONSISTENCY**: Without LoRA, videos won't have consistent brand style

**Recommendation**: Implement LoRA training as P1 feature (post-MVP but high priority).

---

## 9. Pricing & Subscription

### AIVP Specification (Decision #3)
```
Free Tier: 2 videos (15s + 30s)
Credits: $5/30s, $8/60s
Subscriptions: Starter ($29), Pro ($79), Agency ($199)
```

### Current Implementation
- ❌ No subscription tier in User model
- ❌ No credits tracking
- ❌ No `free_videos_used` counter
- ❌ No tier-based feature gating

### Impact
- ❌ **BLOCKER**: Cannot enforce pricing model
- ❌ **NO MONETIZATION**: System cannot charge users

**Recommendation**: Add subscription fields to User model as P0 before launch.

---

## 10. API Routes Comparison

### Current Routes
```python
# auth.py
POST /api/auth/verify - Verify Supabase token
GET /api/auth/me - Get current user

# brands.py
GET /api/brands - List user brands
POST /api/brands - Create brand
GET /api/brands/{id} - Get brand details

# campaigns.py
POST /api/campaigns - Create campaign
GET /api/campaigns/{id} - Get campaign status
POST /api/campaigns/{id}/generate - Start video generation

# chat.py
POST /api/chat/creative-brief - Start conversation
POST /api/chat/message - Send message
```

### AIVP Expected Routes
- ✅ Auth routes match
- ✅ Brand CRUD matches
- ⚠️ Campaign routes partial (missing detailed progress)
- ❌ Missing: Script approval endpoint
- ❌ Missing: LoRA training endpoints
- ❌ Missing: Video editor integration endpoints

---

## 11. Dependencies Comparison

### AIVP Specification
```
Backend: Python 3.11+, FastAPI, PostgreSQL, RQ, Redis, FFmpeg
Frontend: Electron, React, TypeScript, Zustand, TailwindCSS
APIs: OpenAI GPT-4, Sora (Replicate), Suno AI, Replicate TTS
```

### Current Implementation (requirements.txt)
```
✅ fastapi==0.109.0
✅ sqlalchemy==2.0.25
✅ psycopg2-binary==2.9.9
⚠️ celery==5.3.4 (should be RQ per AIVP)
✅ redis==5.0.1
✅ openai==1.12.0
✅ replicate==0.22.0
✅ boto3==1.34.34 (for S3)
❌ firebase-admin (removed, using Supabase)
⚠️ PyJWT==2.8.0 + cryptography (for Supabase JWT)
```

### Frontend (package.json)
```
✅ react, react-dom, react-router-dom
✅ tailwindcss
✅ lucide-react (icons)
✅ @supabase/supabase-js
❌ electron (not present - web only)
❌ zustand (not in dependencies, but may be used)
```

---

## 12. Configuration Differences

### AIVP Environment Variables
```
DATABASE_URL, REDIS_URL
OPENAI_API_KEY, REPLICATE_API_TOKEN
AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET
FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY, FIREBASE_CLIENT_EMAIL
CORS_ORIGINS
```

### Current .env
```
✅ DATABASE_URL
✅ REDIS_URL
✅ OPENAI_API_KEY, REPLICATE_API_TOKEN
✅ AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET
✅ AWS_REGION, AWS_ENDPOINT_URL (for Cloudflare R2 support)
✅ SUPABASE_URL (replaces Firebase config)
❌ No Firebase credentials
✅ CORS_ORIGINS
```

---

## Summary of Critical Issues

### 🔴 BLOCKING (Must fix before production)
1. **No subscription/credits system** - Cannot monetize
2. **No job tracking table** - Cannot show granular progress
3. **Parallel video generation** - Quality risk (violates AIVP Decision #10)
4. **No voiceover** - Incomplete audio suite

### 🟡 HIGH PRIORITY (Missing core features)
5. **No LoRA training** - Missing differentiation
6. **No crossfade transitions** - Lower video quality
7. **No product image overlays** - Missing brand integration
8. **No Electron/Zapcut integration** - Not a desktop app

### 🟢 MEDIUM PRIORITY (Architectural debt)
9. **RQ vs Celery** - Architecture mismatch
10. **No chat_messages table** - Harder to query conversations
11. **No scripts table** - No approval workflow
12. **No SFX support** - Incomplete audio

### ✅ ACCEPTABLE DEVIATIONS
- Supabase instead of Firebase (simpler, integrated)
- Creative Bibles concept (good separation of concerns)
- Cloudflare R2 support (cost savings)

---

## Recommendations

### Immediate (Week 1)
1. Add subscription fields to User model
2. Refactor video generation to sequential (AIVP Decision #10)
3. Implement voiceover generation
4. Add `generation_jobs` table for progress tracking

### Short-term (Week 2-4)
5. Implement crossfade transitions in FFmpeg
6. Add product image overlay support
7. Implement proper audio mixing (VO 100%, Music 30%)
8. Update AIVP docs to reflect Supabase auth

### Medium-term (Month 2)
9. Implement LoRA training workflow
10. Add SFX support
11. Migrate to RQ OR update AIVP to specify Celery
12. Add chat_messages and scripts tables

### Long-term (Month 3+)
13. Electron wrapper + Zapcut editor integration
14. 4K video support (currently 1080p only)
15. API access for Agency tier

---

## Conclusion

The current implementation is a **functional MVP prototype** but deviates significantly from AIVP specifications in key areas:

- ✅ **Core flow works**: Auth → Brands → Chat → Video generation
- ⚠️ **Quality concerns**: Parallel generation reduces video quality
- ❌ **Missing monetization**: Cannot charge users
- ❌ **Incomplete features**: No voiceover, LoRA, or editor integration

**Next Steps**: Prioritize fixing blocking issues (subscription system, sequential generation, voiceover) before launch.
