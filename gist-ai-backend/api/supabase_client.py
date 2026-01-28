"""
Supabase database client
"""

import os
from supabase import create_client, Client

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class VideoRepository:
    """Repository for video database operations"""
    
    @staticmethod
    def create_video(source_url: str, source_type: str, youtube_id: str = None, video_id: str = None):
        """Create a new video record"""
        data = {
            'source_url': source_url,
            'source_type': source_type,
            'status': 'PENDING'
        }
        if video_id:
            data['id'] = video_id  # Use provided ID instead of auto-generated
        if youtube_id:
            data['youtube_id'] = youtube_id
        
        result = supabase.table('videos').insert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_video(video_id: str):
        """Get video by ID"""
        result = supabase.table('videos').select('*').eq('id', video_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def update_video(video_id: str, updates: dict):
        """Update video record"""
        result = supabase.table('videos').update(updates).eq('id', video_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def update_processing_state(video_id: str, status: str, current_stage: str, progress: int, message: str = None):
        """Update video processing state"""
        updates = {
            'status': status,
            'current_stage': current_stage,
            'progress': progress
        }
        if message:
            updates['error_message'] = message if status == 'FAILED' else None
        
        return VideoRepository.update_video(video_id, updates)
    
    @staticmethod
    def set_video_urls(video_id: str, original_url: str = None, audio_url: str = None, transcript_url: str = None):
        """Set storage URLs for video files"""
        updates = {}
        if original_url:
            updates['original_video_url'] = original_url
        if audio_url:
            updates['audio_file_url'] = audio_url
        if transcript_url:
            updates['transcript_url'] = transcript_url
        
        if updates:
            return VideoRepository.update_video(video_id, updates)
    
    @staticmethod
    def set_video_metadata(video_id: str, title: str, duration: float, language: str = None):
        """Set video metadata"""
        updates = {
            'title': title,
            'duration': duration
        }
        if language:
            updates['language'] = language
        
        return VideoRepository.update_video(video_id, updates)
    
    @staticmethod
    def list_videos(limit: int = 20):
        """List recent videos"""
        result = supabase.table('videos').select('*').order('created_at', desc=True).limit(limit).execute()
        return result.data


class IdeaRepository:
    """Repository for idea database operations"""
    
    @staticmethod
    def create_idea(video_id: str, rank: int, title: str, description: str, **kwargs):
        """Create a new idea"""
        data = {
            'video_id': video_id,
            'rank': rank,
            'title': title,
            'description': description,
            **kwargs
        }
        result = supabase.table('ideas').insert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_ideas_for_video(video_id: str):
        """Get all ideas for a video"""
        result = supabase.table('ideas').select('*').eq('video_id', video_id).order('rank').execute()
        return result.data
    
    @staticmethod
    def delete_ideas_for_video(video_id: str):
        """Delete all ideas for a video"""
        supabase.table('ideas').delete().eq('video_id', video_id).execute()


class SegmentRepository:
    """Repository for segment database operations"""
    
    @staticmethod
    def create_segment(idea_id: str, start_time: float, end_time: float, duration: float, sequence_order: int, purpose: str = None):
        """Create a new segment"""
        data = {
            'idea_id': idea_id,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'sequence_order': sequence_order
        }
        if purpose:
            data['purpose'] = purpose
        
        result = supabase.table('segments').insert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_segments_for_idea(idea_id: str):
        """Get all segments for an idea"""
        result = supabase.table('segments').select('*').eq('idea_id', idea_id).order('sequence_order').execute()
        return result.data
    
    @staticmethod
    def bulk_create_segments(segments: list):
        """Create multiple segments at once"""
        result = supabase.table('segments').insert(segments).execute()
        return result.data
