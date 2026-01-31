'use client';

import React from "react"

import { useState, useCallback, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import { FileUp, Share2, Download, Play, Pause, Volume2, SkipBack, SkipForward } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { TopAppBar } from './editor/top-app-bar';
import { LeftSidebar } from './editor/left-sidebar';
import { VideoPlayer } from './editor/video-player';
import { Timeline } from './editor/timeline';
import { useVideoProcessing } from '@/lib/hooks/use-video-processing';

export function VideoEditor() {
  const searchParams = useSearchParams();
  const projectId = searchParams.get('project');
  
  const [projectName, setProjectName] = useState('Untitled Project');
  const [autoSave, setAutoSave] = useState('All changes saved');
  const [aspectRatio, setAspectRatio] = useState<'16:9' | '9:16'>('16:9');
  const [selectedIdea, setSelectedIdea] = useState<string | null>(null);

  // Single source of truth for playback state
  const [playbackState, setPlaybackState] = useState({
    currentTime: 0,
    isPlaying: false,
    duration: 0
  });

  // Get video processing state from hook - SINGLE SOURCE OF TRUTH
  // Passed to LeftSidebar as props to avoid duplicate hook instances
  const {
    videoId,
    videoUrl,
    videoStreamUrl,
    videoDuration,
    videoTitle,
    status,
    progress,
    currentStage,
    message,
    ideas,
    isLoading,
    isProcessing,
    isComplete,
    error,
    submitVideo,
    reset,
  } = useVideoProcessing(projectId);

  // Update duration when video metadata is available
  const handleDurationChange = useCallback((dur: number) => {
    setPlaybackState(prev => ({ ...prev, duration: dur }));
  }, []);

  // Handle timeline seek
  const handleSeek = useCallback((time: number) => {
    setPlaybackState(prev => ({ ...prev, currentTime: time }));
  }, []);

  // Handle time updates from video player
  const handleTimeUpdate = useCallback((time: number) => {
    setPlaybackState(prev => ({ ...prev, currentTime: time }));
  }, []);

  // Handle play/pause toggle
  const handlePlayPause = useCallback(() => {
    setPlaybackState(prev => ({ ...prev, isPlaying: !prev.isPlaying }));
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
        {/* Left Sidebar - receives all video processing state as props */}
        <LeftSidebar
          selectedIdea={selectedIdea}
          onSelectIdea={setSelectedIdea}
          projectId={projectId}
          videoId={videoId}
          videoStreamUrl={videoStreamUrl}
          status={status}
          progress={progress}
          currentStage={currentStage}
          message={message}
          ideas={ideas}
          isLoading={isLoading}
          isProcessing={isProcessing}
          isComplete={isComplete}
          error={error}
          submitVideo={submitVideo}
          reset={reset}
        />

        {/* Center Workspace */}
        <div className="flex flex-1 flex-col overflow-hidden border-l border-border">
          {/* Video Preview */}
          <div className="flex flex-1 flex-col overflow-hidden border-b border-border bg-secondary/30 p-4">
            <div className={`mx-auto ${aspectRatio === '16:9' ? 'w-full max-w-4xl' : 'w-auto max-h-full'}`}>
              <div className={`relative ${aspectRatio === '16:9' ? 'aspect-video' : 'aspect-[9/16] max-w-md mx-auto'}`}>
                <VideoPlayer
                  videoUrl={videoStreamUrl}
                  currentTime={playbackState.currentTime}
                  isPlaying={playbackState.isPlaying}
                  onTimeUpdate={handleTimeUpdate}
                  onDurationChange={handleDurationChange}
                  onPlayPause={handlePlayPause}
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
              currentTime={playbackState.currentTime}
              duration={playbackState.duration || videoDuration || 0}
              selectedIdeaRanges={selectedIdeaRanges}
              onSeek={handleSeek}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
