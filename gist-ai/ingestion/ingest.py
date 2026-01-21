"""
Ingestion Brain - Fact-only layer
Converts YouTube video to timestamped transcript JSON
"""

import whisper
import yt_dlp
import json
import os
from pathlib import Path


class VideoIngestion:
    def __init__(self, output_dir="output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Load Whisper model (base = good balance of speed/accuracy)
        print("Loading Whisper model...")
        self.model = whisper.load_model("base")
        print("Model loaded.")
    
    def download_audio(self, youtube_url):
        """
        Download audio AND video from YouTube URL
        Returns: paths to audio and video files
        UPDATED: Better error handling
        """
        print(f"Downloading from: {youtube_url}")
        
        try:
            # Download video file (for stitcher later)
            print("  → Downloading video...")
            video_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': str(self.output_dir / '%(id)s_video.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(video_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                video_id = info['id']
                video_path = self.output_dir / f"{video_id}_video.mp4"
            
            if not video_path.exists():
                raise FileNotFoundError(f"Video file not created: {video_path}")
            
            print(f"  ✓ Video downloaded: {video_path.name}")
            
            # Download audio (for transcription)
            print("  → Downloading audio...")
            audio_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': str(self.output_dir / '%(id)s_audio.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(audio_opts) as ydl:
                ydl.extract_info(youtube_url, download=True)
                audio_path = self.output_dir / f"{video_id}_audio.mp3"
            
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not created: {audio_path}")
            
            print(f"  ✓ Audio downloaded: {audio_path.name}")
            
            return audio_path, video_path, video_id
            
        except yt_dlp.utils.DownloadError as e:
            raise RuntimeError(f"Download failed: Invalid URL or video unavailable - {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Download failed: {str(e)}")
    
    def transcribe(self, audio_path):
        """
        Transcribe audio with word-level timestamps
        Returns: transcript data structure
        UPDATED: Better progress indication
        """
        print("  → Transcribing audio (this may take a few minutes)...")
        
        try:
            # Transcribe with word-level timestamps
            result = self.model.transcribe(
                str(audio_path),
                word_timestamps=True,
                verbose=False
            )
            
            print(f"  ✓ Transcription complete ({len(result['segments'])} segments)")
            return result
            
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {str(e)}")
    
    def format_output(self, transcript_result, video_id, youtube_url, video_path):
        """
        Convert Whisper output to clean JSON structure
        FACTS ONLY - no interpretation
        UPDATED: Include video file path
        """
        segments = []
        
        for segment in transcript_result['segments']:
            segment_data = {
                'id': segment['id'],
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip(),
                'words': []
            }
            
            # Include word-level timestamps if available
            if 'words' in segment:
                for word in segment['words']:
                    segment_data['words'].append({
                        'word': word['word'].strip(),
                        'start': word['start'],
                        'end': word['end']
                    })
            
            segments.append(segment_data)
        
        # Build final output structure
        output = {
            'video_id': video_id,
            'source_url': youtube_url,
            'video_file_path': str(video_path),
            'language': transcript_result.get('language', 'unknown'),
            'duration': transcript_result['segments'][-1]['end'] if segments else 0,
            'segments': segments
        }
        
        return output
    
    def save_json(self, data, video_id):
        """Save transcript to JSON file"""
        output_path = self.output_dir / f"{video_id}_transcript.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Transcript saved: {output_path}")
        return output_path
    
    def process(self, youtube_url):
        """
        Full ingestion pipeline
        Input: YouTube URL
        Output: JSON file path
        UPDATED: Edge case handling
        """
        # Step 1: Download audio and video
        audio_path, video_path, video_id = self.download_audio(youtube_url)
        
        # Step 2: Transcribe
        transcript_result = self.transcribe(audio_path)
        
        # Step 3: Validate transcript quality
        if not transcript_result.get('segments'):
            raise RuntimeError("Transcription failed: No speech detected in video")
        
        duration = transcript_result['segments'][-1]['end'] if transcript_result['segments'] else 0
        
        # Edge case: Video too short
        if duration < 120:  # Less than 2 minutes
            print(f"\n  ⚠ WARNING: Video is very short ({duration:.0f}s)")
            print(f"  ⚠ Short videos rarely have complete standalone ideas")
            print(f"  ⚠ Continuing anyway, but Brain may find no ideas\n")
        
        # Edge case: Video too long
        if duration > 1800:  # More than 30 minutes
            print(f"\n  ⚠ WARNING: Video is very long ({duration/60:.1f} minutes)")
            print(f"  ⚠ This may take a while and cost more API credits")
            print(f"  ⚠ Consider processing shorter videos first\n")
        
        # Edge case: Language detection
        detected_language = transcript_result.get('language', 'unknown')
        if detected_language != 'en' and detected_language != 'unknown':
            print(f"\n  ⚠ WARNING: Detected language is '{detected_language}', not English")
            print(f"  ⚠ Brain prompts are in English and may not work well")
            print(f"  ⚠ Results may be unreliable\n")
        
        # Step 4: Format as clean JSON
        output_data = self.format_output(transcript_result, video_id, youtube_url, video_path)
        
        # Step 5: Save
        json_path = self.save_json(output_data, video_id)
        
        return json_path


# Command-line usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <youtube_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    
    ingestion = VideoIngestion()
    result_path = ingestion.process(url)
    
    print(f"\n✓ Ingestion complete")
    print(f"✓ Output: {result_path}")