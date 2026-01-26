'use client';

import React from "react"

import { useState, useCallback } from 'react';
import { FileUp, Share2, Download, Play, Pause, Volume2, SkipBack, SkipForward } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { TopAppBar } from './editor/top-app-bar';
import { LeftSidebar } from './editor/left-sidebar';
import { VideoPreview } from './editor/video-preview';
import { Timeline } from './editor/timeline';

export function VideoEditor() {
  const [projectName, setProjectName] = useState('Untitled Project');
  const [autoSave, setAutoSave] = useState('All changes saved');
  const [isPlaying, setIsPlaying] = useState(false);
  const [aspectRatio, setAspectRatio] = useState<'16:9' | '9:16'>('16:9');
  const [currentTime, setCurrentTime] = useState(0);
  const [duration] = useState(120); // 2 minutes
  const [selectedIdea, setSelectedIdea] = useState<string | null>(null);
  const [volume, setVolume] = useState(80);

  const handlePlayPause = useCallback(() => {
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  const handleSkipBack = useCallback(() => {
    setCurrentTime(Math.max(0, currentTime - 5));
  }, [currentTime]);

  const handleSkipForward = useCallback(() => {
    setCurrentTime(Math.min(duration, currentTime + 5));
  }, [currentTime, duration]);

  const handleTimelineClick = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setCurrentTime(Number(e.target.value));
  }, []);

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
          <div className="flex flex-1 flex-col overflow-hidden border-b border-border bg-secondary">
            <VideoPreview aspectRatio={aspectRatio} />

            {/* Playback Controls */}
            <div className="flex items-center justify-between gap-4 border-t border-border bg-background px-6 py-3">
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleSkipBack}
                  title="Skip back 5 seconds"
                  className="h-8 w-8 p-0 bg-transparent"
                >
                  <SkipBack className="h-4 w-4" />
                </Button>

                <Button
                  size="sm"
                  variant="default"
                  onClick={handlePlayPause}
                  title={isPlaying ? 'Pause' : 'Play'}
                  className="h-8 w-8 p-0"
                >
                  {isPlaying ? (
                    <Pause className="h-4 w-4" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                </Button>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleSkipForward}
                  title="Skip forward 5 seconds"
                  className="h-8 w-8 p-0 bg-transparent"
                >
                  <SkipForward className="h-4 w-4" />
                </Button>
              </div>

              <div className="flex items-center gap-2 text-sm text-muted-foreground font-mono">
                <span>{String(Math.floor(currentTime / 60)).padStart(2, '0')}:{String(Math.floor(currentTime % 60)).padStart(2, '0')}</span>
                <span className="text-muted-foreground/50">/</span>
                <span>{String(Math.floor(duration / 60)).padStart(2, '0')}:{String(Math.floor(duration % 60)).padStart(2, '0')}</span>
              </div>

              <div className="flex-1 max-w-xs">
                <input
                  type="range"
                  min="0"
                  max={duration}
                  value={currentTime}
                  onChange={handleTimelineClick}
                  className="h-1 w-full cursor-pointer accent-primary"
                  title={`${currentTime}s`}
                />
              </div>

              <div className="flex items-center gap-2 border-l border-border pl-4">
                <Volume2 className="h-4 w-4 text-muted-foreground" />
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={volume}
                  onChange={(e) => setVolume(Number(e.target.value))}
                  className="w-20 h-1 cursor-pointer accent-primary"
                  title={`Volume: ${volume}%`}
                />
              </div>

              <div className="flex gap-1 border-l border-border pl-4">
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
          </div>

          {/* Timeline */}
          <div className="flex-shrink-0 border-t border-border bg-background">
            <Timeline currentTime={currentTime} duration={duration} />
          </div>
        </div>
      </div>
    </div>
  );
}
