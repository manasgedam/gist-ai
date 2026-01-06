import json
import subprocess
import os
import re
import sys

def slugify(text):
    """Converts titles to file-safe names (e.g., 'Viral Hook!' -> 'viral_hook')"""
    return re.sub(r'(?u)[^-\w.]', '_', text.strip().lower())

def merge_intervals(intervals):
    """Merges overlapping timestamps to ensure smooth narrative flow."""
    if not intervals: return []
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for current in intervals[1:]:
        prev_start, prev_end = merged[-1]
        curr_start, curr_end = current
        if curr_start <= prev_end: 
            merged[-1] = (prev_start, max(prev_end, curr_end))
        else:
            merged.append(current)
    return merged

def stitch_idea_video(video_path, idea_data, output_path):
    """
    Cuts video segments with frame-accurate precision and 
    professional audio/video fades.
    """
    raw_timestamps = idea_data.get('timestamps', [])
    if not raw_timestamps:
        return False

    merged_timestamps = merge_intervals(raw_timestamps)
    
    # Calculate Total Duration
    total_duration = sum(end - start for start, end in merged_timestamps)
    
    # HARD CAP: 85 Seconds (Optimized for Attention Spans)
    if total_duration > 85.0:
        diff = total_duration - 85.0
        last_s, last_e = merged_timestamps[-1]
        merged_timestamps[-1] = (last_s, last_e - diff)
        total_duration = 85.0

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    filter_str = ""
    concat_str = ""
    fade_duration = 0.5 
    
    for i, (start, end) in enumerate(merged_timestamps):
        # Adding 0.2s padding to prevent "cutting off" the last word
        b_start = max(0, start) 
        b_end = end + 0.2
        seg_duration = b_end - b_start
        
        filter_str += f"[0:v]trim=start={b_start}:duration={seg_duration},setpts=PTS-STARTPTS[v{i}]; "
        filter_str += f"[0:a]atrim=start={b_start}:duration={seg_duration},asetpts=PTS-STARTPTS[a{i}]; "
        concat_str += f"[v{i}][a{i}]"

    # Concatenate segments and apply professional Fade Out
    filter_str += f"{concat_str}concat=n={len(merged_timestamps)}:v=1:a=1[cv][ca]; "
    filter_str += f"[cv]fade=t=out:st={total_duration - fade_duration}:d={fade_duration}[outv]; "
    filter_str += f"[ca]afade=t=out:st={total_duration - fade_duration}:d={fade_duration}[outa]"

    command = [
        "ffmpeg", "-y", "-i", video_path,
        "-filter_complex", filter_str,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-crf", "18", # CRF 18 is near-lossless quality
        "-preset", "slow",               # Slower preset = better compression/quality ratio
        "-movflags", "+faststart",       # Optimized for web/mobile playback
        output_path
    ]

    try:
        # Run with capture_output=True to keep console clean unless there's an error
        subprocess.run(command, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg Error for {output_path}: {e.stderr.decode()}")
        return False

def process_batch_from_map(map_path):
    """Logic to process an entire knowledge map file."""
    if not os.path.exists(map_path):
        return
    
    video_id = os.path.basename(map_path).replace("_map.json", "")
    video_file = os.path.join("downloads", f"{video_id}.mp4")

    if not os.path.exists(video_file):
        print(f"❌ Source video missing: {video_file}")
        return

    with open(map_path, 'r') as f:
        knowledge_map = json.load(f)

    print(f"🚀 Stitching {len(knowledge_map)} segments for {video_id}...")

    for index, idea in enumerate(knowledge_map):
        title_slug = slugify(idea.get('title', 'clip'))
        output_filename = f"exports/{video_id}/{index+1}_{title_slug}.mp4"
        
        if stitch_idea_video(video_file, idea, output_filename):
            print(f"   ✅ Created: {output_filename}")

if __name__ == "__main__":
    # Logic for standalone usage
    map_files = [f for f in os.listdir("downloads") if f.endswith("_map.json")]
    if not map_files:
        print("❌ No maps found in downloads/")
        sys.exit(1)

    # Process the most recent map
    map_files.sort(key=lambda x: os.path.getmtime(os.path.join("downloads", x)), reverse=True)
    process_batch_from_map(os.path.join("downloads", map_files[0]))