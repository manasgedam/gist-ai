"""
Stitcher - Mechanical execution layer
Cuts and concatenates video segments based on timestamps
TEMPORARY: Will be replaced by full editor later
"""

import json
import subprocess
from pathlib import Path
import os


class Stitcher:
    def __init__(self, output_dir="output"):
        self.output_dir = Path(output_dir)
        self.temp_dir = self.output_dir / "temp"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Verify ffmpeg is installed
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE, 
                         check=True)
            print("Stitcher initialized (ffmpeg found)")
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("ffmpeg not found. Install with: brew install ffmpeg")
    
    def load_ideas(self, ideas_path):
        """Load ideas JSON from Brain output"""
        with open(ideas_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Loaded ideas: {ideas_path}")
        print(f"Total ideas: {data['ideas_count']}")
        
        return data
    
    def load_transcript(self, transcript_path):
        """Load transcript to get video file path"""
        with open(transcript_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    
    def extract_segment(self, video_path, start_seconds, end_seconds, output_path):
        """
        Extract one segment from video using ffmpeg
        Uses stream copy for speed (no re-encoding)
        """
        duration = end_seconds - start_seconds
        
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file
            '-ss', str(start_seconds),  # Start time
            '-i', str(video_path),  # Input video
            '-t', str(duration),  # Duration
            '-c', 'copy',  # Copy streams (fast, no re-encode)
            '-avoid_negative_ts', '1',  # Fix timestamp issues
            str(output_path)
        ]
        
        result = subprocess.run(cmd, 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg extract failed: {result.stderr}")
        
        return output_path
    
    def concatenate_segments(self, segment_paths, output_path):
        """
        Concatenate multiple video segments using ffmpeg concat demuxer
        This is faster than filter_complex for same codec segments
        """
        # Create concat file list
        concat_file = self.temp_dir / "concat_list.txt"
        
        with open(concat_file, 'w') as f:
            for path in segment_paths:
                # Use relative path if possible, absolute otherwise
                f.write(f"file '{path.absolute()}'\n")
        
        cmd = [
            'ffmpeg',
            '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',  # Copy streams (fast)
            str(output_path)
        ]
        
        result = subprocess.run(cmd,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg concat failed: {result.stderr}")
        
        return output_path
    
    def stitch_idea(self, video_path, idea, idea_index):
        """
        Stitch one complete idea from multiple segments
        Returns: path to output video
        """
        print(f"\n--- Stitching idea {idea_index}: '{idea['title']}' ---")
        print(f"Segments: {idea['segment_count']}")
        print(f"Total duration: {idea['total_duration_seconds']}s")
        
        segment_paths = []
        
        # Extract each segment
        for idx, segment in enumerate(idea['segments'], 1):
            print(f"  Extracting segment {idx}/{idea['segment_count']} "
                  f"[{segment['start_time_formatted']}-{segment['end_time_formatted']}]")
            
            temp_segment_path = self.temp_dir / f"idea_{idea_index}_seg_{idx}.mp4"
            
            self.extract_segment(
                video_path,
                segment['start_seconds'],
                segment['end_seconds'],
                temp_segment_path
            )
            
            segment_paths.append(temp_segment_path)
        
        # Concatenate segments
        print(f"  Concatenating {len(segment_paths)} segments...")
        
        # Sanitize filename (remove special chars)
        safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' 
                           for c in idea['title'])
        safe_title = safe_title[:50]  # Limit length
        
        output_filename = f"idea_{idea_index}_{safe_title}.mp4"
        output_path = self.output_dir / output_filename
        
        if len(segment_paths) == 1:
            # Single segment, just rename
            segment_paths[0].rename(output_path)
        else:
            # Multiple segments, concatenate
            self.concatenate_segments(segment_paths, output_path)
        
        print(f"  ✓ Created: {output_path}")
        
        return output_path
    
    def cleanup_temp_files(self):
        """Remove temporary segment files"""
        print("\nCleaning up temporary files...")
        for file in self.temp_dir.glob("*.mp4"):
            file.unlink()
        for file in self.temp_dir.glob("*.txt"):
            file.unlink()
    
    def process(self, ideas_path, transcript_path):
        """
        Full stitcher pipeline
        Input: ideas JSON, transcript JSON
        Output: Multiple MP4 files (one per idea)
        """
        # Load data
        ideas_data = self.load_ideas(ideas_path)
        transcript_data = self.load_transcript(transcript_path)
        
        # Get video file path
        video_path = Path(transcript_data['video_file_path'])
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        print(f"Source video: {video_path}")
        
        # Process each idea
        output_paths = []
        
        for idx, idea in enumerate(ideas_data['ideas'], 1):
            try:
                output_path = self.stitch_idea(video_path, idea, idx)
                output_paths.append(output_path)
            except Exception as e:
                print(f"  ✗ Failed to stitch idea {idx}: {e}")
                continue
        
        # Cleanup
        self.cleanup_temp_files()
        
        print(f"\n✓ Stitching complete")
        print(f"✓ Created {len(output_paths)} video clips")
        
        return output_paths


# Command-line usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python stitch.py <ideas_json_path> <transcript_json_path>")
        print("\nExample:")
        print("  python stitch.py output/VIDEO_ID_ideas_groq.json output/VIDEO_ID_transcript.json")
        sys.exit(1)
    
    ideas_path = sys.argv[1]
    transcript_path = sys.argv[2]
    
    stitcher = Stitcher()
    output_paths = stitcher.process(ideas_path, transcript_path)
    
    print("\nOutput files:")
    for path in output_paths:
        print(f"  - {path}")