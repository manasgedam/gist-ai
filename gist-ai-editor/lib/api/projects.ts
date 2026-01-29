// API client for projects

import { getAuthToken } from '@/lib/supabase';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Project {
  id: string;
  title: string;
  video_url?: string;
  thumbnail_url?: string;
  status: 'pending' | 'processing' | 'ready' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface ProjectListResponse {
  projects: Project[];
}

export const projectsApi = {
  async list(): Promise<Project[]> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout for fetch

    try {
      // Create a timeout for auth token retrieval to prevent infinite hanging
      const authTimeoutPromise = new Promise<string | null>((_, reject) => {
        setTimeout(() => reject(new Error('Auth token retrieval timed out')), 5000);
      });

      // Race between actual token retrieval and timeout
      // using type assertion since Promise.race returns the first resolved/rejected promise
      const token = await Promise.race([
        getAuthToken(),
        authTimeoutPromise
      ]) as string | null | undefined;

      if (!token) {
        console.warn('No auth token available');
        clearTimeout(timeoutId);
        return []; // Return empty array if not authenticated
      }
      
      const response = await fetch(`${API_BASE_URL}/api/projects`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        if (response.status === 401) {
          console.warn('Unauthorized - user may need to sign in');
          return [];
        }
        throw new Error(`Failed to fetch projects: ${response.status}`);
      }
      
      const data: ProjectListResponse = await response.json();
      return data.projects;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error) {
         if (error.name === 'AbortError') {
          throw new Error('Request timeout - please check your connection');
        }
        // Log the specific error to help debugging
        console.error('Error in projectsApi.list:', error.message);
      }
      throw error;
    }
  },

  async create(title: string): Promise<Project> {
    const token = await getAuthToken();
    
    const response = await fetch(`${API_BASE_URL}/api/projects`, {
      method: 'POST',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ title }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to create project');
    }
    
    return response.json();
  },

  async get(id: string): Promise<Project> {
    const token = await getAuthToken();
    
    const response = await fetch(`${API_BASE_URL}/api/projects/${id}`, {
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch project');
    }
    
    return response.json();
  },

  async delete(id: string): Promise<void> {
    const token = await getAuthToken();
    
    const response = await fetch(`${API_BASE_URL}/api/projects/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to delete project');
    }
  },
};

// Helper function to format relative time
export function formatRelativeTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  const weeks = Math.floor(days / 7);
  
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  if (weeks < 4) return `${weeks}w ago`;
  return date.toLocaleDateString();
}
