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
    def create_video(source_url: str, source_type: str, user_id: str, project_id: str, youtube_id: str = None, video_id: str = None, **kwargs):
        """
        Create a new video record
        
        Args:
            source_url: YouTube URL or upload URL
            source_type: 'youtube' or 'upload'
            user_id: User ID (REQUIRED - no anonymous users)
            project_id: Project ID (REQUIRED - videos must belong to a project)
            youtube_id: YouTube video ID (optional)
            video_id: Custom video ID (optional, auto-generated if not provided)
            **kwargs: Additional fields
        
        Raises:
            ValueError: If user_id or project_id is missing
        """
        if not user_id:
            raise ValueError("user_id is required - no anonymous users allowed")
        if not project_id:
            raise ValueError("project_id is required - videos must belong to a project")
        
        data = {
            'source_url': source_url,
            'source_type': source_type,
            'user_id': user_id,
            'project_id': project_id,
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
        # Convert status to uppercase for Supabase (it expects PENDING, COMPLETE, FAILED, etc.)
        data = {'status': status.upper() if status else status}
        if current_stage:
            data['current_stage'] = current_stage.upper()
        if progress is not None:
            data['progress'] = progress
        if message:
            data['error_message'] = message
        
        result = supabase.table('videos').update(data).eq('id', video_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_videos_by_project(project_id: str):
        """Get all videos for a project"""
        result = supabase.table('videos').select('*').eq('project_id', project_id).execute()
        return result.data if result.data else []
    
    @staticmethod
    def set_video_urls(video_id: str, original_url: str = None, audio_url: str = None, transcript_url: str = None):
        """Set video file URLs"""
        data = {}
        if original_url:
            data['original_video_url'] = original_url
        if audio_url:
            data['audio_file_url'] = audio_url
        if transcript_url:
            data['transcript_url'] = transcript_url
        
        if data:
            result = supabase.table('videos').update(data).eq('id', video_id).execute()
            return result.data[0] if result.data else None
        return None
    
    @staticmethod
    def set_video_metadata(video_id: str, title: str = None, duration: float = None, language: str = None):
        """Set video metadata"""
        data = {}
        if title:
            data['title'] = title
        if duration is not None:
            data['duration'] = duration
        if language:
            data['language'] = language
        
        if data:
            result = supabase.table('videos').update(data).eq('id', video_id).execute()
            return result.data[0] if result.data else None
        return None
    
    @staticmethod
    def mark_completed(video_id: str):
        """Mark video as completed with timestamp (atomic completion)"""
        from datetime import datetime
        data = {
            'status': 'COMPLETE',
            'progress': 100,
            'completed_at': datetime.utcnow().isoformat()
        }
        result = supabase.table('videos').update(data).eq('id', video_id).execute()
        return result.data[0] if result.data else None


class IdeaRepository:
    """Repository for idea database operations"""
    
    @staticmethod
    def create_idea(video_id: str, rank: int, title: str, **kwargs):
        """Create a new idea"""
        data = {
            'video_id': video_id,
            'rank': rank,
            'title': title,
            **kwargs
        }
        result = supabase.table('ideas').insert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def delete_ideas_for_video(video_id: str):
        """Delete all ideas for a video (cascades to segments via ON DELETE CASCADE)"""
        result = supabase.table('ideas').delete().eq('video_id', video_id).execute()
        return result
    
    @staticmethod
    def get_ideas_for_video(video_id: str):
        """Get all ideas for a video"""
        result = supabase.table('ideas').select('*').eq('video_id', video_id).order('rank').execute()
        return result.data if result.data else []


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
    
    @staticmethod
    def bulk_create_segments(segments: list):
        """Bulk create segments"""
        if not segments:
            return []
        result = supabase.table('segments').insert(segments).execute()
        return result.data if result.data else []
