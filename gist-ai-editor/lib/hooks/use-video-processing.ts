import { useState, useEffect, useCallback, useRef } from 'react';
import { videoApi, Idea, StatusResponse } from '../api/client';

export interface UseVideoProcessingReturn {
  // State
  videoId: string | null;
  videoUrl: string | null;
  videoStreamUrl: string | null;
  videoDuration: number | null;
  videoTitle: string | null;
  status: string | null;
  progress: number;
  currentStage: string | null;
  message: string | null;
  ideas: Idea[];
  isProcessing: boolean;
  isComplete: boolean;
  error: string | null;

  // Actions
  submitVideo: (url: string, mode?: string) => Promise<void>;
  reset: () => void;
}

const STORAGE_KEY = 'gist-ai-video-processing';

interface PersistedState {
  videoId: string;
  videoUrl: string;
  status: string;
  progress: number;
  currentStage: string;
  timestamp: number;
}

export function useVideoProcessing(): UseVideoProcessingReturn {
  const [videoId, setVideoId] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [videoStreamUrl, setVideoStreamUrl] = useState<string | null>(null);
  const [videoDuration, setVideoDuration] = useState<number | null>(null);
  const [videoTitle, setVideoTitle] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [currentStage, setCurrentStage] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // CRITICAL FIX: Use ref to store videoId so WebSocket handler always has latest value
  const videoIdRef = useRef<string | null>(null);
  
  // Keep videoIdRef in sync with videoId state
  useEffect(() => {
    videoIdRef.current = videoId;
  }, [videoId]);

  const isProcessing = status !== null && status !== 'COMPLETE' && status !== 'FAILED';
  const isComplete = status === 'COMPLETE';

  // Save state to localStorage whenever it changes
  useEffect(() => {
    if (videoId && status && status !== 'COMPLETE' && status !== 'FAILED') {
      const state: PersistedState = {
        videoId,
        videoUrl: videoUrl || '',
        status,
        progress,
        currentStage: currentStage || '',
        timestamp: Date.now(),
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } else if (status === 'COMPLETE' || status === 'FAILED') {
      // Clear storage when processing is done
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [videoId, videoUrl, status, progress, currentStage]);

  // Restore state from localStorage on mount
  useEffect(() => {
    const restoreState = async () => {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) return;

      try {
        const state: PersistedState = JSON.parse(stored);
        
        // Only restore if less than 24 hours old
        const age = Date.now() - state.timestamp;
        if (age > 24 * 60 * 60 * 1000) {
          localStorage.removeItem(STORAGE_KEY);
          return;
        }

        console.log('🔄 Restoring video processing state:', state.videoId);
        
        // Restore state
        setVideoId(state.videoId);
        videoIdRef.current = state.videoId;
        setVideoUrl(state.videoUrl);
        setStatus(state.status);
        setProgress(state.progress);
        setCurrentStage(state.currentStage);
        setMessage('Reconnecting to video processing...');

        // Fetch current status from server
        try {
          const statusResponse = await videoApi.getVideoStatus(state.videoId);
          setStatus(statusResponse.status);
          setProgress(statusResponse.progress);
          setCurrentStage(statusResponse.current_stage);
          setMessage(statusResponse.message);

          // If complete, fetch ideas and metadata
          if (statusResponse.status === 'COMPLETE') {
            const ideasResponse = await videoApi.getVideoIdeas(state.videoId);
            setIdeas(ideasResponse.ideas);
            
            const timeline = await videoApi.getVideoTimeline(state.videoId);
            setVideoStreamUrl(timeline.video_url);
            setVideoDuration(timeline.duration);
            setVideoTitle(timeline.title);
            
            localStorage.removeItem(STORAGE_KEY);
          } else if (statusResponse.status === 'FAILED') {
            setError('Processing failed');
            localStorage.removeItem(STORAGE_KEY);
          } else {
            // Still processing - reconnect WebSocket and start polling
            try {
              wsRef.current = videoApi.connectWebSocket(state.videoId, handleWebSocketMessage);
            } catch (wsError) {
              console.warn('WebSocket reconnection failed:', wsError);
            }

            // Start polling
            pollingIntervalRef.current = setInterval(() => {
              pollStatus(state.videoId);
            }, 2000);
          }
        } catch (err) {
          console.error('Failed to restore video state:', err);
          localStorage.removeItem(STORAGE_KEY);
        }
      } catch (err) {
        console.error('Failed to parse stored state:', err);
        localStorage.removeItem(STORAGE_KEY);
      }
    };

    restoreState();
  }, []); // Only run on mount

  // Fetch video metadata when video ID is available
  const fetchVideoMetadata = useCallback(async (vid: string) => {
    try {
      const timeline = await videoApi.getVideoTimeline(vid);
      setVideoStreamUrl(timeline.video_url);
      setVideoDuration(timeline.duration);
      setVideoTitle(timeline.title);
    } catch (err) {
      console.error('Failed to fetch video metadata:', err);
    }
  }, []);

  // CRITICAL FIX: Define WebSocket handler that reads from ref, not closure
  const handleWebSocketMessage = useCallback((messageData: any) => {
    console.log('🔔 WebSocket message received:', messageData);
    
    // Use ref to get current videoId (avoids stale closure)
    const currentVideoId = videoIdRef.current;

    switch (messageData.type) {
      case 'progress':
        console.log('✅ Processing progress update:', messageData.stage, messageData.progress + '%');
        setStatus(messageData.stage);
        setProgress(messageData.progress || 0);
        setCurrentStage(messageData.stage);
        setMessage(messageData.message);
        break;

      case 'video_ready':
        console.log('📹 Video ready event received');
        if (currentVideoId) {
          fetchVideoMetadata(currentVideoId);
        }
        setMessage(messageData.message || 'Video ready for playback');
        break;

      case 'stage_complete':
        console.log('✅ Stage complete:', messageData.current_stage, '→', messageData.next_stage);
        setCurrentStage(messageData.next_stage);
        setStatus(messageData.next_stage);
        break;

      case 'complete':
        console.log('🎉 Processing complete!');
        setStatus('COMPLETE');
        setProgress(100);
        setMessage(messageData.message);
        setCurrentStage('COMPLETE');
        if (currentVideoId) {
          videoApi.getVideoIdeas(currentVideoId).then((response) => {
            setIdeas(response.ideas);
          }).catch((err) => {
            console.error('Failed to fetch ideas:', err);
          });
          fetchVideoMetadata(currentVideoId);
        }
        break;

      case 'error':
        console.error('❌ Processing error:', messageData.message);
        setStatus('FAILED');
        setError(messageData.message || 'Processing failed');
        setMessage(messageData.message);
        break;
    }
  }, [fetchVideoMetadata]); // Only depends on stable fetchVideoMetadata

  // Poll for status updates (fallback if WebSocket fails)
  const pollStatus = useCallback(async (vid: string) => {
    try {
      const statusResponse = await videoApi.getVideoStatus(vid);
      setStatus(statusResponse.status);
      setProgress(statusResponse.progress);
      setCurrentStage(statusResponse.current_stage);
      setMessage(statusResponse.message);

      // Fetch video metadata early when transcribing starts
      if (statusResponse.current_stage === 'TRANSCRIBING') {
        setVideoStreamUrl((currentUrl) => {
          if (!currentUrl) {
            fetchVideoMetadata(vid);
          }
          return currentUrl;
        });
      }

      // If complete, fetch ideas and metadata
      if (statusResponse.status === 'COMPLETE') {
        const ideasResponse = await videoApi.getVideoIdeas(vid);
        setIdeas(ideasResponse.ideas);
        fetchVideoMetadata(vid);
        
        // Stop polling
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      } else if (statusResponse.status === 'FAILED') {
        setError('Processing failed');
        
        // Stop polling
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      }
    } catch (err) {
      console.error('Failed to poll status:', err);
    }
  }, [fetchVideoMetadata]);

  // Submit video for processing
  const submitVideo = useCallback(async (url: string, mode: string = 'groq') => {
    try {
      // Reset previous state
      setError(null);
      setProgress(0);
      setIdeas([]);
      setVideoStreamUrl(null);
      setVideoDuration(null);
      setVideoTitle(null);
      
      setVideoUrl(url);
      setStatus('PENDING');
      setCurrentStage('PENDING');
      setMessage('Submitting video...');

      const response = await videoApi.submitYouTubeUrl(url, mode);
      
      // CRITICAL: Set videoId in BOTH state and ref before connecting WebSocket
      setVideoId(response.video_id);
      videoIdRef.current = response.video_id;
      
      setStatus(response.status);
      setMessage(response.message);

      // Connect WebSocket AFTER videoIdRef is set
      try {
        wsRef.current = videoApi.connectWebSocket(response.video_id, handleWebSocketMessage);
      } catch (wsError) {
        console.warn('WebSocket connection failed, falling back to polling:', wsError);
      }

      // Start polling as fallback
      pollingIntervalRef.current = setInterval(() => {
        pollStatus(response.video_id);
      }, 2000);

    } catch (err: any) {
      setError(err.message || 'Failed to submit video');
      setStatus('FAILED');
    }
  }, [handleWebSocketMessage, pollStatus]);

  // Reset state
  const reset = useCallback(() => {
    setVideoId(null);
    videoIdRef.current = null;
    setVideoUrl(null);
    setVideoStreamUrl(null);
    setVideoDuration(null);
    setVideoTitle(null);
    setStatus(null);
    setProgress(0);
    setCurrentStage(null);
    setMessage(null);
    setIdeas([]);
    setError(null);

    // Clean up WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Clean up polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    // Clear localStorage
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  return {
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
    isProcessing,
    isComplete,
    error,
    submitVideo,
    reset,
  };
}
