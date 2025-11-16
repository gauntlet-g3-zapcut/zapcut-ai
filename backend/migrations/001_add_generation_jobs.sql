-- Migration: Add generation_jobs table and campaign tracking fields
-- Epic 5, Story 5.2: Enhanced Job Queue & Tracking System
-- Created: 2025-11-15

-- Create generation_jobs table
CREATE TABLE IF NOT EXISTS generation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL,  -- 'scene_video', 'voiceover', 'music', 'composite'
    scene_number INTEGER,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    replicate_job_id VARCHAR(255),
    input_params JSONB,
    output_url TEXT,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_generation_jobs_campaign ON generation_jobs(campaign_id);
CREATE INDEX IF NOT EXISTS idx_generation_jobs_status ON generation_jobs(status);

-- Add new columns to campaigns table
ALTER TABLE campaigns
ADD COLUMN IF NOT EXISTS voiceover_urls JSONB,
ADD COLUMN IF NOT EXISTS generation_stage VARCHAR(50) DEFAULT 'not_started',
ADD COLUMN IF NOT EXISTS generation_progress INTEGER DEFAULT 0;

-- Add comments for documentation
COMMENT ON TABLE generation_jobs IS 'Tracks individual job execution for video generation pipeline';
COMMENT ON COLUMN generation_jobs.job_type IS 'Type of generation job: scene_video, voiceover, music, composite';
COMMENT ON COLUMN generation_jobs.status IS 'Job status: pending, processing, completed, failed';
COMMENT ON COLUMN campaigns.voiceover_urls IS 'Array of voiceover URLs per scene';
COMMENT ON COLUMN campaigns.generation_stage IS 'Current pipeline stage: not_started, reference_images, storyboard, scene_videos, voiceovers, music, compositing, complete';
COMMENT ON COLUMN campaigns.generation_progress IS 'Progress percentage 0-100';
