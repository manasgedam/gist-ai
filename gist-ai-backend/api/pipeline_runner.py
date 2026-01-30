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
    
    @staticmethod
    def normalize_idea_data(idea_data: dict) -> dict:
        """
        Normalize idea data from brain output to database schema.
        This creates a clear contract boundary between AI pipeline and database.
        
        Brain output fields:
        - title: str
        - description: str (from Stage 1)
        - reasoning: str (from Stage 2, explains how segments connect)
        - segments: list
        - segment_count: int
        - total_duration_seconds: float
        - transcript_excerpt: str
        
        Database fields:
        - title: str (NOT NULL)
        - description: str (nullable)
        - reason: str (nullable) - maps from 'reasoning'
        - strength: str (nullable)
        - viral_potential: float (nullable)
        - highlights: JSON (nullable)
        - time_ranges: JSON (nullable)
        """
        return {
            'title': idea_data.get('title', ''),
            'description': idea_data.get('description', ''),
            'reason': idea_data.get('reasoning', ''),  # Map 'reasoning' to 'reason'
            'strength': idea_data.get('strength', 'medium'),
            'viral_potential': idea_data.get('viral_potential'),
            'highlights': idea_data.get('highlights', []),
            'segments': idea_data.get('segments', []),
            'segment_count': idea_data.get('segment_count', 0),
            'total_duration_seconds': idea_data.get('total_duration_seconds', 0)
        }
        
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
                status=stage,
                current_stage=stage,
                progress=progress,
                message=error if error else None
            )
        except Exception as e:
            print(f"  ⚠ Warning: Supabase state update failed: {e}")
        
        # Broadcast via WebSocket
        await ws_manager.send_progress(self.video_id, stage, progress, message)
    
    async def save_ideas_to_db(self, ideas_data: dict):
        """Parse ideas JSON and save to database"""
        with get_db() as db:
            video = db.query(Video).filter(Video.id == self.video_id).first()
            if not video:
                return
            
            user_id = video.user_id  # Get user_id from video for isolation
            
            # Clear existing ideas
            db.query(Idea).filter(Idea.video_id == self.video_id).delete()
            
            # Parse and save new ideas
            for rank, idea_data in enumerate(ideas_data.get('ideas', []), 1):
                # Normalize data to ensure correct field mapping
                normalized = self.normalize_idea_data(idea_data)
                
                # Extract time ranges from segments
                time_ranges = []
                for segment in normalized['segments']:
                    time_ranges.append({
                        "start": segment.get('start_seconds', 0),
                        "end": segment.get('end_seconds', 0),
                        "confidence": 1.0
                    })
                
                idea = Idea(
                    video_id=self.video_id,
                    rank=rank,
                    title=normalized['title'],
                    description=normalized['description'],
                    reason=normalized['reason'],  # Correctly mapped from 'reasoning'
                    strength=normalized['strength'],
                    viral_potential=normalized['viral_potential'],
                    highlights=normalized['highlights'],
                    time_ranges=time_ranges,
                    user_id=user_id  # User isolation
                )
                db.add(idea)
            
            db.commit()
        
        # Also save to Supabase (dual-write)
        try:
            print(f"💾 Saving ideas to Supabase...")
            
            # Clear existing ideas in Supabase
            IdeaRepository.delete_ideas_for_video(self.video_id)
            
            # Save new ideas and segments
            for rank, idea_data in enumerate(ideas_data.get('ideas', []), 1):
                # Normalize data to ensure correct field mapping
                normalized = self.normalize_idea_data(idea_data)
                
                # Create idea in Supabase
                idea = IdeaRepository.create_idea(
                    video_id=self.video_id,
                    rank=rank,
                    title=normalized['title'],
                    description=normalized['description'],
                    reason=normalized['reason'],  # Correctly mapped from 'reasoning'
                    strength=normalized['strength'],
                    viral_potential=normalized['viral_potential'],
                    total_duration=normalized['total_duration_seconds'],
                    segment_count=normalized['segment_count'],
                    user_id=user_id  # User isolation
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
                    ProcessingStage.INGESTING,
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
                
                # Upload to R2 - CRITICAL: Abort on failure
                video_url = None
                audio_url = None
                transcript_url = None
                
                if video_path.exists():
                    video_url = r2_storage.upload_video(self.video_id, str(video_path), 'original')
                    if not video_url:
                        raise RuntimeError("Failed to upload video to R2 storage")
                    print(f"  ✓ Video uploaded: {video_url}")
                
                if audio_path.exists():
                    audio_url = r2_storage.upload_video(self.video_id, str(audio_path), 'audio')
                    if not audio_url:
                        raise RuntimeError("Failed to upload audio to R2 storage")
                    print(f"  ✓ Audio uploaded: {audio_url}")
                
                if transcript_path.exists():
                    transcript_url = r2_storage.upload_video(self.video_id, str(transcript_path), 'transcript')
                    if not transcript_url:
                        raise RuntimeError("Failed to upload transcript to R2 storage")
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
                
                # NOTE: Cleanup moved to end of pipeline (after Brain stage)
                # Brain needs to read transcript.json, so we can't delete it yet
                
            except Exception as e:
                # CRITICAL: Abort pipeline on upload failure
                error_msg = str(e)
                print(f"❌ Cloud storage failed: {error_msg}")
                
                # Update database with failure
                await self.update_video_status(
                    ProcessingStage.FAILED,
                    0,
                    f"Upload failed: {error_msg}",
                    error=error_msg
                )
                
                # Send WebSocket failure event
                await ws_manager.send_message(self.video_id, {
                    "type": "upload_failed",
                    "video_id": self.video_id,
                    "error": "Failed to upload files to cloud storage. Please try again.",
                    "stage": "upload",
                    "technical_error": error_msg
                })
                
                raise  # Abort pipeline
            
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
                ProcessingStage.INGESTING,
                ProcessingStage.TRANSCRIBING
            )
            
            # Stage 3: Understanding - Brain Stage 1 (Identifying Ideas)
            await self.update_video_status(
                ProcessingStage.UNDERSTANDING,
                45,
                "Analyzing semantic content with AI..."
            )
            await ws_manager.send_stage_complete(
                self.video_id,
                ProcessingStage.TRANSCRIBING,
                ProcessingStage.UNDERSTANDING
            )
            
            
            # Run brain processing (includes understanding, grouping, ranking)
            # CRITICAL: Run in thread pool to prevent blocking the event loop
            # Stage 2: Brain (Two-Stage Processing)
            try:
                ideas_path = await asyncio.get_event_loop().run_in_executor(
                    None,
                    pipeline.run_brain, transcript_path
                )
            except RuntimeError as e:
                # Provider preflight failure
                error_msg = str(e)
                if "All providers failed preflight" in error_msg:
                    print(f"\n❌ FATAL: {error_msg}")
                    
                    # Update database with failure
                    await self.update_video_status(
                        ProcessingStage.FAILED,
                        0,
                        "LLM provider unavailable - check API keys",
                        error=error_msg
                    )
                    
                    # Send WebSocket failure event
                    await ws_manager.send_message(self.video_id, {
                        "type": "provider_failed",
                        "video_id": self.video_id,
                        "error": "No LLM providers available. Please check your API keys in settings.",
                        "stage": "brain_init",
                        "technical_error": error_msg
                    })
                    
                    return  # Abort pipeline
                else:
                    # Other RuntimeError, re-raise
                    raise
            except ValueError as e:
                # Model validation error or configuration issue
                error_msg = str(e)
                print(f"✗ Brain initialization error: {error_msg}")
                await self.update_video_status(
                    ProcessingStage.FAILED,
                    0,
                    f"Invalid model configuration: {error_msg}",
                    error=error_msg
                )
                await ws_manager.send_error(
                    self.video_id,
                    ProcessingStage.UNDERSTANDING,
                    "Model configuration error",
                    error_msg
                )
                return
            except Exception as e:
                # Other Brain processing errors
                error_msg = str(e)
                print(f"✗ Brain processing error: {error_msg}")
                await self.update_video_status(
                    ProcessingStage.FAILED,
                    0,
                    f"Brain processing failed: {error_msg}",
                    error=error_msg
                )
                await ws_manager.send_error(
                    self.video_id,
                    ProcessingStage.UNDERSTANDING,
                    "Brain processing failed",
                    error_msg
                )
                return
            
            if not ideas_path:
                await self.update_video_status(
                    ProcessingStage.FAILED,
                    0,
                    "No ideas could be generated from this video",
                    error="Brain processing failed"
                )
                await ws_manager.send_error(
                    self.video_id,
                    ProcessingStage.RANKING,
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
                ProcessingStage.UNDERSTANDING,
                ProcessingStage.GROUPING
            )
            
            # Stage 5: Ranking complete
            await self.update_video_status(
                ProcessingStage.RANKING,
                90,
                "Ranking complete"
            )
            await ws_manager.send_stage_complete(
                self.video_id,
                ProcessingStage.GROUPING,
                ProcessingStage.RANKING
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
            
            # Stage 6: Cleanup local files (after all stages that need them)
            print(f"🗑️  Cleaning up local files...")
            try:
                # Get file paths from transcript
                with open(transcript_path, 'r') as f:
                    transcript_data = json.load(f)
                
                video_path = Path(transcript_data.get('video_file_path', ''))
                audio_path = transcript_path.parent / f"{yt_id}_audio.mp3"
                
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
                # Don't fail the pipeline if cleanup fails
            
            # Stage 7: Complete (Atomic)
            # 1. Update SQLite status
            await self.update_video_status(
                ProcessingStage.COMPLETE,
                100,
                f"Processing complete! {ideas_data.get('ideas_count', 0)} ideas generated."
            )
            
            # 2. Mark complete in Supabase (atomic: status + progress + timestamp)
            try:
                VideoRepository.mark_completed(self.video_id)
                print(f"✓ Marked video {self.video_id} as COMPLETE in Supabase")
            except Exception as e:
                print(f"⚠ Warning: Supabase completion update failed: {e}")
            
            # 3. Send WebSocket completion event
            await ws_manager.send_complete(
                self.video_id,
                ideas_data.get('ideas_count', 0)
            )
            
            # 4. Update project status to READY
            try:
                from api.project_repository import ProjectRepository
                # Get video to find project_id
                with get_db() as db:
                    video = db.query(Video).filter(Video.id == self.video_id).first()
                    if video and video.project_id:
                        ProjectRepository.update_project(
                            video.project_id,
                            status='ready',
                            ideas_count=ideas_data.get('ideas_count', 0)
                        )
                        print(f"✓ Updated project {video.project_id} to READY with {ideas_data.get('ideas_count', 0)} ideas")
            except Exception as e:
                print(f"⚠ Warning: Project status update failed: {e}")
                # Don't fail pipeline if project update fails
            
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

