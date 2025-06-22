-- Migration: Remove old image columns after consolidating to image_url
-- Date: 2025-06-22
-- Description: Remove the deprecated 'images' (JSONB) and 'thumbnail_url' columns
--              since all images are now consolidated into the single 'image_url' field

-- Remove the old image columns
ALTER TABLE articles DROP COLUMN IF EXISTS images;
ALTER TABLE articles DROP COLUMN IF EXISTS thumbnail_url;

-- Add a comment to document the change
COMMENT ON COLUMN articles.image_url IS 'Single image URL for all articles (consolidated from old images array and thumbnail_url fields)'; 