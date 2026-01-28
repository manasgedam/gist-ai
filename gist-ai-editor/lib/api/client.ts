// API client for Gist AI backend

import { getAuthToken } from '@/lib/supabase';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export interface TimeRange {
  start: number;
  end: number;
  confidence: number;
}

export interface Idea {
  id: string;
  rank: number;
  title: string;
  reason: string;
  strength: 'high' | 'medium' | 'low';
  viral_potential?: string;
  highlights: string[];
  time_ranges: TimeRange[];
}

export interface VideoResponse {
  video_id: string;
  status: string;
  message: string;
}

export interface StatusResponse {
  video_id: string;
  status: string;
  progress: number;
  current_stage: string;
  message: string;
  estimated_completion?: string;
}

export interface IdeasResponse {
  video_id: string;
  ideas: Idea[];
}

export interface TimelineSegment {
  start: number;
  end: number;
  label: string;
  ideas: string[];
}

export interface TimelineResponse {
  video_id: string;
  video_url: string;
  duration: number;
  title: string;
  thumbnail?: string;
  segments: TimelineSegment[];
}

export const videoApi = {
  /**
   * Submit a YouTube URL for processing
   */
  async submitYouTubeUrl(url: string, mode: string = 'groq'): Promise<VideoResponse> {
    const response = await fetch(`${API_BASE_URL}/api/videos/youtube`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url, mode }),
    });

    if (!response.ok) {
      throw new Error(`Failed to submit video: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Get video processing status
   */
  async getVideoStatus(videoId: string): Promise<StatusResponse> {
    const response = await fetch(`${API_BASE_URL}/api/videos/${videoId}`);

    if (!response.ok) {
      throw new Error(`Failed to get video status: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Get generated ideas for a video
   */
  async getVideoIdeas(videoId: string): Promise<IdeasResponse> {
    const response = await fetch(`${API_BASE_URL}/api/videos/${videoId}/ideas`);

    if (!response.ok) {
      throw new Error(`Failed to get ideas: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Get video timeline data
   */
  async getVideoTimeline(videoId: string): Promise<TimelineResponse> {
    const response = await fetch(`${API_BASE_URL}/api/videos/${videoId}/timeline`);

    if (!response.ok) {
      throw new Error(`Failed to get timeline: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Get video stream URL
   */
  getVideoStreamUrl(videoId: string): string {
    return `${API_BASE_URL}/api/videos/${videoId}/stream`;
  },

  /**
   * Connect to WebSocket for real-time updates
   */
  connectWebSocket(videoId: string, onMessage: (message: any) => void): WebSocket {
    const ws = new WebSocket(`${WS_BASE_URL}/ws/videos/${videoId}`);

    ws.onopen = () => {
      console.log(`WebSocket connected for video ${videoId}`);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        onMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log(`WebSocket disconnected for video ${videoId}`);
    };

    return ws;
  },
};
