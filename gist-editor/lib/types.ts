export interface Segment {
  start_time_formatted: string
  end_time_formatted: string
  start_seconds: number
  end_seconds: number
  duration_seconds: number
  purpose: string
}

export interface Idea {
  title: string
  description: string
  segments: Segment[]
  segment_count: number
  total_duration_seconds: number
  reasoning: string
  transcript_excerpt: string
}

export interface IdeasData {
  video_id: string
  source_url: string
  total_duration: number
  model_used: string
  processing_method: string
  ideas_count: number
  ideas: Idea[]
}

export interface TranscriptSegment {
  id: number
  start: number
  end: number
  text: string
  words?: Array<{
    word: string
    start: number
    end: number
  }>
}

export interface TranscriptData {
  video_id: string
  source_url: string
  video_file_path: string
  language: string
  duration: number
  segments: TranscriptSegment[]
}