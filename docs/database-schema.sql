-- Database Schema for CritiqueWire Backend
-- Run this in your Supabase SQL Editor

-- Create the analyses table
CREATE TABLE IF NOT EXISTS analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    preset TEXT NOT NULL DEFAULT 'general',
    analysis_type TEXT NOT NULL CHECK (analysis_type IN ('url', 'text')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    article_id UUID,
    url TEXT,
    content_preview TEXT,
    results JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_status ON analyses(status);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_preset ON analyses(preset);
CREATE INDEX IF NOT EXISTS idx_analyses_analysis_type ON analyses(analysis_type);

-- Create a full-text search index for title and content_preview
CREATE INDEX IF NOT EXISTS idx_analyses_search ON analyses USING GIN (to_tsvector('english', title || ' ' || COALESCE(content_preview, '')));

-- Enable Row Level Security (RLS)
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users can only see their own analyses
CREATE POLICY "Users can view their own analyses" ON analyses
    FOR SELECT USING (auth.uid() = user_id);

-- Users can insert their own analyses
CREATE POLICY "Users can insert their own analyses" ON analyses
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can update their own analyses
CREATE POLICY "Users can update their own analyses" ON analyses
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can delete their own analyses
CREATE POLICY "Users can delete their own analyses" ON analyses
    FOR DELETE USING (auth.uid() = user_id);

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create a trigger to automatically update the updated_at column
CREATE TRIGGER update_analyses_updated_at 
    BEFORE UPDATE ON analyses 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Optional: Create a view for analysis statistics
CREATE OR REPLACE VIEW analysis_stats AS
SELECT 
    user_id,
    COUNT(*) as total_analyses,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_analyses,
    COUNT(*) FILTER (WHERE status = 'pending') as pending_analyses,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_analyses,
    AVG((results->>'analysisScore')::float) FILTER (WHERE results IS NOT NULL) as avg_analysis_score,
    MAX(created_at) as last_analysis_date
FROM analyses
GROUP BY user_id; 