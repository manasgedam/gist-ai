'use client'

import { useEditorStore } from '@/lib/store'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Trash2, Save, Play } from 'lucide-react'
import { useState } from 'react'

export default function SegmentEditor() {
  const ideas = useEditorStore(state => state.ideas)
  const selectedIdeaId = useEditorStore(state => state.selectedIdeaId)
  const editableSegments = useEditorStore(state => state.editableSegments)
  const selectedSegmentId = useEditorStore(state => state.selectedSegmentId)
  const selectSegment = useEditorStore(state => state.selectSegment)
  const updateSegment = useEditorStore(state => state.updateSegment)
  const deleteSegment = useEditorStore(state => state.deleteSegment)
  const applyEditsToIdea = useEditorStore(state => state.applyEditsToIdea)
  const setCurrentTime = useEditorStore(state => state.setCurrentTime)
  const setIsPlaying = useEditorStore(state => state.setIsPlaying)

  if (!ideas || selectedIdeaId === null) return null

  const idea = ideas.ideas[parseInt(selectedIdeaId)]
  const hasChanges = editableSegments.length !== idea.segments.length ||
    editableSegments.some((seg, idx) => {
      const original = idea.segments[idx]
      return !original || 
        seg.start_seconds !== original.start_seconds ||
        seg.end_seconds !== original.end_seconds
    })

  const handlePreviewSegment = (segmentId: string) => {
    const segment = editableSegments.find(s => s.id === segmentId)
    if (segment) {
      setCurrentTime(segment.start_seconds)
      setIsPlaying(true)
    }
  }

  const handleSave = () => {
    applyEditsToIdea()
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b">
        <h2 className="font-semibold text-sm mb-2">Edit Segments</h2>
        <p className="text-xs text-muted-foreground">
          {idea.title}
        </p>
        {hasChanges && (
          <Button 
            size="sm" 
            className="mt-3 w-full"
            onClick={handleSave}
          >
            <Save className="w-3 h-3 mr-2" />
            Save Changes
          </Button>
        )}
      </div>

      <ScrollArea className="flex-1">
        <div className="p-3 space-y-3">
          {editableSegments.map((segment, index) => (
            <SegmentCard
              key={segment.id}
              segment={segment}
              index={index}
              isSelected={selectedSegmentId === segment.id}
              onSelect={() => selectSegment(segment.id)}
              onUpdate={(changes) => updateSegment(segment.id, changes)}
              onDelete={() => deleteSegment(segment.id)}
              onPreview={() => handlePreviewSegment(segment.id)}
            />
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}

function SegmentCard({
  segment,
  index,
  isSelected,
  onSelect,
  onUpdate,
  onDelete,
  onPreview
}: {
  segment: any
  index: number
  isSelected: boolean
  onSelect: () => void
  onUpdate: (changes: any) => void
  onDelete: () => void
  onPreview: () => void
}) {
  const [startTime, setStartTime] = useState(formatTime(segment.start_seconds))
  const [endTime, setEndTime] = useState(formatTime(segment.end_seconds))

  const handleStartChange = (value: string) => {
    setStartTime(value)
    const seconds = parseTime(value)
    if (!isNaN(seconds)) {
      onUpdate({ start_seconds: seconds })
    }
  }

  const handleEndChange = (value: string) => {
    setEndTime(value)
    const seconds = parseTime(value)
    if (!isNaN(seconds)) {
      onUpdate({ end_seconds: seconds })
    }
  }

  return (
    <Card
      className={`p-3 cursor-pointer transition-colors ${
        isSelected ? 'border-primary bg-accent' : ''
      }`}
      onClick={onSelect}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <div className="text-xs font-medium text-muted-foreground mb-1">
            Segment {index + 1}
          </div>
          <div className="text-xs text-muted-foreground line-clamp-2">
            {segment.purpose}
          </div>
        </div>
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={(e) => {
              e.stopPropagation()
              onPreview()
            }}
          >
            <Play className="w-3 h-3" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 text-destructive"
            onClick={(e) => {
              e.stopPropagation()
              onDelete()
            }}
          >
            <Trash2 className="w-3 h-3" />
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mt-2">
        <div>
          <label className="text-xs text-muted-foreground">Start</label>
          <Input
            value={startTime}
            onChange={(e) => handleStartChange(e.target.value)}
            className="h-7 text-xs"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground">End</label>
          <Input
            value={endTime}
            onChange={(e) => handleEndChange(e.target.value)}
            className="h-7 text-xs"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      </div>

      <div className="text-xs text-muted-foreground mt-2">
        Duration: {segment.duration_seconds.toFixed(1)}s
      </div>
    </Card>
  )
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 10)
  return `${mins}:${String(secs).padStart(2, '0')}.${ms}`
}

function parseTime(timeStr: string): number {
  const parts = timeStr.split(':')
  if (parts.length !== 2) return NaN
  
  const mins = parseInt(parts[0])
  const secsAndMs = parts[1].split('.')
  const secs = parseInt(secsAndMs[0])
  const ms = secsAndMs[1] ? parseInt(secsAndMs[1]) / 10 : 0
  
  return mins * 60 + secs + ms
}