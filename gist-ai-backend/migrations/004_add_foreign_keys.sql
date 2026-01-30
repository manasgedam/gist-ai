-- Migration: Add Foreign Key Constraints
-- Run this in Supabase SQL Editor
-- Purpose: Enforce referential integrity between tables and auth.users

-- 1. Add foreign key from projects.user_id to auth.users
ALTER TABLE projects
ADD CONSTRAINT projects_user_id_fkey
FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- 2. Add foreign key from videos.user_id to auth.users
ALTER TABLE videos
ADD CONSTRAINT videos_user_id_fkey
FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- 3. Add foreign key from videos.project_id to projects
ALTER TABLE videos
ADD CONSTRAINT videos_project_id_fkey
FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

-- 4. Add foreign key from ideas.user_id to auth.users
ALTER TABLE ideas
ADD CONSTRAINT ideas_user_id_fkey
FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- 5. Add foreign key from ideas.video_id to videos
ALTER TABLE ideas
ADD CONSTRAINT ideas_video_id_fkey
FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE;

-- Verify constraints
SELECT
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name IN ('projects', 'videos', 'ideas')
ORDER BY tc.table_name, tc.constraint_name;
