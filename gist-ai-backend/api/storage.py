"""
Storage service for uploading files to Cloudflare R2
"""

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from boto3.s3.transfer import TransferConfig
import os
import time
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
        
        # Configure boto3 for R2 with production-grade settings
        # Cloudflare R2 has different characteristics than AWS S3:
        # - Higher latency (CDN-backed)
        # - Stricter connection limits
        # - Better performance with fewer, larger chunks
        config = Config(
            region_name='auto',
            signature_version='s3v4',
            
            # CRITICAL: Retry configuration for transient failures
            retries={
                'max_attempts': 5,          # Increased from 3 for R2 reliability
                'mode': 'adaptive',         # Exponential backoff
                'total_max_attempts': 5
            },
            
            # CRITICAL: Timeouts tuned for Cloudflare R2
            connect_timeout=30,             # Increased from 10s (R2 CDN routing)
            read_timeout=600,               # Increased from 300s (10min for large parts)
            
            # S3-specific configuration
            s3={
                'addressing_style': 'path',
                'payload_signing_enabled': True,
                'use_accelerate_endpoint': False
            },
            
            # TCP keepalive to prevent connection drops
            tcp_keepalive=True
        )
        
        # Initialize S3 client (R2 is S3-compatible)
        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=config
        )
        
        # CRITICAL: Transfer configuration optimized for Cloudflare R2
        # Research shows R2 performs best with:
        # - Larger chunks (16-100MB) = fewer network round-trips
        # - Lower concurrency (3-5) = prevents connection exhaustion
        #
        # Example: 50MB file
        # - Old (8MB chunks): 7 parts
        # - New (16MB chunks): 4 parts = 57% fewer round-trips
        self.transfer_config = TransferConfig(
            # Start multipart upload for files > 20MB
            multipart_threshold=20 * 1024 * 1024,   # 20MB
            
            # CRITICAL: 16MB chunks (optimal for R2)
            multipart_chunksize=16 * 1024 * 1024,   # 16MB per part
            
            # CRITICAL: Lower concurrency for R2 (prevents connection exhaustion)
            max_concurrency=3,                       # R2 performs better with 3-5
            
            # Enable threading for async I/O
            use_threads=True,
            
            # Increase I/O chunk size for better throughput
            io_chunksize=256 * 1024                 # 256KB read chunks
        )
    
    def upload_file(self, local_path: str, r2_key: str, content_type: Optional[str] = None) -> Optional[str]:
        """
        Upload a file to R2 with retry logic and graceful error handling
        
        Args:
            local_path: Path to local file
            r2_key: Key in R2 bucket (e.g., 'videos/abc123/original.mp4')
            content_type: MIME type (auto-detected if not provided)
        
        Returns:
            Public URL to the uploaded file, or None if upload failed
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
        file_size_mb = file_size / 1024 / 1024
        
        # Calculate expected number of parts for multipart upload
        if file_size > self.transfer_config.multipart_threshold:
            num_parts = (file_size // self.transfer_config.multipart_chunksize) + 1
            print(f"  → Uploading {Path(local_path).name} ({file_size_mb:.1f} MB, ~{num_parts} parts)")
        else:
            print(f"  → Uploading {Path(local_path).name} ({file_size_mb:.1f} MB, single-part)")
        
        # Retry configuration
        max_retries = 3
        base_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Upload to R2 with automatic retry logic (handled by boto3 Config)
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
                
                # Return public URL
                return f"{self.public_url}/{r2_key}"
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_msg = e.response['Error'].get('Message', str(e))
                
                # Check if this is a retryable error
                is_last_attempt = (attempt == max_retries - 1)
                
                if is_last_attempt:
                    print(f"  ✗ Upload failed after {max_retries} attempts: {error_code} - {error_msg}")
                    self._abort_multipart_uploads(r2_key)
                    return None
                else:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    print(f"  ⚠️  Attempt {attempt + 1} failed: {error_code}")
                    print(f"  → Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                
                # Check if this is a connection error (retryable)
                is_connection_error = any(keyword in error_type.lower() for keyword in [
                    'connection', 'timeout', 'socket', 'network'
                ])
                is_last_attempt = (attempt == max_retries - 1)
                
                if is_connection_error and not is_last_attempt:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    print(f"  ⚠️  Attempt {attempt + 1} failed: {error_type}")
                    print(f"  → Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"  ✗ Upload failed: {error_type}: {error_msg}")
                    self._abort_multipart_uploads(r2_key)
                    return None
        
        # Should never reach here, but just in case
        return None
    
    def _abort_multipart_uploads(self, r2_key: str):
        """
        Abort any in-progress multipart uploads for a given key
        Prevents orphaned multipart uploads in R2
        """
        try:
            # List in-progress multipart uploads
            response = self.client.list_multipart_uploads(
                Bucket=self.bucket,
                Prefix=r2_key
            )
            
            if 'Uploads' in response and response['Uploads']:
                for upload in response['Uploads']:
                    if upload['Key'] == r2_key:
                        upload_id = upload['UploadId']
                        print(f"  → Aborting multipart upload: {upload_id[:16]}...")
                        
                        self.client.abort_multipart_upload(
                            Bucket=self.bucket,
                            Key=r2_key,
                            UploadId=upload_id
                        )
                        print(f"  ✓ Multipart upload aborted")
        except Exception as cleanup_error:
            # Don't fail if cleanup fails, just log it
            print(f"  ⚠️  Cleanup warning: {cleanup_error}")
    
    def upload_video(self, video_id: str, local_path: str, file_type: str) -> Optional[str]:
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
    
    def upload_clip(self, idea_id: str, local_path: str) -> Optional[str]:
        """
        Upload a generated clip to R2
        
        Args:
            idea_id: Idea UUID
            local_path: Path to local clip file
        
        Returns:
            Public URL to the uploaded clip, or None if upload failed
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
