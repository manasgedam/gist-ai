#!/usr/bin/env python3
"""
Extract Idea Clips - Creates separate audio files for each idea from Groq ideas JSON
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()


def extract_audio_segments(input_audio: str, output_file: str, segments: List[Dict]) -> bool:
    """
    Extract and concatenate multiple segments from audio file using ffmpeg filter_complex.
    Returns True if successful, False otherwise.
    """
    if not segments:
        return False
    
    # Build filter_complex command for multiple segments
    filter_parts = []
    concat_inputs = []
    
    for i, segment in enumerate(segments):
        start = segment['start_seconds']
        end = segment['end_seconds']
        duration = end - start
        
        # Create a trim filter for each segment
        filter_parts.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]")
        concat_inputs.append(f"[a{i}]")
    
    # Concatenate all segments
    concat_filter = f"{''.join(concat_inputs)}concat=n={len(segments)}:v=0:a=1[out]"
    filter_parts.append(concat_filter)
    
    filter_complex = ';'.join(filter_parts)
    
    cmd = [
        'ffmpeg',
        '-i', input_audio,
        '-filter_complex', filter_complex,
        '-map', '[out]',
        '-y',  # Overwrite output file
        output_file
    ]
    
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"    ❌ Error extracting segments: {e.stderr.decode()[:200]}")
        return False
    except FileNotFoundError:
        print("    ❌ ffmpeg not found. Please install ffmpeg first.")
        return False


def extract_idea_clips(
    output_dir: str,
    video_id: str = None,
    model: str = "groq"
) -> List[str]:
    """
    Extract separate audio clips for each idea from the ideas JSON file.
    
    Args:
        output_dir: Directory containing audio and ideas files
        video_id: Optional specific video ID to process
        model: Model type to use (groq or local)
    
    Returns:
        List of created audio file paths
    """
    output_path = Path(output_dir)
    
    if not output_path.exists():
        raise FileNotFoundError(f"Output directory not found: {output_dir}")
    
    # Find all idea files for the specified model
    idea_files = {}
    for file in output_path.glob(f"*_ideas_{model}.json"):
        parts = file.stem.split(f"_ideas_{model}")
        if len(parts) >= 1:
            vid_id = parts[0]
            
            if video_id and vid_id != video_id:
                continue
            
            idea_files[vid_id] = str(file)
    
    if not idea_files:
        print(f"No {model} idea files found in {output_dir}")
        return []
    
    output_files = []
    
    for vid_id, ideas_file in idea_files.items():
        print(f"\n{'='*60}")
        print(f"Processing video: {vid_id}")
        print(f"{'='*60}")
        
        # Find the source audio file
        audio_file = output_path / f"{vid_id}.mp3"
        if not audio_file.exists():
            # Try other formats
            for ext in ['.m4a', '.wav', '.aac', '.mp4']:
                alt_audio = output_path / f"{vid_id}{ext}"
                if alt_audio.exists():
                    audio_file = alt_audio
                    break
        
        if not audio_file.exists():
            print(f"  ⚠️  Audio file not found for {vid_id}")
            continue
        
        print(f"  🎵 Source audio: {audio_file.name}")
        
        # Load ideas
        ideas_data = load_json_file(ideas_file)
        ideas = ideas_data.get("ideas", [])
        
        print(f"  📊 Found {len(ideas)} ideas")
        
        if not ideas:
            print(f"  ⚠️  No ideas found")
            continue
        
        # Create clips directory
        clips_dir = output_path / f"{vid_id}_clips"
        clips_dir.mkdir(exist_ok=True)
        
        # Extract each idea as a separate audio file
        for i, idea in enumerate(ideas):
            title = idea.get("title", f"Idea_{i+1}")
            segments = idea.get("segments", [])
            total_duration = idea.get("total_duration_seconds", 0)
            
            if not segments:
                print(f"\n  [{i+1}/{len(ideas)}] ⚠️  Skipping '{title}' - no segments")
                continue
            
            print(f"\n  [{i+1}/{len(ideas)}] Processing: {title}")
            print(f"    Segments: {len(segments)}, Duration: {total_duration:.1f}s")
            
            # Create sanitized filename
            safe_title = sanitize_filename(title)
            output_file = clips_dir / f"{i+1:02d}_{safe_title}.mp3"
            
            # Extract and concatenate segments
            if extract_audio_segments(str(audio_file), str(output_file), segments):
                print(f"    ✅ Created: {output_file.name}")
                output_files.append(str(output_file))
                
                # Create metadata file for this clip
                metadata = {
                    "video_id": vid_id,
                    "idea_index": i,
                    "title": title,
                    "description": idea.get("description", ""),
                    "segment_count": len(segments),
                    "total_duration_seconds": total_duration,
                    "segments": segments,
                    "reasoning": idea.get("reasoning", ""),
                    "transcript_excerpt": idea.get("transcript_excerpt", ""),
                    "created_at": datetime.now().isoformat()
                }
                
                metadata_file = clips_dir / f"{i+1:02d}_{safe_title}_metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
            else:
                print(f"    ❌ Failed to create clip")
        
        print(f"\n  📁 All clips saved to: {clips_dir.name}/")
    
    return output_files


def main():
    """Main entry point for the clip extractor."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract separate audio clips for each idea from Groq ideas JSON"
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="./output",
        help="Directory containing audio and idea files (default: ./output)"
    )
    parser.add_argument(
        "--video-id",
        "-v",
        help="Specific video ID to process (optional, processes all if not specified)"
    )
    parser.add_argument(
        "--model",
        "-m",
        default="groq",
        choices=["groq", "local"],
        help="Model type to use (default: groq)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Idea Clip Extractor - Creating Audio Files for Each Idea")
    print("=" * 60)
    
    try:
        output_files = extract_idea_clips(
            output_dir=args.output_dir,
            video_id=args.video_id,
            model=args.model
        )
        
        print("\n" + "=" * 60)
        if output_files:
            print(f"✅ Successfully created {len(output_files)} audio clip(s)")
        else:
            print("⚠️  No audio clips were created")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
