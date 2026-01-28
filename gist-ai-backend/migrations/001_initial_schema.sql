-- Initial schema for Gist AI storage
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Videos table
CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Source
    source_url TEXT NOT NULL,
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('youtube', 'upload')),
    youtube_id VARCHAR(20),
    
    -- Metadata
    title TEXT,
    duration FLOAT,
    language VARCHAR(10),
    
    -- Storage References (R2 URLs)
    original_video_url TEXT,
    audio_file_url TEXT,
    transcript_url TEXT,
    
    -- Processing State
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' 
        CHECK (status IN ('PENDING', 'INGESTING', 'TRANSCRIBING', 'UNDERSTANDING', 'GROUPING', 'RANKING', 'COMPLETE', 'FAILED')),
    current_stage VARCHAR(20),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Ideas table
CREATE TABLE ideas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    
    -- Idea Content
    rank INTEGER NOT NULL CHECK (rank > 0),
    title TEXT NOT NULL,
    description TEXT,
    reason TEXT,
    
    -- Scoring
    strength VARCHAR(20) CHECK (strength IN ('strong', 'medium', 'weak')),
    viral_potential FLOAT CHECK (viral_potential >= 0 AND viral_potential <= 1),
    
    -- Metadata
    total_duration FLOAT,
    segment_count INTEGER,
    
    -- Storage Reference
    clip_url TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Segments table
CREATE TABLE segments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    idea_id UUID NOT NULL REFERENCES ideas(id) ON DELETE CASCADE,
    
    -- Timing
    start_time FLOAT NOT NULL CHECK (start_time >= 0),
    end_time FLOAT NOT NULL CHECK (end_time > start_time),
    duration FLOAT NOT NULL CHECK (duration > 0),
    
    -- Segment Metadata
    purpose TEXT,
    sequence_order INTEGER NOT NULL CHECK (sequence_order > 0),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Processing events table (optional - for debugging/analytics)
CREATE TABLE processing_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    
    -- Event Details
    event_type VARCHAR(50) NOT NULL,
    stage VARCHAR(20),
    progress INTEGER,
    message TEXT,
    error_details JSONB,
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_videos_created_at ON videos(created_at DESC);
CREATE INDEX idx_videos_youtube_id ON videos(youtube_id);

CREATE INDEX idx_ideas_video_id ON ideas(video_id);
CREATE INDEX idx_ideas_rank ON ideas(video_id, rank);

CREATE INDEX idx_segments_idea_id ON segments(idea_id);
CREATE INDEX idx_segments_sequence ON segments(idea_id, sequence_order);

CREATE INDEX idx_events_video_id ON processing_events(video_id);
CREATE INDEX idx_events_created_at ON processing_events(created_at DESC);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_videos_updated_at BEFORE UPDATE ON videos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) - Enable later if needed
-- ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE ideas ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE segments ENABLE ROW LEVEL SECURITY;

-- Grant permissions (adjust based on your auth setup)
-- GRANT ALL ON videos TO authenticated;
-- GRANT ALL ON ideas TO authenticated;
-- GRANT ALL ON segments TO authenticated;
-- GRANT ALL ON processing_events TO authenticated;
