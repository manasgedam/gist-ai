'use client';

import { useRef, useEffect, useState } from 'react';
import { Play, Pause, Volume2, VolumeX, Maximize2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface VideoPlayerProps {
  videoUrl: string | null;
  currentTime: number;
  isPlaying: boolean;
  onTimeUpdate: (time: number) => void;
  onDurationChange: (duration: number) => void;
  onPlayPause: () => void;
  className?: string;
}

export function VideoPlayer({
  videoUrl,
  currentTime,
  isPlaying,
  onTimeUpdate,
  onDurationChange,
  onPlayPause,
  className = '',
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const seekingRef = useRef(false);
  const [volume, setVolume] = useState(80);
  const [isMuted, setIsMuted] = useState(false);

  // Controlled playback - sync isPlaying prop with video element
  useEffect(() => {
    if (!videoRef.current) return;

    if (isPlaying) {
      videoRef.current.play().catch(err => {
        console.error('Play failed:', err);
      });
    } else {
      videoRef.current.pause();
    }
  }, [isPlaying]);

  // Controlled seeking - sync currentTime prop with video element
  useEffect(() => {
    if (!videoRef.current) return;

    const diff = Math.abs(videoRef.current.currentTime - currentTime);
    // Reduced threshold from 0.5s to 0.1s for better precision
    if (diff > 0.1) {
      seekingRef.current = true;
      videoRef.current.currentTime = currentTime;
    }
  }, [currentTime]);

  // Handle video metadata loaded
  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      const dur = videoRef.current.duration;
      onDurationChange(dur);
    }
  };

  // Handle time update - prevent feedback loop
  const handleTimeUpdate = () => {
    if (!videoRef.current || seekingRef.current) {
      seekingRef.current = false;
      return;
    }
    onTimeUpdate(videoRef.current.currentTime);
  };

  // Volume control
  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseInt(e.target.value);
    setVolume(newVolume);
    if (videoRef.current) {
      videoRef.current.volume = newVolume / 100;
      if (newVolume > 0) {
        setIsMuted(false);
      }
    }
  };

  // Mute toggle
  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  // Fullscreen
  const toggleFullscreen = () => {
    if (videoRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        videoRef.current.requestFullscreen();
      }
    }
  };

  if (!videoUrl) {
    return (
      <div className={`flex items-center justify-center bg-secondary/30 rounded-lg ${className}`}>
        <div className="text-center p-8">
          <Play className="h-12 w-12 text-muted-foreground/50 mx-auto mb-3" />
          <p className="text-sm font-medium text-muted-foreground">No video loaded</p>
          <p className="text-xs text-muted-foreground/60 mt-1">Upload a video to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative group ${className}`}>
      <video
        ref={videoRef}
        src={videoUrl}
        className="w-full h-full rounded-lg bg-black"
        onLoadedMetadata={handleLoadedMetadata}
        onTimeUpdate={handleTimeUpdate}
      />

      {/* Video Controls Overlay */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 opacity-0 group-hover:opacity-100 transition-opacity">
        <div className="flex items-center gap-3">
          {/* Play/Pause */}
          <Button
            size="sm"
            variant="ghost"
            className="text-white hover:bg-white/20"
            onClick={onPlayPause}
          >
            {isPlaying ? (
              <Pause className="h-4 w-4" />
            ) : (
              <Play className="h-4 w-4" />
            )}
          </Button>

          {/* Volume */}
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="ghost"
              className="text-white hover:bg-white/20"
              onClick={toggleMute}
            >
              {isMuted || volume === 0 ? (
                <VolumeX className="h-4 w-4" />
              ) : (
                <Volume2 className="h-4 w-4" />
              )}
            </Button>
            <input
              type="range"
              min="0"
              max="100"
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              className="w-20 h-1 bg-white/30 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          <div className="flex-1" />

          {/* Fullscreen */}
          <Button
            size="sm"
            variant="ghost"
            className="text-white hover:bg-white/20"
            onClick={toggleFullscreen}
          >
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
