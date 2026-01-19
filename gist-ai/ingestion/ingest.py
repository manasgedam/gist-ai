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
        """
        print(f"Downloading from: {youtube_url}")
        
        # Download video file (for stitcher later)
        video_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': str(self.output_dir / '%(id)s_video.%(ext)s'),
            'quiet': False,
        }
        
        with yt_dlp.YoutubeDL(video_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            video_id = info['id']
            video_path = self.output_dir / f"{video_id}_video.mp4"
        
        print(f"Video downloaded: {video_path}")
        
        # Download audio (for transcription)
        audio_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(self.output_dir / '%(id)s_audio.%(ext)s'),
            'quiet': False,
        }
        
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            ydl.extract_info(youtube_url, download=True)
            audio_path = self.output_dir / f"{video_id}_audio.mp3"
        
        print(f"Audio downloaded: {audio_path}")
        
        return audio_path, video_path, video_id
    
    def transcribe(self, audio_path):
        """
        Transcribe audio with word-level timestamps
        Returns: transcript data structure
        """
        print("Transcribing audio (this may take a few minutes)...")
        
        # Transcribe with word-level timestamps
        result = self.model.transcribe(
            str(audio_path),
            word_timestamps=True,
            verbose=False
        )
        
        print("Transcription complete.")
        return result
    
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
        UPDATED: Downloads both video and audio
        """
        # Step 1: Download audio and video
        audio_path, video_path, video_id = self.download_audio(youtube_url)
        
        # Step 2: Transcribe
        transcript_result = self.transcribe(audio_path)
        
        # Step 3: Format as clean JSON
        output_data = self.format_output(transcript_result, video_id, youtube_url, video_path)
        
        # Step 4: Save
        json_path = self.save_json(output_data, video_id)
        
        # Note: Keep both audio and video files for later stages
        
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