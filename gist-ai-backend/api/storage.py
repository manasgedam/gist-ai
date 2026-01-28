"""
Storage service for uploading files to Cloudflare R2
"""

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from boto3.s3.transfer import TransferConfig
import os
from pathlib import Path
from typing import Optional

class R2Storage:
    """Cloudflare R2 storage client"""
    
    def __init__(self):
        self.endpoint = os.getenv('R2_ENDPOINT')
        self.access_key = os.getenv('R2_ACCESS_KEY')
        self.secret_key = os.getenv('R2_SECRET_KEY')
        self.bucket = os.getenv('R2_BUCKET', 'gist-ai-storage')
        self.public_url = os.getenv('R2_PUBLIC_URL', 'https://gist-ai.r2.dev')
        
        # Configure boto3 for R2 with proper timeouts and retries
        config = Config(
            region_name='auto',
            signature_version='s3v4',
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            },
            # Increase timeouts for large file uploads
            connect_timeout=10,
            read_timeout=300,  # 5 minutes for large files
            # S3-specific configuration
            s3={
                'addressing_style': 'path'
            }
        )
        
        # Initialize S3 client (R2 is S3-compatible)
        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=config
        )
        
        # Transfer configuration for multipart uploads
        self.transfer_config = TransferConfig(
            multipart_threshold=8 * 1024 * 1024,  # 8MB
            max_concurrency=10,
            multipart_chunksize=8 * 1024 * 1024,  # 8MB chunks
            use_threads=True
        )
    
    def upload_file(self, local_path: str, r2_key: str, content_type: Optional[str] = None) -> str:
        """
        Upload a file to R2 and return the public URL
        
        Args:
            local_path: Path to local file
            r2_key: Key in R2 bucket (e.g., 'videos/abc123/original.mp4')
            content_type: MIME type (auto-detected if not provided)
        
        Returns:
            Public URL to the uploaded file
        """
        # Auto-detect content type if not provided
        if not content_type:
            ext = Path(local_path).suffix.lower()
            content_types = {
                '.mp4': 'video/mp4',
                '.mp3': 'audio/mpeg',
                '.json': 'application/json',
                '.webm': 'video/webm',
            }
            content_type = content_types.get(ext, 'application/octet-stream')
        
        # Get file size
        file_size = os.path.getsize(local_path)
        print(f"  → Uploading {Path(local_path).name} ({file_size / 1024 / 1024:.1f} MB)")
        
        try:
            # Upload to R2 with retry logic
            extra_args = {
                'ContentType': content_type,
                'ACL': 'public-read'  # Make file publicly accessible
            }
            
            self.client.upload_file(
                local_path,
                self.bucket,
                r2_key,
                ExtraArgs=extra_args,
                Config=self.transfer_config
            )
            
            print(f"  ✓ Upload complete")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error'].get('Message', str(e))
            print(f"  ✗ Upload failed: {error_code} - {error_msg}")
            raise Exception(f"R2 upload failed: {error_code} - {error_msg}")
        except Exception as e:
            print(f"  ✗ Upload failed: {str(e)}")
            raise Exception(f"R2 upload failed: {str(e)}")
        
        # Return public URL
        return f"{self.public_url}/{r2_key}"
    
    def upload_video(self, video_id: str, local_path: str, file_type: str) -> str:
        """
        Upload a video-related file to R2
        
        Args:
            video_id: Video UUID
            local_path: Path to local file
            file_type: 'original' | 'audio' | 'transcript'
        
        Returns:
            Public URL to the uploaded file
        """
        extensions = {
            'original': '.mp4',
            'audio': '.mp3',
            'transcript': '.json'
        }
        
        ext = extensions.get(file_type, Path(local_path).suffix)
        r2_key = f"videos/{video_id}/{file_type}{ext}"
        
        return self.upload_file(local_path, r2_key)
    
    def upload_clip(self, idea_id: str, local_path: str) -> str:
        """
        Upload a generated clip to R2
        
        Args:
            idea_id: Idea UUID
            local_path: Path to local clip file
        
        Returns:
            Public URL to the uploaded clip
        """
        r2_key = f"clips/{idea_id}.mp4"
        return self.upload_file(local_path, r2_key, content_type='video/mp4')
    
    def delete_file(self, r2_key: str):
        """Delete a file from R2"""
        self.client.delete_object(Bucket=self.bucket, Key=r2_key)
    
    def delete_video_files(self, video_id: str):
        """Delete all files for a video"""
        prefix = f"videos/{video_id}/"
        
        # List all objects with this prefix
        response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        
        if 'Contents' in response:
            for obj in response['Contents']:
                self.client.delete_object(Bucket=self.bucket, Key=obj['Key'])


# Singleton instance
r2_storage = R2Storage()
