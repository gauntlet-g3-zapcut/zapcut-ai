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
