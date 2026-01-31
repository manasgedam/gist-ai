// API client for projects
// Uses authenticated apiFetch wrapper to ensure Authorization headers

import { api } from './fetch';

export interface Project {
  id: string;
  title: string;
  video_url?: string;
  thumbnail_url?: string;
  status: 'pending' | 'processing' | 'ready' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface Video {
  id: string;
  project_id: string;
  status: string;
  original_url: string;
  title?: string;
  duration?: number;
  progress?: number;
  current_stage?: string;
  error_message?: string;
  created_at: string;
}

export interface Idea {
  id: string;
  video_id: string;
  title: string;
  description: string;
  score?: number;
  created_at: string;
}

export interface ProjectDetailsResponse {
  project: Project;
  videos: Video[];
  ideas: Idea[];
  status: string;
}

export interface ProjectListResponse {
  projects: Project[];
}

export const projectsApi = {
  async list(): Promise<Project[]> {
    try {
      const data: ProjectListResponse = await api.get('/api/projects');
      return data.projects;
    } catch (error) {
      if (error instanceof Error) {
        console.error('Error in projectsApi.list:', error.message);
        // Return empty array for auth errors instead of throwing
        if (error.message.includes('Not authenticated') || error.message.includes('Session expired')) {
          return [];
        }
      }
      throw error;
    }
  },

  async create(title: string): Promise<Project> {
    return api.post('/api/projects', { title });
  },

  async get(id: string): Promise<Project> {
    return api.get(`/api/projects/${id}`);
  },

  async getDetails(id: string): Promise<ProjectDetailsResponse> {
    return api.get(`/api/projects/${id}/details`);
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/api/projects/${id}`);
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
