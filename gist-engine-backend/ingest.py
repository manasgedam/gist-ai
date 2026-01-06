import os
import glob
import subprocess
import yt_dlp
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MAX_AUDIO_SIZE_MB = 25

def compress_audio(input_path: str) -> str:
    """
    Compresses audio file if it exceeds the size limit.
    Target properties: Mono, 16kHz, 64kbps (optimized for Whisper).
    """
    try:
        file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
    except FileNotFoundError:
        print(f"⚠️ Warning: File not found for compression: {input_path}")
        return input_path

    # If it's already under the limit (with 1MB buffer), don't bother compressing
    if file_size_mb < (MAX_AUDIO_SIZE_MB - 1):
        return input_path

    compressed_path = input_path.rsplit('.', 1)[0] + "_lowres.mp3"
    print(f"📉 Audio is {file_size_mb:.2f}MB. Compressing to stay under {MAX_AUDIO_SIZE_MB}MB limit...")
    
    # -aq 8 or -b:a 64k creates a very small file suitable for Whisper
    # Standardizing on subprocess.run for better control/logging if needed
    cmd = [
        "ffmpeg", "-i", input_path,
        "-vn",              # No video
        "-ar", "16000",     # 16kHz sampling
        "-ac", "1",         # Mono channel
        "-b:a", "64k",      # 64k bitrate
        compressed_path,
        "-y"                # Overwrite
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        new_size = os.path.getsize(compressed_path) / (1024 * 1024)
        print(f"✅ Compression complete: {new_size:.2f}MB")
        return compressed_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Compression failed: {e}")
        return input_path

def download_video_and_audio(url: str):
    """
    Downloads video and best available audio using yt-dlp.
    Falls back to ffmpeg extraction if audio isn't separate.
    """
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    ydl_opts = {
        # 🍪 Auth: Keep this to bypass "Video Unavailable"
        'cookiesfrombrowser': ('brave',), 
        
        # 🛠️ JS RUNTIME: Changed from ['deno'] to a dictionary format
        'js_runtimes': {'deno': {}}, 
        
        # 🛠️ REMOTE COMPONENTS: Also ensure this is a list
        'remote_components': ['ejs:github'],
        
        'format': 'bestvideo[vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'noplaylist': True,
        'keepvideo': True,
        'nocheckcertificate': True,
    }
        
    video_id = None
    video_path = None
    audio_path = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info['id']
            video_path = f"downloads/{video_id}.mp4"

            # Search for downloaded audio files
            possible_files = glob.glob(f"downloads/{video_id}.*")
            for f in possible_files:
                if f.endswith(('.m4a', '.mp3', '.webm')) and f != video_path:
                    audio_path = f
                    break
            
            # Fallback: Extract from video if no separate audio found
            if not audio_path or not os.path.exists(audio_path):
                print(f"ℹ️ Extracting audio from video...")
                extracted_audio = f"downloads/{video_id}_extracted.m4a"
                cmd = [
                    "ffmpeg", "-i", video_path,
                    "-vn", "-acodec", "copy",
                    extracted_audio, "-y"
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                audio_path = extracted_audio
                
            # Compress before returning to ensure it fits API limits
            audio_path = compress_audio(audio_path)
            
            return video_id, video_path, audio_path

    except Exception as e:
        print(f"❌ Download failed: {e}")
        # Return what we have or rethink error handling, keeping strict signature for now
        return video_id, video_path, audio_path

def transcribe_with_groq(audio_path: str, video_id: str):
    """
    Sends the audio file to Groq for transcription using Whisper.
    """
    if not audio_path or not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found at {audio_path}")

    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    if file_size_mb >= MAX_AUDIO_SIZE_MB:
        print(f"⚠️ Warning: File is still {file_size_mb:.2f}MB. Groq might reject it.")

    print(f"🎙️ Sending to Groq: {audio_path} ({file_size_mb:.2f}MB)")
    
    try:
        with open(audio_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), file.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
            )
        
        transcript_path = f"downloads/{video_id}_transcript.json"
        with open(transcript_path, "w") as f:
            f.write(transcription.model_dump_json(indent=4))
        
        print(f"✅ Transcription saved to: {transcript_path}")
        return transcript_path
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        raise e