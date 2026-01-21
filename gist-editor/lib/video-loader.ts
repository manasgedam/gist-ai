import { IdeasData, TranscriptData } from './types'

export async function getLatestVideoData(): Promise<{
  ideas: IdeasData | null
  transcript: TranscriptData | null
  videoId: string | null
}> {
  try {
    // Fetch all files from output directory
    const response = await fetch('/api/get-latest-video')
    if (!response.ok) throw new Error('Failed to fetch video data')
    
    const data = await response.json()
    return data
  } catch (error) {
    console.error('Error loading video data:', error)
    return { ideas: null, transcript: null, videoId: null }
  }
}

export function getVideoUrl(videoId: string): string {
  return `/output/${videoId}_video.mp4`
}