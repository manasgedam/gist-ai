"""
Supabase client and repository classes for database operations
"""

import os
from supabase import create_client, Client

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


class VideoRepository:
    """Repository for video database operations"""
    
    @staticmethod
    def create_video(source_url: str, source_type: str, youtube_id: str = None, video_id: str = None, **kwargs):
        """Create a new video record"""
        data = {
            'source_url': source_url,
            'source_type': source_type,
            'youtube_id': youtube_id,
            'status': 'PENDING',
            'progress': 0,
            **kwargs
        }
        if video_id:
            data['id'] = video_id
        
        result = supabase.table('videos').insert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def update_processing_state(video_id: str, status: str, current_stage: str = None, progress: int = None, message: str = None):
        """Update video processing state"""
        data = {'status': status}
        if current_stage:
            data['current_stage'] = current_stage
        if progress is not None:
            data['progress'] = progress
        if message:
            data['error_message'] = message
        
        result = supabase.table('videos').update(data).eq('id', video_id).execute()
        return result.data[0] if result.data else None


class IdeaRepository:
    """Repository for idea database operations"""
    
    @staticmethod
    def create_idea(video_id: str, user_id: str, rank: int, title: str, **kwargs):
        """Create a new idea"""
        data = {
            'video_id': video_id,
            'user_id': user_id,
            'rank': rank,
            'title': title,
            **kwargs
        }
        result = supabase.table('ideas').insert(data).execute()
        return result.data[0] if result.data else None


class SegmentRepository:
    """Repository for segment database operations"""
    
    @staticmethod
    def create_segment(idea_id: str, start_time: float, end_time: float, duration: float, sequence_order: int, **kwargs):
        """Create a new segment"""
        data = {
            'idea_id': idea_id,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'sequence_order': sequence_order,
            **kwargs
        }
        result = supabase.table('segments').insert(data).execute()
        return result.data[0] if result.data else None
