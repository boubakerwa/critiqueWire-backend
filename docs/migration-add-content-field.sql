-- Migration: Add content field to analyses table
-- This migration adds a full content field to store complete content for analysis processing
-- Run this in your Supabase SQL Editor for production database

-- Add content column to existing table if it doesn't exist
-- This is safe to run multiple times
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS content TEXT;

-- Add a comment to document the purpose of the column
COMMENT ON COLUMN analyses.content IS 'Full content for analysis processing (content_preview is for display only)';

-- Optional: Update existing records to copy content_preview to content if content is null
-- This ensures existing analyses have some content for reprocessing
UPDATE analyses 
SET content = content_preview 
WHERE content IS NULL AND content_preview IS NOT NULL;

-- Verify the migration
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'analyses' 
    AND table_schema = 'public'
    AND column_name IN ('content', 'content_preview')
ORDER BY column_name; 