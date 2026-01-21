'use client'

import { useEffect, useRef, useState } from 'react'
import { useEditorStore } from '@/lib/store'
import { getVideoUrl } from '@/lib/video-loader'

export default function VideoPreview() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const videoId = useEditorStore(state => state.videoId)
  const transcript = useEditorStore(state => state.transcript)
  const currentTime = useEditorStore(state => state.currentTime)
  const isPlaying = useEditorStore(state => state.isPlaying)
  const showSubtitles = useEditorStore(state => state.showSubtitles)
  const setCurrentTime = useEditorStore(state => state.setCurrentTime)
  const setIsPlaying = useEditorStore(state => state.setIsPlaying)
  
  const [currentSubtitle, setCurrentSubtitle] = useState<string>('')

  // Sync video time with store
  useEffect(() => {
    if (videoRef.current && Math.abs(videoRef.current.currentTime - currentTime) > 0.5) {
      videoRef.current.currentTime = currentTime
    }
  }, [currentTime])

  // Sync play/pause with store
  useEffect(() => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.play().catch(() => setIsPlaying(false))
      } else {
        videoRef.current.pause()
      }
    }
  }, [isPlaying, setIsPlaying])

  // Update subtitles based on current time
  useEffect(() => {
    if (!transcript || !showSubtitles) {
      setCurrentSubtitle('')
      return
    }

    const segment = transcript.segments.find(
      seg => currentTime >= seg.start && currentTime <= seg.end
    )
    
    setCurrentSubtitle(segment?.text || '')
  }, [currentTime, transcript, showSubtitles])

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime)
    }
  }

  const handleEnded = () => {
    setIsPlaying(false)
  }

  if (!videoId) return null

  return (
    <div className="relative w-full h-full flex items-center justify-center">
      <video
        ref={videoRef}
        src={getVideoUrl(videoId)}
        className="max-w-full max-h-full rounded-lg shadow-2xl"
        onTimeUpdate={handleTimeUpdate}
        onEnded={handleEnded}
        onPause={() => setIsPlaying(false)}
        onPlay={() => setIsPlaying(true)}
      />
      
      {/* Subtitles overlay */}
      {showSubtitles && currentSubtitle && (
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 max-w-[80%] px-4 py-2 bg-black/80 text-white text-center rounded-lg backdrop-blur-sm">
          <p className="text-sm md:text-base font-medium leading-relaxed">
            {currentSubtitle}
          </p>
        </div>
      )}
    </div>
  )
}