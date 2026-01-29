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
from api.supabase_client import VideoRepository, IdeaRepository, SegmentRepository
from api.storage import r2_storage


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
        
        # Also update Supabase (dual-write)
        try:
            VideoRepository.update_processing_state(
                self.video_id,
                status=stage.value,
                current_stage=stage.value,
                progress=progress,
                message=error if error else None
            )
        except Exception as e:
            print(f"  ⚠ Warning: Supabase state update failed: {e}")
        
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
                    description=idea_data.get('reason', ''),
                    strength=idea_data.get('strength', 'medium'),
                    viral_potential=idea_data.get('viral_potential'),
                    highlights=idea_data.get('highlights', []),
                    time_ranges=time_ranges
                )
                db.add(idea)
            
            db.commit()
        
        # Also save to Supabase (dual-write)
        try:
            print(f"💾 Saving ideas to Supabase...")
            
            # Clear existing ideas in Supabase
            IdeaRepository.delete_ideas_for_video(self.video_id)
            
            # Save new ideas and segments
            for idea_data in ideas_data.get('ideas', []):
                # Create idea in Supabase
                idea = IdeaRepository.create_idea(
                    video_id=self.video_id,
                    rank=idea_data.get('rank', 0) + 1,  # Convert 0-indexed to 1-indexed
                    title=idea_data.get('title', ''),
                    description=idea_data.get('reason', ''),
                    strength=idea_data.get('strength', 'medium'),
                    viral_potential=idea_data.get('viral_potential'),
                    total_duration=idea_data.get('total_duration_seconds'),
                    segment_count=idea_data.get('segment_count')
                )
                
                idea_id = idea['id']
                
                # Create segments for this idea
                segments = []
                for idx, segment_data in enumerate(idea_data.get('segments', []), 1):
                    segments.append({
                        'idea_id': idea_id,
                        'start_time': segment_data.get('start_seconds', 0),
                        'end_time': segment_data.get('end_seconds', 0),
                        'duration': segment_data.get('duration_seconds', 0),
                        'sequence_order': idx,
                        'purpose': segment_data.get('purpose', '')
                    })
                
                if segments:
                    SegmentRepository.bulk_create_segments(segments)
            
            print(f"  ✓ Saved {len(ideas_data.get('ideas', []))} ideas to Supabase")
            
        except Exception as e:
            print(f"  ⚠ Warning: Supabase ideas save failed: {e}")
    
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
            
            # Update video metadata in SQLite
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
            
            # CLOUD STORAGE: Upload files to R2 and save to Supabase
            try:
                print(f"📤 Uploading files to R2...")
                
                # Get file paths from transcript data
                with open(transcript_path, 'r') as f:
                    transcript_data = json.load(f)
                
                video_path = Path(transcript_data.get('video_file_path', ''))
                audio_path = transcript_path.parent / f"{yt_id}_audio.mp3"
                
                # Upload to R2
                video_url = None
                audio_url = None
                transcript_url = None
                
                if video_path.exists():
                    video_url = r2_storage.upload_video(self.video_id, str(video_path), 'original')
                    print(f"  ✓ Video uploaded: {video_url}")
                
                if audio_path.exists():
                    audio_url = r2_storage.upload_video(self.video_id, str(audio_path), 'audio')
                    print(f"  ✓ Audio uploaded: {audio_url}")
                
                if transcript_path.exists():
                    transcript_url = r2_storage.upload_video(self.video_id, str(transcript_path), 'transcript')
                    print(f"  ✓ Transcript uploaded: {transcript_url}")
                
                # Save to Supabase
                VideoRepository.set_video_urls(
                    self.video_id,
                    original_url=video_url,
                    audio_url=audio_url,
                    transcript_url=transcript_url
                )
                
                VideoRepository.set_video_metadata(
                    self.video_id,
                    title=transcript_data.get('title', 'Unknown'),
                    duration=transcript_data.get('duration', 0),
                    language=transcript_data.get('language', 'en')
                )
                print(f"  ✓ Metadata saved to Supabase")
                
                # Clean up local files after successful upload
                print(f"🗑️  Cleaning up local files...")
                try:
                    if video_path.exists():
                        video_path.unlink()
                        print(f"  ✓ Deleted local video: {video_path.name}")
                    
                    if audio_path.exists():
                        audio_path.unlink()
                        print(f"  ✓ Deleted local audio: {audio_path.name}")
                    
                    if transcript_path.exists():
                        transcript_path.unlink()
                        print(f"  ✓ Deleted local transcript: {transcript_path.name}")
                    
                    print(f"  ✓ Local files cleaned up")
                except Exception as cleanup_error:
                    print(f"  ⚠ Warning: File cleanup failed: {cleanup_error}")
                
            except Exception as e:
                print(f"  ⚠ Warning: Cloud storage failed: {e}")
                # Continue processing even if cloud storage fails
            
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

    def _run_mock_pipeline(self):
        """Mock pipeline for development without API calls"""
        import time
        from api.mock_data import get_mock_ideas
        
        try:
            # Simulate some processing time
            self._update_state('INGESTING', 20, 'Downloading video...')
            time.sleep(0.5)
            
            self._update_state('TRANSCRIBING', 40, 'Extracting audio...')
            time.sleep(0.5)
            
            self._update_state('UNDERSTANDING', 60, 'Analyzing content...')
            time.sleep(0.5)
            
            self._update_state('GROUPING', 80, 'Finding ideas...')
            time.sleep(0.5)
            
            # Get mock ideas
            mock_data = get_mock_ideas()
            
            # Save to database (same as real pipeline)
            self._save_ideas_to_db(mock_data)
            
            self._update_state('COMPLETE', 100, 'Processing complete!')
            print('✅ Mock pipeline complete - ideas saved to database')
            
        except Exception as e:
            print(f'Mock pipeline error: {e}')
            self._update_state('FAILED', 0, f'Mock processing failed: {str(e)}')
            raise

