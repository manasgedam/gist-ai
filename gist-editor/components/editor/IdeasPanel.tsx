'use client'

import { useEditorStore } from '@/lib/store'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Card } from '@/components/ui/card'
import { Clock, Layers } from 'lucide-react'

export default function IdeasPanel() {
  const ideas = useEditorStore(state => state.ideas)
  const selectedIdeaId = useEditorStore(state => state.selectedIdeaId)
  const selectIdea = useEditorStore(state => state.selectIdea)
  const setCurrentTime = useEditorStore(state => state.setCurrentTime)

  if (!ideas) return null

  const handleIdeaClick = (index: number) => {
    selectIdea(index)
    // Jump to first segment of this idea
    const idea = ideas.ideas[index]
    if (idea.segments.length > 0) {
      setCurrentTime(idea.segments[0].start_seconds)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b">
        <h2 className="font-semibold text-sm">Video Ideas</h2>
        <p className="text-xs text-muted-foreground mt-1">
          Click to preview and edit
        </p>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-3 space-y-2">
          {ideas.ideas.map((idea, index) => (
            <Card
              key={index}
              className={`p-3 cursor-pointer transition-colors hover:bg-accent ${
                selectedIdeaId === String(index) ? 'border-primary bg-accent' : ''
              }`}
              onClick={() => handleIdeaClick(index)}
            >
              <h3 className="font-medium text-sm mb-2 line-clamp-2">
                {idea.title}
              </h3>
              
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Layers className="w-3 h-3" />
                  {idea.segment_count} {idea.segment_count === 1 ? 'segment' : 'segments'}
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {Math.floor(idea.total_duration_seconds)}s
                </div>
              </div>

              {selectedIdeaId === String(index) && (
                <div className="mt-2 pt-2 border-t">
                  <p className="text-xs text-muted-foreground line-clamp-3">
                    {idea.description}
                  </p>
                </div>
              )}
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}