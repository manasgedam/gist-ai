import sys
import os
import json
import asyncio
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

# Add parent directory to path to import pipeline modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_pipeline import GistPipeline
from api.models import ProcessingStage, Video, Idea, TimeRangeSchema
from api.database import get_db
from api.websocket_manager import ws_manager


class PipelineRunner:
    """Wraps GistPipeline for API integration with progress callbacks"""
    
    def __init__(self, video_id: str, youtube_url: str, mode: str = "groq"):
        self.video_id = video_id
        self.youtube_url = youtube_url
        self.mode = mode
        self.output_dir = Path("output")
        
    async def update_video_status(self, stage: ProcessingStage, progress: int, message: str, error: Optional[str] = None):
        """Update video status in database"""
        with get_db() as db:
            video = db.query(Video).filter(Video.id == self.video_id).first()
            if video:
                video.current_stage = stage
                video.status = stage
                video.progress = progress
                video.updated_at = datetime.utcnow()
                if error:
                    video.error_message = error
                    video.status = ProcessingStage.FAILED
                db.commit()
        
        # Broadcast via WebSocket
        await ws_manager.send_progress(self.video_id, stage.value, progress, message)
    
    async def save_ideas_to_db(self, ideas_data: dict):
        """Parse ideas JSON and save to database"""
        with get_db() as db:
            video = db.query(Video).filter(Video.id == self.video_id).first()
            if not video:
                return
            
            # Clear existing ideas
            db.query(Idea).filter(Idea.video_id == self.video_id).delete()
            
            # Parse and save new ideas
            for idea_data in ideas_data.get('ideas', []):
                # Extract time ranges
                time_ranges = []
                for tr in idea_data.get('time_ranges', []):
                    time_ranges.append({
                        "start": tr.get('start', 0),
                        "end": tr.get('end', 0),
                        "confidence": tr.get('confidence', 1.0)
                    })
                
                idea = Idea(
                    video_id=self.video_id,
                    rank=idea_data.get('rank', 0),
                    title=idea_data.get('title', ''),
                    reason=idea_data.get('reason', ''),
                    strength=idea_data.get('strength', 'medium'),
                    viral_potential=idea_data.get('viral_potential'),
                    highlights=idea_data.get('highlights', []),
                    time_ranges=time_ranges
                )
                db.add(idea)
            
            db.commit()
    
    async def run(self):
        """Run the pipeline with progress updates"""
        # Wait 1 second to ensure WebSocket connection is established
        # This prevents messages from being sent before frontend is ready
        await asyncio.sleep(1)
        
        try:
            # Stage 1: Ingestion
            await self.update_video_status(
                ProcessingStage.INGESTING,
                10,
                "Downloading video and extracting audio..."
            )
            
            pipeline = GistPipeline(mode=self.mode, skip_stitch=True)
            # CRITICAL: Run in thread pool to prevent blocking the event loop
            # This allows WebSocket messages to be sent during processing
            transcript_path, yt_id = await asyncio.to_thread(
                pipeline.run_ingestion, self.youtube_url
            )
            
            if not transcript_path:
                await self.update_video_status(
                    ProcessingStage.FAILED,
                    0,
                    "Failed to download or process video",
                    error="Ingestion failed"
                )
                await ws_manager.send_error(
                    self.video_id,
                    ProcessingStage.INGESTING.value,
                    "Ingestion failed",
                    "Could not download or process the video"
                )
                return
            
            # Update video metadata
            with get_db() as db:
                video = db.query(Video).filter(Video.id == self.video_id).first()
                if video:
                    video.youtube_id = yt_id
                    video.transcript_path = str(transcript_path)
                    
                    # Extract metadata from transcript
                    with open(transcript_path, 'r') as f:
                        transcript_data = json.load(f)
                        video.title = transcript_data.get('title', 'Unknown')
                        video.duration = transcript_data.get('duration', 0)
                        video.video_path = transcript_data.get('video_path', '')
                    
                    db.commit()
            
            # Emit video_ready event with metadata so frontend can load video immediately
            await ws_manager.send_message(self.video_id, {
                "type": "video_ready",
                "video_id": self.video_id,
                "title": transcript_data.get('title', 'Unknown'),
                "duration": transcript_data.get('duration', 0),
                "message": "Video is ready for playback"
            })
            
            # Stage 2: Transcription complete (already done in ingestion)
            await self.update_video_status(
                ProcessingStage.TRANSCRIBING,
                30,
                "Transcription complete"
            )
            await ws_manager.send_stage_complete(
                self.video_id,
                ProcessingStage.INGESTING.value,
                ProcessingStage.TRANSCRIBING.value
            )
            
            # Stage 3: Understanding - Brain Stage 1 (Identifying Ideas)
            await self.update_video_status(
                ProcessingStage.UNDERSTANDING,
                45,
                "Analyzing semantic content with AI..."
            )
            await ws_manager.send_stage_complete(
                self.video_id,
                ProcessingStage.TRANSCRIBING.value,
                ProcessingStage.UNDERSTANDING.value
            )
            
            # Run brain processing (includes understanding, grouping, ranking)
            # CRITICAL: Run in thread pool to prevent blocking the event loop
            ideas_path = await asyncio.to_thread(
                pipeline.run_brain, transcript_path
            )
            
            if not ideas_path:
                await self.update_video_status(
                    ProcessingStage.FAILED,
                    0,
                    "No ideas could be generated from this video",
                    error="Brain processing failed"
                )
                await ws_manager.send_error(
                    self.video_id,
                    ProcessingStage.RANKING.value,
                    "No ideas generated",
                    "Could not find usable ideas in this video"
                )
                return
            
            # Brain processing complete - update remaining stages
            # Stage 4: Grouping complete
            await self.update_video_status(
                ProcessingStage.GROUPING,
                70,
                "Grouping complete"
            )
            await ws_manager.send_stage_complete(
                self.video_id,
                ProcessingStage.UNDERSTANDING.value,
                ProcessingStage.GROUPING.value
            )
            
            # Stage 5: Ranking complete
            await self.update_video_status(
                ProcessingStage.RANKING,
                90,
                "Ranking complete"
            )
            await ws_manager.send_stage_complete(
                self.video_id,
                ProcessingStage.GROUPING.value,
                ProcessingStage.RANKING.value
            )
            
            # Update video with ideas path
            with get_db() as db:
                video = db.query(Video).filter(Video.id == self.video_id).first()
                if video:
                    video.ideas_path = str(ideas_path)
                    db.commit()
            
            # Parse and save ideas
            with open(ideas_path, 'r') as f:
                ideas_data = json.load(f)
            
            await self.save_ideas_to_db(ideas_data)
            
            # Complete
            await self.update_video_status(
                ProcessingStage.COMPLETE,
                100,
                f"Processing complete! {ideas_data.get('ideas_count', 0)} ideas generated."
            )
            await ws_manager.send_complete(
                self.video_id,
                ideas_data.get('ideas_count', 0)
            )
            
        except Exception as e:
            print(f"Pipeline error: {str(e)}")
            await self.update_video_status(
                ProcessingStage.FAILED,
                0,
                f"Processing failed: {str(e)}",
                error=str(e)
            )
            await ws_manager.send_error(
                self.video_id,
                "UNKNOWN",
                str(e),
                "An unexpected error occurred during processing"
            )


async def run_pipeline_task(video_id: str, youtube_url: str, mode: str = "local"):
    """Background task to run the pipeline"""
    runner = PipelineRunner(video_id, youtube_url, mode)
    await runner.run()
