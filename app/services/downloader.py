import yt_dlp
import os
import uuid
import logging

logger = logging.getLogger(__name__)

class DownloaderService:
    def __init__(self, download_path="data/uploads"):
        self.download_path = download_path
        os.makedirs(self.download_path, exist_ok=True)

    def download_youtube_video(self, url: str) -> str:
        """
        Downloads a YouTube video and returns the local file path.
        """
        file_id = str(uuid.uuid4())
        # Industry standard: Download best quality video/audio and merge into mp4
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': f'{self.download_path}/{file_id}_%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

        try:
            logger.info(f"Downloading YouTube video: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return filename
        except Exception as e:
            logger.error(f"YouTube Download Failed: {e}")
            raise