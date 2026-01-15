import logging
import json
from .services import downloader, reasoner, video_editor
from .database import SessionLocal
from . import models

logger = logging.getLogger(__name__)

class GistOrchestrator:
    def __init__(self, db_session_factory=SessionLocal):
        self.db_factory = db_session_factory
        # Initialize specialized service handlers
        self.dl = downloader.DownloaderService()
        # GistAIEngine handles transcription (using TranscriberService internally) and reasoning
        self.engine = reasoner.GistAIEngine()
        self.ed = video_editor.VideoEditorService()

    async def run_job(self, job_id: str, youtube_url: str):
        """The 'Master' function that runs the entire sequence."""
        db = self.db_factory()
        try:
            # 1. DOWNLOAD
            self._update_status(db, job_id, "DOWNLOADING")
            video_path = self.dl.download_youtube_video(youtube_url)
            
            # Update local path in DB
            video_entry = db.query(models.Video).filter(models.Video.id == job_id).first()
            if video_entry:
                video_entry.local_path = video_path
            db.commit()

            # 2. PROCESS (Transcribe + Reason)
            self._update_status(db, job_id, "PROCESSING")
            # engine.process_video returns (final_clips_data, transcript_segments)
            final_clips_data, transcript_segments = self.engine.process_video(video_path)

            # 3. SAVE TRANSCRIPTS
            self._save_transcripts(db, job_id, transcript_segments)

            # 4. EDIT (Stitching the first viral suggestion)
            self._update_status(db, job_id, "STITCHING")
            
            if final_clips_data:
                # We use the timestamps from the first AI-suggested clip
                first_clip_json = final_clips_data[0]
                if isinstance(first_clip_json, str):
                    clip_data = json.loads(first_clip_json)
                else:
                    clip_data = first_clip_json

                if "timestamps" in clip_data:
                    # Save "Clips" metadata to DB (Best effort mapping)
                    self._save_clips(db, job_id, clip_data["timestamps"])
                    
                    output_name = f"gist_{job_id}.mp4"
                    self.ed.stitch_clips(video_path, clip_data["timestamps"], output_name)
                    logger.info(f"✅ Gist Created for Job {job_id}")

            self._update_status(db, job_id, "COMPLETED")
            logger.info(f"✅ Job {job_id} completed successfully.")

        except Exception as e:
            logger.error(f"❌ Job {job_id} failed: {str(e)}")
            self._update_status(db, job_id, f"FAILED: {str(e)[:50]}")
        finally:
            db.close()

    def _update_status(self, db, job_id, status):
        video = db.query(models.Video).filter(models.Video.id == job_id).first()
        if video:
            video.status = status
            db.commit()

    def _save_transcripts(self, db, job_id, segments):
        # segments is a list of objects with start, end, text attributes
        db_segments = [
            models.Transcript(
                video_id=job_id, 
                start_time=s.start, 
                end_time=s.end, 
                content=s.text
            )
            for s in segments
        ]
        db.add_all(db_segments)
        db.commit()

    def _save_clips(self, db, job_id, timestamps):
        # timestamps is a list of dicts {'start': float, 'end': float}
        for i, ts in enumerate(timestamps):
            db_clip = models.Clip(
                video_id=job_id, 
                title=f"Viral Segment {i+1}", 
                start_time=ts['start'], 
                end_time=ts['end'], 
                hook_reason="Identified by GistAI"
            )
            db.add(db_clip)
        db.commit()