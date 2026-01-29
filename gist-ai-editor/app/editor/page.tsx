'use client'

import { useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { VideoEditor } from '@/components/video-editor'

export default function EditorPage() {
  const searchParams = useSearchParams()
  const projectId = searchParams.get('project')

  useEffect(() => {
    // If this is a new project (no project_id), clear any stale localStorage
    // This ensures we show the upload form instead of old processing state
    if (!projectId) {
      const STORAGE_KEY = 'gist-ai-video-processing'
      const stored = localStorage.getItem(STORAGE_KEY)
      
      if (stored) {
        console.log('🧹 Clearing stale video processing state for new project')
        localStorage.removeItem(STORAGE_KEY)
        // Force a page reload to reset the VideoEditor state
        window.location.reload()
      }
    }
  }, [projectId])

  return <VideoEditor />
}
