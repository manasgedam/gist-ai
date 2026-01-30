-- Migration: Fix ideas.reason column to allow NULL
-- This aligns the local SQLite schema with the Supabase schema
-- and fixes the NOT NULL constraint failure

-- SQLite doesn't support ALTER COLUMN directly, so we need to recreate the table

BEGIN TRANSACTION;

-- Step 1: Create new table with correct schema
CREATE TABLE ideas_new (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    rank INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    reason TEXT,  -- Now nullable (removed NOT NULL constraint)
    strength TEXT,
    viral_potential REAL,
    highlights TEXT,  -- JSON stored as TEXT
    time_ranges TEXT,  -- JSON stored as TEXT
    created_at TEXT,
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
);

-- Step 2: Copy existing data from old table (if it exists)
INSERT INTO ideas_new 
SELECT id, video_id, rank, title, description, reason, strength, viral_potential, highlights, time_ranges, created_at
FROM ideas;

-- Step 3: Drop old table
DROP TABLE ideas;

-- Step 4: Rename new table to original name
ALTER TABLE ideas_new RENAME TO ideas;

-- Step 5: Recreate indexes for performance
CREATE INDEX IF NOT EXISTS idx_ideas_video_id ON ideas(video_id);
CREATE INDEX IF NOT EXISTS idx_ideas_rank ON ideas(video_id, rank);

COMMIT;

-- Verification query (run separately to check)
-- SELECT sql FROM sqlite_master WHERE type='table' AND name='ideas';
