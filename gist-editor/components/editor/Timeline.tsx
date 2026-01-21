'use client'

import { useRef, useEffect, useState } from 'react'
import { useEditorStore } from '@/lib/store'

export default function Timeline() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [canvasSize, setCanvasSize] = useState({ width: 0, height: 0 })
  
  const ideas = useEditorStore(state => state.ideas)
  const selectedIdeaId = useEditorStore(state => state.selectedIdeaId)
  const currentTime = useEditorStore(state => state.currentTime)
  const setCurrentTime = useEditorStore(state => state.setCurrentTime)
  const zoom = useEditorStore(state => state.zoom)

  // Resize canvas to match container
  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect()
        setCanvasSize({ width, height })
      }
    }
    
    updateSize()
    window.addEventListener('resize', updateSize)
    return () => window.removeEventListener('resize', updateSize)
  }, [])

  // Draw timeline
  useEffect(() => {
    if (!canvasRef.current || !ideas) return
    
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const { width, height } = canvasSize
    const duration = ideas.total_duration
    const pixelsPerSecond = (width - 40) / duration * zoom
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height)
    
    // Draw time markers
    ctx.fillStyle = '#64748b'
    ctx.font = '10px sans-serif'
    const timeInterval = Math.max(10, Math.floor(30 / zoom))
    for (let t = 0; t <= duration; t += timeInterval) {
      const x = 20 + t * pixelsPerSecond
      ctx.fillText(formatTime(t), x, 15)
      ctx.fillRect(x, 20, 1, 5)
    }
    
    // Draw all ideas as light gray blocks
    ideas.ideas.forEach((idea, ideaIndex) => {
      const isSelected = selectedIdeaId === String(ideaIndex)
      
      idea.segments.forEach((segment) => {
        const x = 20 + segment.start_seconds * pixelsPerSecond
        const w = segment.duration_seconds * pixelsPerSecond
        
        // Background block
        ctx.fillStyle = isSelected ? '#3b82f620' : '#e2e8f010'
        ctx.fillRect(x, 30, w, height - 60)
        
        // Border
        ctx.strokeStyle = isSelected ? '#3b82f6' : '#cbd5e1'
        ctx.lineWidth = isSelected ? 2 : 1
        ctx.strokeRect(x, 30, w, height - 60)
        
        // Label (only if selected)
        if (isSelected && w > 50) {
          ctx.fillStyle = '#3b82f6'
          ctx.font = '11px sans-serif'
          ctx.fillText(
            segment.purpose.slice(0, 20),
            x + 4,
            45
          )
        }
      })
    })
    
    // Draw playhead
    const playheadX = 20 + currentTime * pixelsPerSecond
    ctx.strokeStyle = '#ef4444'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(playheadX, 20)
    ctx.lineTo(playheadX, height - 30)
    ctx.stroke()
    
    // Playhead triangle
    ctx.fillStyle = '#ef4444'
    ctx.beginPath()
    ctx.moveTo(playheadX, 20)
    ctx.lineTo(playheadX - 5, 12)
    ctx.lineTo(playheadX + 5, 12)
    ctx.closePath()
    ctx.fill()
    
  }, [canvasSize, ideas, selectedIdeaId, currentTime, zoom])

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!ideas) return
    
    const canvas = canvasRef.current
    if (!canvas) return
    
    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const duration = ideas.total_duration
    const pixelsPerSecond = (canvasSize.width - 40) / duration * zoom
    
    const clickedTime = (x - 20) / pixelsPerSecond
    setCurrentTime(Math.max(0, Math.min(duration, clickedTime)))
  }

  return (
    <div ref={containerRef} className="w-full h-full relative bg-background">
      <canvas
        ref={canvasRef}
        width={canvasSize.width}
        height={canvasSize.height}
        onClick={handleClick}
        className="cursor-pointer"
      />
      
      <div className="absolute bottom-2 right-2 text-xs text-muted-foreground">
        {formatTime(currentTime)} / {formatTime(ideas?.total_duration || 0)}
      </div>
    </div>
  )
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${String(secs).padStart(2, '0')}`
}