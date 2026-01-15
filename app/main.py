from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

# Import your local modules
from .database import SessionLocal, engine, init_db
from .orchestrator import GistOrchestrator
from . import models

# Initialize the FastAPI app
app = FastAPI(title="Gist AI API", version="1.0.0")

# Ensure tables are created on startup (Standard Practice for small projects)
@app.on_event("startup")
def on_startup():
    init_db()

# Dependency to get a fresh DB session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize our Orchestrator
# Note: In a larger app, you might inject this as a dependency
orchestrator = GistOrchestrator()

@app.post("/process/", status_code=202)
async def start_gist_process(
    youtube_url: str, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Accepts a YouTube URL and triggers the AI pipeline in the background.
    Returns a job_id immediately so the user doesn't wait.
    """
    # 1. Generate a unique ID for this specific run
    job_id = str(uuid.uuid4())

    # 2. Create the initial 'Video' entry in our SQL database
    # This acts as our "State of Truth"
    new_video = models.Video(
        id=job_id,
        url=youtube_url,
        title="Processing...", # Will be updated by yt-dlp later
        status="QUEUED"
    )
    db.add(new_video)
    db.commit()

    # 3. Schedule the Orchestrator to run in the background
    # FastAPI handles the threading for you here
    background_tasks.add_task(orchestrator.run_job, job_id, youtube_url)

    # 4. Return the 'receipt' to the user
    return {
        "job_id": job_id,
        "message": "Gist AI has started analyzing your video. Use the /status/ endpoint to track progress.",
        "status": "QUEUED"
    }

@app.get("/status/{job_id}")
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Allows the frontend to poll for progress.
    """
    video = db.query(models.Video).filter(models.Video.id == job_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": video.id,
        "status": video.status,
        "title": video.title,
        "created_at": video.created_at,
        "clips_found": len(video.clips),
        "clips": video.clips # Returns the AI-generated ideas if ready
    }

