-- Migration: Extend existing articles table for RSS news feed collection
-- Description: Add RSS-specific columns to existing articles table for unified article management
-- Preserves all existing data and columns (including UUID primary key)

-- Add RSS-specific columns to existing articles table
ALTER TABLE articles 
ADD COLUMN IF NOT EXISTS summary TEXT,
ADD COLUMN IF NOT EXISTS source_url TEXT,  -- RSS feed URL (different from existing source_name)
ADD COLUMN IF NOT EXISTS collected_at TIMESTAMPTZ,  -- When found via RSS (NULL for manual articles)
ADD COLUMN IF NOT EXISTS content_hash TEXT UNIQUE,  -- For RSS deduplication
ADD COLUMN IF NOT EXISTS images JSONB DEFAULT '[]',  -- Multiple images (in addition to existing image_url)
ADD COLUMN IF NOT EXISTS word_count INTEGER,
ADD COLUMN IF NOT EXISTS reading_time INTEGER,
ADD COLUMN IF NOT EXISTS content_extracted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS analysis_status TEXT DEFAULT 'not_analyzed' 
    CHECK (analysis_status IN ('not_analyzed', 'pending', 'completed', 'failed')),
ADD COLUMN IF NOT EXISTS analysis_id UUID REFERENCES analyses(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS thumbnail_url TEXT;  -- RSS thumbnail (different from existing image_url)

-- Add indexes for RSS functionality (only new columns)
CREATE INDEX IF NOT EXISTS idx_articles_collected_at ON articles(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_analysis_status ON articles(analysis_status);
CREATE INDEX IF NOT EXISTS idx_articles_content_hash ON articles(content_hash);
CREATE INDEX IF NOT EXISTS idx_articles_source_url ON articles(source_url);

-- Enhance existing published_at index if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at DESC);

-- Full-text search index for title and summary (enhance existing search capability)
CREATE INDEX IF NOT EXISTS idx_articles_search ON articles 
USING gin(to_tsvector('english', title || ' ' || COALESCE(summary, '')));

-- Update existing updated_at trigger to handle new columns
-- (This will work with existing trigger if it exists)

-- Comments for new columns
COMMENT ON COLUMN articles.summary IS 'Article summary/excerpt (from RSS feeds)';
COMMENT ON COLUMN articles.source_url IS 'RSS feed URL (for auto-collected articles)';
COMMENT ON COLUMN articles.collected_at IS 'When article was collected via RSS (NULL for manual articles)';
COMMENT ON COLUMN articles.content_hash IS 'Content hash for RSS deduplication';
COMMENT ON COLUMN articles.images IS 'Array of image URLs from article';
COMMENT ON COLUMN articles.word_count IS 'Number of words in article content';
COMMENT ON COLUMN articles.reading_time IS 'Estimated reading time in minutes';
COMMENT ON COLUMN articles.content_extracted_at IS 'When full content was extracted';
COMMENT ON COLUMN articles.analysis_status IS 'Status of AI analysis (not_analyzed/pending/completed/failed)';
COMMENT ON COLUMN articles.analysis_id IS 'Reference to analysis results if performed';
COMMENT ON COLUMN articles.thumbnail_url IS 'Article thumbnail image (from RSS)';

-- Update table comment
COMMENT ON TABLE articles IS 'Unified articles table: manually added articles and RSS-collected articles';

-- Note: Existing columns remain completely unchanged:
-- id (UUID), title, content, url, source_name, author, published_at, image_url, created_at, updated_at 