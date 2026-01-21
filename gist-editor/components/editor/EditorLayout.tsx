'use client'

import { useEditorStore } from '@/lib/store'
import IdeasPanel from './IdeasPanel'
import VideoPreview from './VideoPreview'
import Timeline from './Timeline'
import Controls from './Controls'
import SegmentEditor from './SegmentEditor'
import { Separator } from '@/components/ui/separator'

export default function EditorLayout() {
  const ideas = useEditorStore(state => state.ideas)
  const videoId = useEditorStore(state => state.videoId)
  const selectedIdeaId = useEditorStore(state => state.selectedIdeaId)

  if (!ideas || !videoId) {
    return null
  }

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <div className="h-14 border-b flex items-center px-4">
        <h1 className="text-lg font-semibold">Gist AI Editor</h1>
        <div className="ml-4 text-sm text-muted-foreground">
          {ideas.ideas_count} ideas • {Math.floor(ideas.total_duration / 60)}:{String(Math.floor(ideas.total_duration % 60)).padStart(2, '0')} total
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left sidebar - Ideas list */}
        <div className="w-80 border-r flex flex-col">
          <IdeasPanel />
        </div>

        {/* Center - Video preview and timeline */}
        <div className="flex-1 flex flex-col">
          {/* Video preview */}
          <div className="flex-1 bg-black flex items-center justify-center p-4">
            <VideoPreview />
          </div>

          <Separator />

          {/* Controls */}
          <div className="h-16 border-t">
            <Controls />
          </div>

          {/* Timeline */}
          <div className="h-48 border-t bg-muted/30">
            <Timeline />
          </div>
        </div>

        {/* Right sidebar - Segment editor (shows when idea selected) */}
        {selectedIdeaId !== null && (
          <div className="w-80 border-l flex flex-col">
            <SegmentEditor />
          </div>
        )}
      </div>
    </div>
  )
}