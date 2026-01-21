'use client'

import { useEditorStore } from '@/lib/store'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Play, Pause, SkipBack, SkipForward, ZoomIn, ZoomOut, Subtitles } from 'lucide-react'

export default function Controls() {
  const isPlaying = useEditorStore(state => state.isPlaying)
  const setIsPlaying = useEditorStore(state => state.setIsPlaying)
  const currentTime = useEditorStore(state => state.currentTime)
  const setCurrentTime = useEditorStore(state => state.setCurrentTime)
  const zoom = useEditorStore(state => state.zoom)
  const setZoom = useEditorStore(state => state.setZoom)
  const showSubtitles = useEditorStore(state => state.showSubtitles)
  const toggleSubtitles = useEditorStore(state => state.toggleSubtitles)
  const ideas = useEditorStore(state => state.ideas)

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying)
  }

  const handleSkipBackward = () => {
    setCurrentTime(Math.max(0, currentTime - 5))
  }

  const handleSkipForward = () => {
    const maxTime = ideas?.total_duration || 0
    setCurrentTime(Math.min(maxTime, currentTime + 5))
  }

  const handleZoomIn = () => {
    setZoom(Math.min(3, zoom + 0.25))
  }

  const handleZoomOut = () => {
    setZoom(Math.max(0.5, zoom - 0.25))
  }

  return (
    <div className="h-full flex items-center justify-between px-4">
      {/* Playback controls */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={handleSkipBackward}
          title="Skip backward 5s"
        >
          <SkipBack className="w-4 h-4" />
        </Button>
        
        <Button
          variant="default"
          size="icon"
          onClick={handlePlayPause}
          title={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
        </Button>
        
        <Button
          variant="ghost"
          size="icon"
          onClick={handleSkipForward}
          title="Skip forward 5s"
        >
          <SkipForward className="w-4 h-4" />
        </Button>
        
        <div className="h-6 w-px bg-border mx-1" />
        
        <Button
          variant={showSubtitles ? "default" : "ghost"}
          size="icon"
          onClick={toggleSubtitles}
          title={showSubtitles ? 'Hide subtitles' : 'Show subtitles'}
        >
          <Subtitles className="w-4 h-4" />
        </Button>
      </div>

      {/* Time display */}
      <div className="text-sm text-muted-foreground">
        {formatTime(currentTime)} / {formatTime(ideas?.total_duration || 0)}
      </div>

      {/* Zoom controls */}
      <div className="flex items-center gap-3">
        <span className="text-xs text-muted-foreground">Zoom</span>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleZoomOut}
          disabled={zoom <= 0.5}
          title="Zoom out"
        >
          <ZoomOut className="w-4 h-4" />
        </Button>
        
        <div className="w-24">
          <Slider
            value={[zoom]}
            onValueChange={([value]) => setZoom(value)}
            min={0.5}
            max={3}
            step={0.25}
          />
        </div>
        
        <Button
          variant="ghost"
          size="icon"
          onClick={handleZoomIn}
          disabled={zoom >= 3}
          title="Zoom in"
        >
          <ZoomIn className="w-4 h-4" />
        </Button>
        
        <span className="text-xs text-muted-foreground w-8">
          {zoom.toFixed(1)}x
        </span>
      </div>
    </div>
  )
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${String(secs).padStart(2, '0')}`
}