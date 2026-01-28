'use client';

import { useState, useRef, useEffect } from 'react';
import { TimeRange } from '@/lib/api/client';

interface TimelineProps {
  currentTime: number;
  duration: number;
  selectedIdeaRanges?: TimeRange[];
  onSeek?: (time: number) => void;
}

export function Timeline({ currentTime, duration, selectedIdeaRanges = [], onSeek }: TimelineProps) {
  const [isDragging, setIsDragging] = useState(false);
  const timelineRef = useRef<HTMLDivElement>(null);

  const getPositionPercent = (time: number) => (time / duration) * 100;

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!onSeek || duration === 0 || !timelineRef.current) return;
    
    const rect = timelineRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percent = Math.max(0, Math.min(1, clickX / rect.width));
    const newTime = percent * duration;
    onSeek(newTime);
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    setIsDragging(true);
    handleSeek(e);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDragging) return;
    handleSeek(e);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Global mouse up listener to handle drag release outside timeline
  useEffect(() => {
    const handleGlobalMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mouseup', handleGlobalMouseUp);
      return () => document.removeEventListener('mouseup', handleGlobalMouseUp);
    }
  }, [isDragging]);

  return (
    <div className="flex h-36 flex-col gap-3 border-t border-border bg-background p-4">
      {/* Ruler / Timeline */}
      <div className="flex items-center gap-2">
        <p className="text-xs font-medium text-muted-foreground w-12">Track</p>
        <div 
          ref={timelineRef}
          className={`relative flex-1 h-5 bg-secondary rounded-sm ${isDragging ? 'cursor-grabbing' : 'cursor-pointer'}`}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
        >
          {[...Array(7)].map((_, i) => (
            <div
              key={i}
              className="absolute top-0 h-full w-px bg-border/50"
              style={{ left: `${(i / 6) * 100}%` }}
            />
          ))}
          <div
            className="absolute top-0 h-full w-0.5 bg-destructive shadow-md z-10"
            style={{ left: `${getPositionPercent(currentTime)}%` }}
          />
        </div>
      </div>

      {/* Video Track with Idea Highlights */}
      <div className="flex items-center gap-2">
        <p className="text-xs font-medium text-muted-foreground w-12">Video</p>
        <div 
          className={`relative flex-1 h-10 rounded-sm bg-secondary border border-border/50 overflow-hidden ${isDragging ? 'cursor-grabbing' : 'cursor-pointer'}`}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
        >
          {/* Full video background */}
          <div className="absolute inset-0 bg-primary/20" />

          {/* Highlighted idea ranges */}
          {selectedIdeaRanges.map((range, index) => (
            <div
              key={index}
              className="absolute h-full bg-primary/60 border-x-2 border-primary hover:bg-primary/80 transition-all"
              style={{
                left: `${getPositionPercent(range.start)}%`,
                right: `${100 - getPositionPercent(range.end)}%`,
              }}
              title={`Idea segment: ${range.start.toFixed(1)}s - ${range.end.toFixed(1)}s`}
            />
          ))}

          {/* Playhead */}
          <div
            className="pointer-events-none absolute top-0 h-full w-0.5 bg-destructive shadow-lg z-10"
            style={{ left: `${getPositionPercent(currentTime)}%` }}
          />
        </div>
      </div>

      {/* Audio Track */}
      <div className="flex items-center gap-2">
        <p className="text-xs font-medium text-muted-foreground w-12">Audio</p>
        <div 
          className={`relative flex-1 h-8 rounded-sm bg-secondary border border-border/50 ${isDragging ? 'cursor-grabbing' : 'cursor-pointer'}`}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
        >
          <div className="absolute inset-0 bg-accent/30" />
          <div
            className="pointer-events-none absolute top-0 h-full w-0.5 bg-destructive z-10"
            style={{ left: `${getPositionPercent(currentTime)}%` }}
          />
        </div>
      </div>

      {/* Time Display */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>{formatTime(currentTime)}</span>
        <span>{formatTime(duration)}</span>
      </div>
    </div>
  );
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
