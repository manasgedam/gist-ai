"""
Repository for project database operations
"""

from api.supabase_client import supabase


class ProjectRepository:
    """Repository for project database operations"""
    
    @staticmethod
    def create_project(user_id: str, title: str, **kwargs):
        """Create a new project"""
        data = {
            'user_id': user_id,
            'title': title,
            'status': 'pending',
            **kwargs
        }
        result = supabase.table('projects').insert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_project(project_id: str):
        """Get a project by ID"""
        result = supabase.table('projects').select('*').eq('id', project_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_user_projects(user_id: str, limit: int = 50):
        """Get all projects for a user, sorted by updated_at desc"""
        result = supabase.table('projects').select('*').eq('user_id', user_id).order('updated_at', desc=True).limit(limit).execute()
        return result.data
    
    @staticmethod
    def update_project(project_id: str, **kwargs):
        """Update a project"""
        result = supabase.table('projects').update(kwargs).eq('id', project_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def delete_project(project_id: str):
        """Delete a project"""
        supabase.table('projects').delete().eq('id', project_id).execute()
    
    @staticmethod
    def update_project_status(project_id: str, status: str):
        """Update project status"""
        return ProjectRepository.update_project(project_id, status=status)

    @staticmethod
    def get_project_details(project_id: str):
        """Get project with all related data (video, ideas, segments)"""
        from api.supabase_client import VideoRepository, IdeaRepository
        
        # Get project
        project = ProjectRepository.get_project(project_id)
        if not project:
            return None
        
        # Get videos for this project
        videos = VideoRepository.get_videos_by_project(project_id)
        video = videos[0] if videos else None
        
        # Get ideas if video exists
        ideas = []
        if video:
            ideas = IdeaRepository.get_ideas_for_video(video['id'])
        
        return {
            'project': project,
            'video': video,
            'ideas': ideas,
            'status': project.get('status', 'pending')
        }

