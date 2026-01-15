import os
import logging
from faster_whisper import WhisperModel

# Configure logging for professional monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriberService:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        """
        Initializes the Whisper model. 
        Industry Tip: 'base' is great for testing; 'small' or 'medium' for production.
        """
        try:
            logger.info(f"Loading Whisper model: {model_size} on {device}...")
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise RuntimeError("Model initialization failed.")

    def transcribe(self, file_path: str):
        """
        Transcribes audio/video and returns structured data with timestamps.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found at {file_path}")

        try:
            logger.info(f"Starting transcription for {file_path}...")
            segments, info = self.model.transcribe(file_path, beam_size=5)
            
            logger.info(f"Detected language: {info.language} with probability {info.language_probability:.2f}")

            results = []
            for segment in segments:
                results.append({
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                    "text": segment.text.strip()
                })
            
            return {
                "language": info.language,
                "duration": info.duration,
                "segments": results
            }
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise