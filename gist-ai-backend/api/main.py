from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import asyncio
from pathlib import Path

from .models import (
    Video, Idea, ProcessingStage,
    VideoSubmitRequest, VideoResponse, VideoStatusResponse,
    IdeaResponse, IdeasResponse, TimelineResponse, TimelineSegment,
    TimeRangeSchema
)
from .database import get_db_session, init_db
from .websocket_manager import ws_manager
from .pipeline_runner import run_pipeline_task

# Initialize FastAPI app
app = FastAPI(
    title="Gist AI API",
    description="API for processing YouTube videos into short-form content ideas",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    print("✓ Database initialized")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Gist AI API is running"}


@app.post("/api/videos/youtube", response_model=VideoResponse)
async def submit_youtube_video(
    request: VideoSubmitRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """Submit a YouTube URL for processing"""
    
    # Create video record
    video = Video(
        youtube_url=request.url,
        status=ProcessingStage.PENDING,
        current_stage=ProcessingStage.PENDING
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    
    # Also create in Supabase (dual-write)
    try:
        from api.supabase_client import VideoRepository
        VideoRepository.create_video(
            source_url=request.url,
            source_type='youtube',
            youtube_id=None,  # Will be set after ingestion
            video_id=video.id  # Use same ID as SQLite
        )
        print(f"✓ Created video in Supabase: {video.id}")
        
        # Update project status if linked
        if request.project_id:
            from api.project_repository import ProjectRepository
            ProjectRepository.update_project(request.project_id, status='processing')
            print(f"✓ Updated project {request.project_id} to processing")
    except Exception as e:
        print(f"⚠ Warning: Supabase video creation failed: {e}")
    
    # Start background processing
    background_tasks.add_task(run_pipeline_task, video.id, request.url, request.mode)
    
    return VideoResponse(
        video_id=video.id,
        status=video.status,
        message="Video queued for processing"
    )


@app.get("/api/videos/{video_id}", response_model=VideoStatusResponse)
async def get_video_status(video_id: str, db: Session = Depends(get_db_session)):
    """Get video processing status"""
    
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Generate status message
    stage_messages = {
        ProcessingStage.PENDING: "Queued for processing...",
        ProcessingStage.INGESTING: "Downloading video and extracting audio...",
        ProcessingStage.TRANSCRIBING: "Transcribing audio to text...",
        ProcessingStage.UNDERSTANDING: "Analyzing semantic content...",
        ProcessingStage.GROUPING: "Grouping related moments and ideas...",
        ProcessingStage.RANKING: "Ranking short-form potential...",
        ProcessingStage.COMPLETE: "Processing complete!",
        ProcessingStage.FAILED: f"Processing failed: {video.error_message or 'Unknown error'}"
    }
    
    return VideoStatusResponse(
        video_id=video.id,
        status=video.status,
        progress=video.progress,
        current_stage=video.current_stage,
        message=stage_messages.get(video.current_stage, "Processing...")
    )


@app.get("/api/videos/{video_id}/ideas", response_model=IdeasResponse)
async def get_video_ideas(video_id: str, db: Session = Depends(get_db_session)):
    """Get generated ideas for a video"""
    
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Allow timeline access even during processing
    # Video player can show while ideas are being generated
    
    # Get ideas
    ideas = db.query(Idea).filter(Idea.video_id == video_id).order_by(Idea.rank).all()
    
    idea_responses = []
    for idea in ideas:
        time_ranges = [TimeRangeSchema(**tr) for tr in idea.time_ranges]
        idea_responses.append(IdeaResponse(
            id=idea.id,
            rank=idea.rank,
            title=idea.title,
            description=idea.description,
            strength=idea.strength,
            viral_potential=idea.viral_potential,
            highlights=idea.highlights or [],
            time_ranges=time_ranges
        ))
    
    return IdeasResponse(
        video_id=video_id,
        ideas=idea_responses
    )


@app.get("/api/videos/{video_id}/timeline", response_model=TimelineResponse)
async def get_video_timeline(video_id: str, db: Session = Depends(get_db_session)):
    """Get video timeline with idea segments"""
    
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Allow timeline access even during processing
    # Video player can show while ideas are being generated
    
    # Get ideas for segments
    ideas = db.query(Idea).filter(Idea.video_id == video_id).order_by(Idea.rank).all()
    
    # Build segments from idea time ranges
    segments = []
    for idea in ideas:
        for time_range in idea.time_ranges:
            segments.append(TimelineSegment(
                start=time_range['start'],
                end=time_range['end'],
                label=idea.title,
                ideas=[idea.id]
            ))
    
    return TimelineResponse(
        video_id=video_id,
        video_url=f"/api/videos/{video_id}/stream",
        duration=video.duration or 0,
        title=video.title or "Unknown",
        thumbnail=None,
        segments=segments
    )


@app.get("/api/videos/{video_id}/stream")
async def stream_video(video_id: str, db: Session = Depends(get_db_session)):
    """Stream the original video file"""
    
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if not video.video_path or not Path(video.video_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        video.video_path,
        media_type="video/mp4",
        filename=f"{video.youtube_id}.mp4"
    )


@app.websocket("/ws/videos/{video_id}")
async def websocket_endpoint(websocket: WebSocket, video_id: str):
    """WebSocket endpoint for real-time progress updates"""
    
    await ws_manager.connect(video_id, websocket)
    try:
        while True:
            # Keep connection alive and receive any client messages
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_text(data)
    except WebSocketDisconnect:
        await ws_manager.disconnect(video_id, websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await ws_manager.disconnect(video_id, websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ============================================================================
# PROJECT ENDPOINTS
# ============================================================================

from fastapi import Header
from .project_models import ProjectCreate, ProjectResponse, ProjectListResponse
from .project_repository import ProjectRepository


async def get_current_user_id(authorization: str = Header(None)) -> str:
    """Extract user ID from authorization header"""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    from api.supabase_client import supabase
    token = authorization.replace('Bearer ', '')
    
    try:
        user = supabase.auth.get_user(token)
        return user.user.id
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/api/projects", response_model=ProjectListResponse)
async def list_projects(user_id: str = Depends(get_current_user_id)):
    """Get all projects for the authenticated user"""
    try:
        projects = ProjectRepository.get_user_projects(user_id)
        return ProjectListResponse(projects=projects)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects", response_model=ProjectResponse)
async def create_project(
    request: ProjectCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new project"""
    try:
        project = ProjectRepository.create_project(
            user_id=user_id,
            title=request.title
        )
        return project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get a specific project"""
    try:
        project = ProjectRepository.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if project['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a project"""
    try:
        project = ProjectRepository.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if project['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        ProjectRepository.delete_project(project_id)
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/details")
async def get_project_details(
    project_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get complete project with video, ideas, and segments"""
    from api.project_repository import ProjectRepository
    
    try:
        details = ProjectRepository.get_project_details(project_id)
        
        if not details:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Verify ownership
        if details['project']['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        return details
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

