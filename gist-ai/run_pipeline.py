"""
Gist AI - Unified Pipeline
Runs full pipeline: YouTube URL → Short video clips

Usage:
  python run_pipeline.py "https://youtube.com/..." --mode groq
  python run_pipeline.py "https://youtube.com/..." --mode local --skip-stitch
"""

import sys
import argparse
from pathlib import Path
import json

# Import components
from ingestion.ingest import VideoIngestion
from brain.brain import Brain
from stitcher.stitch import Stitcher


class GistPipeline:
    def __init__(self, mode="groq", skip_stitch=False):
        self.mode = mode
        self.skip_stitch = skip_stitch
        self.output_dir = Path("output")
        
        print("=" * 60)
        print("GIST AI PIPELINE")
        print("=" * 60)
        print(f"Mode: {mode}")
        print(f"Skip stitcher: {skip_stitch}")
        print()
    
    def print_stage(self, stage_num, stage_name):
        """Print stage header"""
        print(f"\n{'=' * 60}")
        print(f"STAGE {stage_num}: {stage_name}")
        print("=" * 60)
    
    def print_success(self, message):
        """Print success message"""
        print(f"✓ {message}")
    
    def print_error(self, message):
        """Print error message"""
        print(f"✗ ERROR: {message}")
    
    def print_warning(self, message):
        """Print warning message"""
        print(f"⚠ WARNING: {message}")
    
    def run_ingestion(self, youtube_url):
        """
        STAGE 1: Ingestion
        Returns: (transcript_path, video_id) or (None, None) on failure
        UPDATED: Better edge case handling
        """
        self.print_stage(1, "INGESTION")
        
        try:
            ingestion = VideoIngestion(output_dir=self.output_dir)
            transcript_path = ingestion.process(youtube_url)
            
            # Extract video_id from transcript
            with open(transcript_path, 'r') as f:
                data = json.load(f)
                video_id = data['video_id']
            
            self.print_success(f"Ingestion complete: {transcript_path}")
            return transcript_path, video_id
            
        except RuntimeError as e:
            # User-friendly error messages
            error_msg = str(e)
            if "Invalid URL" in error_msg or "unavailable" in error_msg:
                self.print_error("Video unavailable")
                print("  Possible reasons:")
                print("  - Video is private or deleted")
                print("  - Invalid YouTube URL")
                print("  - Video is region-locked")
                print("  - Age-restricted content")
            elif "No speech detected" in error_msg:
                self.print_error("No speech detected in video")
                print("  This video may be:")
                print("  - Music-only")
                print("  - Silent/ambient")
                print("  - Non-verbal content")
            else:
                self.print_error(f"Ingestion failed: {error_msg}")
            
            return None, None
            
        except Exception as e:
            self.print_error(f"Unexpected error during ingestion: {str(e)}")
            return None, None
    
    def run_brain(self, transcript_path):
        """
        STAGE 2: Brain
        Returns: ideas_path or None on failure
        UPDATED: Better edge case handling
        """
        self.print_stage(2, "BRAIN (Two-Stage Processing)")
        
        try:
            brain = Brain(mode=self.mode)
            ideas_data = brain.process(transcript_path)
            ideas_path = brain.save_output(ideas_data)
            
            # Edge case: No ideas found
            if ideas_data['ideas_count'] == 0:
                self.print_warning("No usable ideas found")
                print("\n  This is normal for:")
                print("  - Very short videos (<2 min)")
                print("  - Videos without clear standalone moments")
                print("  - Continuous narratives without natural breaks")
                print("\n  Try a different video with more distinct ideas.")
                return None
            
            self.print_success(f"Brain complete: Found {ideas_data['ideas_count']} ideas")
            return ideas_path
            
        except RuntimeError as e:
            error_msg = str(e)
            
            if "Ollama" in error_msg:
                self.print_error("Local LLM not running")
                print("\n  Start Ollama with: ollama serve")
                print("  Or switch to API mode: --mode groq")
            elif "API key" in error_msg or "billing" in error_msg:
                self.print_error("API authentication failed")
                print("\n  Check your .env file has:")
                if self.mode == 'openai':
                    print("  OPENAI_API_KEY=sk-...")
                    print("\n  Also verify billing at: https://platform.openai.com/account/billing")
                elif self.mode == 'groq':
                    print("  GROQ_API_KEY=gsk-...")
                    print("\n  Get free key at: https://console.groq.com")
            else:
                self.print_error(f"Brain failed: {error_msg}")
            
            return None
            
        except Exception as e:
            self.print_error(f"Unexpected error during Brain processing: {str(e)}")
            return None
    
    def run_stitcher(self, ideas_path, transcript_path):
        """
        STAGE 3: Stitcher
        Returns: list of output video paths or empty list on failure
        UPDATED: Better edge case handling
        """
        self.print_stage(3, "STITCHER")
        
        try:
            stitcher = Stitcher(output_dir=self.output_dir)
            output_paths = stitcher.process(ideas_path, transcript_path)
            
            self.print_success(f"Stitcher complete: Created {len(output_paths)} video clips")
            return output_paths
            
        except FileNotFoundError as e:
            if "Video file not found" in str(e):
                self.print_error("Video file missing")
                print("\n  The video file wasn't saved during ingestion.")
                print("  This can happen if:")
                print("  - Using old transcript JSON (re-run ingestion)")
                print("  - Video file was manually deleted")
                print("\n  Solution: Re-run full pipeline from start")
            else:
                self.print_error(f"File not found: {str(e)}")
            return []
            
        except RuntimeError as e:
            if "ffmpeg" in str(e).lower():
                self.print_error("ffmpeg error")
                print("\n  Make sure ffmpeg is installed: brew install ffmpeg")
            elif "No video clips were created" in str(e):
                self.print_error("All clips failed to create")
                print("\n  Check that:")
                print("  - Ideas JSON has valid timestamps")
                print("  - Video file is not corrupted")
            else:
                self.print_error(f"Stitcher failed: {str(e)}")
            return []
            
        except Exception as e:
            self.print_error(f"Unexpected error during stitching: {str(e)}")
            return []
    
    def print_summary(self, video_id, ideas_count, video_paths):
        """Print final summary"""
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        print(f"\nVideo ID: {video_id}")
        print(f"Ideas found: {ideas_count}")
        
        if self.skip_stitch:
            print(f"\nIdeas JSON: output/{video_id}_ideas_{self.mode}.json")
            print("(Stitcher skipped - use ideas JSON for your editor)")
        else:
            print(f"\nVideo clips created: {len(video_paths)}")
            if video_paths:
                print("\nOutput files:")
                for path in video_paths:
                    print(f"  - {path.name}")
        
        print("\n" + "=" * 60)
    
    def run(self, youtube_url):
        """
        Run full pipeline
        Returns: True on success, False on failure
        """
        # Validate URL
        if not youtube_url.startswith('http'):
            self.print_error("Invalid YouTube URL")
            return False
        
        # Stage 1: Ingestion
        transcript_path, video_id = self.run_ingestion(youtube_url)
        if not transcript_path:
            return False
        
        # Stage 2: Brain
        ideas_path = self.run_brain(transcript_path)
        if not ideas_path:
            self.print_warning("Pipeline stopped: No ideas to process")
            return False
        
        # Get ideas count for summary
        with open(ideas_path, 'r') as f:
            ideas_data = json.load(f)
            ideas_count = ideas_data['ideas_count']
        
        # Stage 3: Stitcher (optional)
        video_paths = []
        if not self.skip_stitch:
            video_paths = self.run_stitcher(ideas_path, transcript_path)
        
        # Summary
        self.print_summary(video_id, ideas_count, video_paths)
        
        return True


def main():
    parser = argparse.ArgumentParser(
        description='Gist AI - Turn long videos into short clips',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py "https://youtube.com/watch?v=abc123" --mode groq
  python run_pipeline.py "https://youtube.com/watch?v=abc123" --mode local
  python run_pipeline.py "https://youtube.com/watch?v=abc123" --mode groq --skip-stitch
        """
    )
    
    parser.add_argument(
        'url',
        help='YouTube URL to process'
    )
    
    parser.add_argument(
        '--mode',
        choices=['local', 'openai', 'groq'],
        default='groq',
        help='Brain mode: local (Ollama), openai (GPT), or groq (default: groq)'
    )
    
    parser.add_argument(
        '--skip-stitch',
        action='store_true',
        help='Skip stitcher stage (only generate ideas JSON)'
    )
    
    args = parser.parse_args()
    
    # Run pipeline
    pipeline = GistPipeline(mode=args.mode, skip_stitch=args.skip_stitch)
    success = pipeline.run(args.url)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()