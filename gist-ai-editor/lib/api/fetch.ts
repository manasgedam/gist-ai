// Unified API fetch wrapper with automatic Supabase authentication
// This is the SINGLE SOURCE OF TRUTH for all backend API calls

import { supabase } from '../supabase';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Authenticated fetch wrapper
 * 
 * Automatically:
 * - Retrieves active Supabase session
 * - Extracts access_token
 * - Injects Authorization header
 * - Handles 401/403 errors
 * 
 * @throws Error if not authenticated or request fails
 */
export async function apiFetch(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  // Get current session
  const { data: { session }, error } = await supabase.auth.getSession();
  
  if (error || !session?.access_token) {
    throw new Error('Not authenticated. Please log in.');
  }

  // Merge headers with Authorization
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
    'Authorization': `Bearer ${session.access_token}`,
  };

  // Make request
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // Handle auth errors
  if (response.status === 401) {
    throw new Error('Session expired. Please log in again.');
  }

  if (response.status === 403) {
    throw new Error('Access denied. You don\'t have permission for this action.');
  }

  // Handle other errors
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Request failed: ${response.statusText}`);
  }

  return response;
}

/**
 * Convenience methods for common HTTP verbs
 */
export const api = {
  async get(endpoint: string) {
    const response = await apiFetch(endpoint, { method: 'GET' });
    return response.json();
  },

  async post(endpoint: string, data?: any) {
    const response = await apiFetch(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
    return response.json();
  },

  async put(endpoint: string, data?: any) {
    const response = await apiFetch(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
    return response.json();
  },

  async delete(endpoint: string) {
    const response = await apiFetch(endpoint, { method: 'DELETE' });
    return response.json();
  },
};
