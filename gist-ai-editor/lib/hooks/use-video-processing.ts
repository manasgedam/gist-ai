import { useState, useEffect, useCallback, useRef } from 'react';
import { videoApi, Idea, StatusResponse } from '../api/client';

export interface UseVideoProcessingReturn {
  // State
  videoId: string | null;
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

export function useVideoProcessing(): UseVideoProcessingReturn {
  const [videoId, setVideoId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [currentStage, setCurrentStage] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const isProcessing = status !== null && status !== 'COMPLETE' && status !== 'FAILED';
  const isComplete = status === 'COMPLETE';

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: any) => {
    console.log('WebSocket message:', message);

    switch (message.type) {
      case 'progress':
        setStatus(message.stage);
        setProgress(message.progress || 0);
        setCurrentStage(message.stage);
        setMessage(message.message);
        break;

      case 'stage_complete':
        setCurrentStage(message.next_stage);
        break;

      case 'complete':
        setStatus('COMPLETE');
        setProgress(100);
        setMessage(message.message);
        // Fetch ideas
        if (videoId) {
          videoApi.getVideoIdeas(videoId).then((response) => {
            setIdeas(response.ideas);
          }).catch((err) => {
            console.error('Failed to fetch ideas:', err);
          });
        }
        break;

      case 'error':
        setStatus('FAILED');
        setError(message.message || 'Processing failed');
        setMessage(message.message);
        break;
    }
  }, [videoId]);

  // Poll for status updates (fallback if WebSocket fails)
  const pollStatus = useCallback(async (vid: string) => {
    try {
      const statusResponse = await videoApi.getVideoStatus(vid);
      setStatus(statusResponse.status);
      setProgress(statusResponse.progress);
      setCurrentStage(statusResponse.current_stage);
      setMessage(statusResponse.message);

      // If complete, fetch ideas
      if (statusResponse.status === 'COMPLETE') {
        const ideasResponse = await videoApi.getVideoIdeas(vid);
        setIdeas(ideasResponse.ideas);
        
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
  }, []);

  // Submit video for processing
  const submitVideo = useCallback(async (url: string, mode: string = 'groq') => {
    try {
      setError(null);
      setProgress(0);
      setStatus('PENDING');
      setMessage('Submitting video...');

      const response = await videoApi.submitYouTubeUrl(url, mode);
      setVideoId(response.video_id);
      setStatus(response.status);
      setMessage(response.message);

      // Connect WebSocket
      try {
        wsRef.current = videoApi.connectWebSocket(response.video_id, handleWebSocketMessage);
      } catch (wsError) {
        console.warn('WebSocket connection failed, falling back to polling:', wsError);
      }

      // Start polling as fallback
      pollingIntervalRef.current = setInterval(() => {
        pollStatus(response.video_id);
      }, 2000); // Poll every 2 seconds

    } catch (err: any) {
      setError(err.message || 'Failed to submit video');
      setStatus('FAILED');
    }
  }, [handleWebSocketMessage, pollStatus]);

  // Reset state
  const reset = useCallback(() => {
    setVideoId(null);
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
