import os
import re
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel

# Phase 1 & 2 Imports
from ingest import download_video_and_audio, transcribe_with_groq
from brain import map_all_ideas
from batch_stitcher import stitch_idea_video, slugify

# Supabase Integration
from database import (
    start_db_job, 
    update_db_status, 
    save_viral_idea, 
    supabase
)

app = FastAPI(title="Meaning Engine API")

class ProcessRequest(BaseModel):
    url: str

def extract_video_id(url: str):
    """Robust extraction of YouTube ID."""
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

# --- CORE PIPELINE ---
def run_pipeline(job_id: str, url: str, video_id: str):
    raw_assets = [] 
    try:
        # 1. INGESTION
        update_db_status(job_id, "ingesting")
        _, video_path, audio_path = download_video_and_audio(url)
        raw_assets.extend([video_path, audio_path])
        
        # 2. TRANSCRIPTION
        update_db_status(job_id, "transcribing")
        transcript_path = transcribe_with_groq(audio_path, video_id)
        # ❌ DON'T add transcript_path to raw_assets yet!
        
        # 3. KNOWLEDGE MAPPING (The Brain)
        update_db_status(job_id, "mapping_knowledge")
        print(f"🧠 Brain is analyzing: {transcript_path}") # Log this!
        knowledge_map = map_all_ideas(transcript_path)
        
        if not knowledge_map:
            print("🛑 Brain found 0 ideas.")
            update_db_status(job_id, "failed: no segments found")
            return

        # 4. STITCHING 
        update_db_status(job_id, "stitching")
        
        # Create the folder for this specific video
        export_dir = os.path.abspath(f"exports/{video_id}")
        os.makedirs(export_dir, exist_ok=True)

        for index, idea in enumerate(knowledge_map):
            clean_title = slugify(idea.get('title', 'untitled'))
            
            # 🔥 THE FIX: Ensure this is a FILE path, not a FOLDER path
            filename = f"{index + 1}_{clean_title}.mp4"
            output_path = os.path.join(export_dir, filename)
            
            print(f"🎬 Stitching segment {index + 1}: {filename}")
            
            # Pass the full output_path (which ends in .mp4) to the stitcher
            success = stitch_idea_video(video_path, idea, output_path)
        # 5. FINALIZATION
        update_db_status(job_id, "completed")
        
        # Only now, if everything worked, we can delete the transcript
        if os.path.exists(transcript_path):
            os.remove(transcript_path)

    except Exception as e:
        print("\n❌ PIPELINE CRASHED:")
        import traceback
        traceback.print_exc()
        update_db_status(job_id, f"failed: {str(e)}")
        
    finally:
        # Surgical Cleanup: Only delete the heavy Source Video/Audio
        for asset in raw_assets:
            if asset and os.path.exists(asset):
                os.remove(asset)
                print(f"🧹 Cleaned source asset: {asset}")
# --- API ENDPOINTS ---

@app.post("/process")
async def start_engine(request: ProcessRequest, background_tasks: BackgroundTasks):
    video_id = extract_video_id(request.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    job_data, already_processed = start_db_job(video_id, request.url)
    actual_id = job_data["id"]

    if already_processed and job_data['status'] == 'completed':
        return {
            "job_id": actual_id,
            "status": "cached",
            "message": "Results already available."
        }

    background_tasks.add_task(run_pipeline, actual_id, request.url, video_id)
    return {"job_id": actual_id, "status": "accepted"}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    try:
        job_query = supabase.table("processing_jobs").select("*").eq("id", job_id).single().execute()
        if not job_query.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job_data = job_query.data
        if job_data["status"] == "completed":
            ideas_query = supabase.table("viral_ideas").select("*").eq("job_id", job_id).execute()
            job_data["results"] = ideas_query.data
        return job_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))