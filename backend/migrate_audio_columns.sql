-- Migration: Add audio columns to campaigns table
-- Run this SQL directly in your database if you have access

DO $$ 
BEGIN
    -- Add audio_url column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'campaigns' AND column_name = 'audio_url'
    ) THEN
        ALTER TABLE campaigns ADD COLUMN audio_url VARCHAR;
        RAISE NOTICE 'Added audio_url column';
    ELSE
        RAISE NOTICE 'audio_url column already exists';
    END IF;
    
    -- Add audio_status column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'campaigns' AND column_name = 'audio_status'
    ) THEN
        ALTER TABLE campaigns ADD COLUMN audio_status VARCHAR DEFAULT 'pending';
        RAISE NOTICE 'Added audio_status column';
    ELSE
        RAISE NOTICE 'audio_status column already exists';
    END IF;
    
    -- Add audio_generation_error column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'campaigns' AND column_name = 'audio_generation_error'
    ) THEN
        ALTER TABLE campaigns ADD COLUMN audio_generation_error VARCHAR;
        RAISE NOTICE 'Added audio_generation_error column';
    ELSE
        RAISE NOTICE 'audio_generation_error column already exists';
    END IF;
END $$;

