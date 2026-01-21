'use client'

import { useEffect, useState } from 'react'
import { useEditorStore } from '@/lib/store'
import { getLatestVideoData } from '@/lib/video-loader'
import EditorLayout from '@/components/editor/EditorLayout'

export default function Home() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const setData = useEditorStore(state => state.setData)

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        const { ideas, transcript, videoId } = await getLatestVideoData()
        
        if (!ideas || !transcript || !videoId) {
          setError('No video data found. Run the pipeline first.')
          return
        }
        
        setData(ideas, transcript, videoId)
        setLoading(false)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load video data')
        setLoading(false)
      }
    }
    
    loadData()
  }, [setData])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading video data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="text-center max-w-md">
          <h2 className="text-2xl font-bold mb-4">No Video Found</h2>
          <p className="text-muted-foreground mb-4">{error}</p>
          <p className="text-sm text-muted-foreground">
            Run the pipeline to generate video data:
          </p>
          <code className="block mt-2 p-3 bg-muted rounded text-sm">
            python run_pipeline.py "YOUR_YOUTUBE_URL" --mode groq
          </code>
        </div>
      </div>
    )
  }

  return <EditorLayout />
}