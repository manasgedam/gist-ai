'use client';

import React from "react"

import { useState, useCallback, useMemo } from 'react';
import { FileUp, Share2, Download, Play, Pause, Volume2, SkipBack, SkipForward } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { TopAppBar } from './editor/top-app-bar';
import { LeftSidebar } from './editor/left-sidebar';
import { VideoPlayer } from './editor/video-player';
import { Timeline } from './editor/timeline';
import { useVideoProcessing } from '@/lib/hooks/use-video-processing';

export function VideoEditor() {
  const [projectName, setProjectName] = useState('Untitled Project');
  const [autoSave, setAutoSave] = useState('All changes saved');
  const [aspectRatio, setAspectRatio] = useState<'16:9' | '9:16'>('16:9');
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [selectedIdea, setSelectedIdea] = useState<string | null>(null);

  // Get video processing state from hook (shared with LeftSidebar via re-render)
  const {
    videoStreamUrl,
    videoDuration,
    videoTitle,
    ideas,
    isComplete,
  } = useVideoProcessing();

  // Update duration when video metadata is available
  const handleDurationChange = useCallback((dur: number) => {
    setDuration(dur);
  }, []);

  // Handle timeline seek
  const handleSeek = useCallback((time: number) => {
    setCurrentTime(time);
  }, []);

  // Get time ranges for selected idea
  const selectedIdeaRanges = useMemo(() => {
    if (!selectedIdea) return [];
    const idea = ideas.find(i => i.id === selectedIdea);
    return idea?.time_ranges || [];
  }, [selectedIdea, ideas]);

  // Update project name when video title is available
  if (videoTitle && projectName === 'Untitled Project') {
    setProjectName(videoTitle);
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      {/* Top App Bar */}
      <TopAppBar projectName={projectName} autoSave={autoSave} />

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <LeftSidebar selectedIdea={selectedIdea} onSelectIdea={setSelectedIdea} />

        {/* Center Workspace */}
        <div className="flex flex-1 flex-col overflow-hidden border-l border-border">
          {/* Video Preview */}
          <div className="flex flex-1 flex-col overflow-hidden border-b border-border bg-secondary/30 p-4">
            <div className={`mx-auto ${aspectRatio === '16:9' ? 'w-full max-w-4xl' : 'w-auto max-h-full'}`}>
              <div className={`relative ${aspectRatio === '16:9' ? 'aspect-video' : 'aspect-[9/16] max-w-md mx-auto'}`}>
                <VideoPlayer
                  videoUrl={videoStreamUrl}
                  currentTime={currentTime}
                  onTimeUpdate={setCurrentTime}
                  onDurationChange={handleDurationChange}
                  className="w-full h-full"
                />
              </div>
            </div>

            {/* Aspect Ratio Controls */}
            <div className="flex justify-center gap-2 mt-4">
              <Button
                size="sm"
                variant={aspectRatio === '16:9' ? 'default' : 'outline'}
                onClick={() => setAspectRatio('16:9')}
                className="text-xs h-8"
              >
                16:9
              </Button>
              <Button
                size="sm"
                variant={aspectRatio === '9:16' ? 'default' : 'outline'}
                onClick={() => setAspectRatio('9:16')}
                className="text-xs h-8"
              >
                9:16
              </Button>
            </div>
          </div>

          {/* Timeline */}
          <div className="flex-shrink-0 border-t border-border bg-background">
            <Timeline
              currentTime={currentTime}
              duration={duration || videoDuration || 0}
              selectedIdeaRanges={selectedIdeaRanges}
              onSeek={handleSeek}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
