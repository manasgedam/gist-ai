-- Migration: Enable Row Level Security (RLS)
-- Run this in Supabase SQL Editor AFTER 004_add_foreign_keys.sql
-- Purpose: Enforce user isolation at database level

-- Enable RLS on all tables
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE ideas ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (idempotent)
DROP POLICY IF EXISTS "Users can only access their own projects" ON projects;
DROP POLICY IF EXISTS "Users can only access videos in their projects" ON videos;
DROP POLICY IF EXISTS "Users can only access ideas from their videos" ON ideas;

-- Projects: Users can only access their own projects
CREATE POLICY "Users can only access their own projects"
ON projects FOR ALL
USING (auth.uid() = user_id);

-- Videos: Users can only access videos in their projects
CREATE POLICY "Users can only access videos in their projects"
ON videos FOR ALL
USING (
    user_id = auth.uid()
    OR project_id IN (
        SELECT id FROM projects WHERE user_id = auth.uid()
    )
);

-- Ideas: Users can only access ideas from their videos
CREATE POLICY "Users can only access ideas from their videos"
ON ideas FOR ALL
USING (
    user_id = auth.uid()
    OR video_id IN (
        SELECT id FROM videos WHERE user_id = auth.uid()
    )
);

-- Verify RLS is enabled
SELECT
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE tablename IN ('projects', 'videos', 'ideas')
ORDER BY tablename;

-- Verify policies exist
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE tablename IN ('projects', 'videos', 'ideas')
ORDER BY tablename, policyname;
