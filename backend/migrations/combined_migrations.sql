-- Phase 1: Core Pipeline Upgrade - Database Migration
-- Video Improvements Plan - New Campaign Fields
--
-- Run this migration on your PostgreSQL database to add the new fields
-- Required before deploying the Phase 1 backend changes
--
-- Usage:
--   psql -d your_database -f migrations/001_phase1_video_improvements.sql
-- Or via Supabase SQL Editor

-- Add director_mode field
-- Values: "surprise_me" (default, auto-approves all steps) | "ill_direct" (manual review)
ALTER TABLE campaigns
ADD COLUMN IF NOT EXISTS director_mode VARCHAR(50) DEFAULT 'surprise_me';

-- Add image_prompts JSON field
-- Structure: [{scene_number: 1, image_prompt: "...", motion_prompt: "..."}, ...]
ALTER TABLE campaigns
ADD COLUMN IF NOT EXISTS image_prompts JSONB DEFAULT NULL;

-- Add pipeline_stage field for tracking multi-stage pipeline progress
-- Values: pending, prompts_generating, prompts_ready, images_generating, images_ready,
--         upscaling, videos_generating, videos_ready, post_processing, assembling, completed, failed
ALTER TABLE campaigns
ADD COLUMN IF NOT EXISTS pipeline_stage VARCHAR(50) DEFAULT 'pending';

-- Add color_grade_preset field for post-processing
-- Values: cinematic (default), warm, cool, vintage, etc.
ALTER TABLE campaigns
ADD COLUMN IF NOT EXISTS color_grade_preset VARCHAR(50) DEFAULT 'cinematic';

-- Add brand_colors JSON field for color grading shift toward brand palette
-- Structure: ["#FF5733", "#2E86AB", ...] - hex colors from brand
ALTER TABLE campaigns
ADD COLUMN IF NOT EXISTS brand_colors JSONB DEFAULT NULL;

-- Create index on pipeline_stage for efficient status queries
CREATE INDEX IF NOT EXISTS idx_campaigns_pipeline_stage
ON campaigns(pipeline_stage);

-- Create index on director_mode for filtering
CREATE INDEX IF NOT EXISTS idx_campaigns_director_mode
ON campaigns(director_mode);

-- Add comment to document the new video_urls JSON structure
-- The video_urls field now supports an enhanced per-scene structure:
-- {
--   "scene_number": 1,
--   "image_prompt": "...",
--   "motion_prompt": "...",
--   "prompts_approved": false,
--   "base_image_url": "...",
--   "image_status": "pending|generating|completed|failed",
--   "image_prediction_id": "...",
--   "image_approved": false,
--   "upscaled_image_url": "...",
--   "upscale_status": "pending|generating|completed|failed",
--   "upscale_prediction_id": "...",
--   "video_url": "...",
--   "video_status": "pending|generating|completed|failed",
--   "video_prediction_id": "...",
--   "video_approved": false,
--   "processed_video_url": "...",
--   "processing_status": "pending|completed|failed",
--   "status": "pending|generating|completed|failed",
--   "duration": 6.0,
--   "error": null,
--   "retry_count": 0
-- }
COMMENT ON COLUMN campaigns.video_urls IS 'JSON array of per-scene video generation status with Phase 1 enhanced structure including image/upscale/video status tracking';

-- Verify migration
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'campaigns'
AND column_name IN ('director_mode', 'image_prompts', 'pipeline_stage', 'color_grade_preset', 'brand_colors');
-- Phase V2: Viral Ad Pipeline - Story-First Sequential Generation
-- Database Migration for new Campaign Fields
--
-- Run this migration on your PostgreSQL database to add V2 pipeline fields
-- Required before deploying the V2 backend changes
--
-- Usage:
--   psql -d your_database -f migrations/002_v2_story_document_fields.sql
-- Or via Supabase SQL Editor

-- Add story_document JSON field
-- Structure: {
--   "title": "...",
--   "logline": "...",
--   "characters": [{id, name, description}, ...],
--   "narrator": {voice_style, tone, elevenlabs_voice_id},
--   "app_screens": [{id, url, description}, ...],
--   "segments": [{number, narration, action, end_state, app_moment}, ...]
-- }
ALTER TABLE campaigns
ADD COLUMN IF NOT EXISTS story_document JSONB DEFAULT NULL;

-- Add voiceover_url field for ElevenLabs TTS full narration
ALTER TABLE campaigns
ADD COLUMN IF NOT EXISTS voiceover_url VARCHAR(2048) DEFAULT NULL;

-- Add voiceover_status field
-- Values: pending, generating, completed, failed
ALTER TABLE campaigns
ADD COLUMN IF NOT EXISTS voiceover_status VARCHAR(50) DEFAULT 'pending';

-- Add final_audio_url field for mixed voiceover + music
ALTER TABLE campaigns
ADD COLUMN IF NOT EXISTS final_audio_url VARCHAR(2048) DEFAULT NULL;

-- Add current_segment field to track sequential video progress (1-5)
ALTER TABLE campaigns
ADD COLUMN IF NOT EXISTS current_segment INTEGER DEFAULT 0;

-- Add pipeline_version field
-- Values: "v1" (parallel image-first) or "v2" (sequential story-first)
ALTER TABLE campaigns
ADD COLUMN IF NOT EXISTS pipeline_version VARCHAR(10) DEFAULT 'v1';

-- Create index on pipeline_version for filtering
CREATE INDEX IF NOT EXISTS idx_campaigns_pipeline_version
ON campaigns(pipeline_version);

-- Create index on voiceover_status for status queries
CREATE INDEX IF NOT EXISTS idx_campaigns_voiceover_status
ON campaigns(voiceover_status);

-- Add comment to document the story_document structure
COMMENT ON COLUMN campaigns.story_document IS 'V2 Pipeline: Full story document with characters, narrator, app_screens, and 5 segments. Generated by GPT-4o Vision.';

COMMENT ON COLUMN campaigns.voiceover_url IS 'V2 Pipeline: ElevenLabs TTS full 40-second narration audio URL';

COMMENT ON COLUMN campaigns.final_audio_url IS 'V2 Pipeline: Mixed voiceover + music audio for final video';

COMMENT ON COLUMN campaigns.current_segment IS 'V2 Pipeline: Current segment being generated (1-5) for sequential video generation';

COMMENT ON COLUMN campaigns.pipeline_version IS 'Pipeline version: v1 (parallel image-first) or v2 (sequential story-first)';

-- Verify migration
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'campaigns'
AND column_name IN ('story_document', 'voiceover_url', 'voiceover_status', 'final_audio_url', 'current_segment', 'pipeline_version');
