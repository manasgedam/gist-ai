-- Add user_id to videos and ideas tables for user-scoped data

-- Add user_id column to videos table
ALTER TABLE videos 
ADD COLUMN user_id UUID REFERENCES auth.users(id);

-- Create index for faster user-specific queries
CREATE INDEX idx_videos_user_id ON videos(user_id);

-- Add user_id to ideas table (optional, can derive from video)
ALTER TABLE ideas
ADD COLUMN user_id UUID REFERENCES auth.users(id);

CREATE INDEX idx_ideas_user_id ON ideas(user_id);

-- Enable Row Level Security on videos table
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own videos
CREATE POLICY "Users can view own videos"
ON videos FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Users can only insert their own videos
CREATE POLICY "Users can insert own videos"
ON videos FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Policy: Users can only update their own videos
CREATE POLICY "Users can update own videos"
ON videos FOR UPDATE
USING (auth.uid() = user_id);

-- Policy: Users can only delete their own videos
CREATE POLICY "Users can delete own videos"
ON videos FOR DELETE
USING (auth.uid() = user_id);

-- Enable Row Level Security on ideas table
ALTER TABLE ideas ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view ideas for their own videos
CREATE POLICY "Users can view own ideas"
ON ideas FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Users can insert ideas for their own videos
CREATE POLICY "Users can insert own ideas"
ON ideas FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own ideas
CREATE POLICY "Users can update own ideas"
ON ideas FOR UPDATE
USING (auth.uid() = user_id);

-- Policy: Users can delete their own ideas
CREATE POLICY "Users can delete own ideas"
ON ideas FOR DELETE
USING (auth.uid() = user_id);

-- Enable RLS on segments table
ALTER TABLE segments ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view segments for their own ideas
CREATE POLICY "Users can view own segments"
ON segments FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM ideas
    WHERE ideas.id = segments.idea_id
    AND ideas.user_id = auth.uid()
  )
);

-- Policy: Users can insert segments for their own ideas
CREATE POLICY "Users can insert own segments"
ON segments FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM ideas
    WHERE ideas.id = segments.idea_id
    AND ideas.user_id = auth.uid()
  )
);

-- For development: Assign existing videos to a test user (optional)
-- UPDATE videos SET user_id = 'your-test-user-id' WHERE user_id IS NULL;
