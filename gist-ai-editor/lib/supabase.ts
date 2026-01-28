import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Auth helpers
export const getCurrentUser = async () => {
  const { data: { user } } = await supabase.auth.getUser()
  return user
}

export const getSession = async () => {
  const { data: { session } } = await supabase.auth.getSession()
  return session
}

export const getAuthToken = async () => {
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token
}

// Database types (auto-generated from Supabase)
export interface Video {
  id: string
  source_url: string
  source_type: 'youtube' | 'upload'
  youtube_id?: string
  title?: string
  duration?: number
  language?: string
  original_video_url?: string
  audio_file_url?: string
  transcript_url?: string
  status: string
  current_stage?: string
  progress: number
  error_message?: string
  user_id?: string
  created_at: string
  updated_at: string
  completed_at?: string
}

export interface Idea {
  id: string
  video_id: string
  rank: number
  title: string
  description?: string
  reason?: string
  strength?: 'strong' | 'medium' | 'weak'
  viral_potential?: number
  total_duration?: number
  segment_count?: number
  clip_url?: string
  user_id?: string
  created_at: string
}

export interface Segment {
  id: string
  idea_id: string
  start_time: number
  end_time: number
  duration: number
  purpose?: string
  sequence_order: number
  created_at: string
}
