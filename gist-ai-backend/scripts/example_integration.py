"""
Example script showing how to integrate Supabase + R2 into the pipeline

This demonstrates the dual-write pattern for safe migration:
1. Write to SQLite (existing)
2. Also write to Supabase (new)
3. Upload files to R2 (new)
"""

import asyncio
from pathlib import Path
from api.supabase_client import VideoRepository, IdeaRepository, SegmentRepository
from api.storage import r2_storage


async def example_video_processing():
    """Example of how to integrate Supabase + R2 into video processing"""
    
    # Step 1: Create video record in Supabase when user submits URL
    video = VideoRepository.create_video(
        source_url="https://youtube.com/watch?v=example",
        source_type="youtube",
        youtube_id="example"
    )
    video_id = video['id']
    print(f"✓ Created video in Supabase: {video_id}")
    
    # Step 2: Update processing state as pipeline progresses
    VideoRepository.update_processing_state(
        video_id,
        status="INGESTING",
        current_stage="INGESTING",
        progress=10
    )
    print("✓ Updated to INGESTING")
    
    # Step 3: After ingestion, upload files to R2 and save URLs
    # Simulate local files
    local_video = Path("output/example_video.mp4")
    local_audio = Path("output/example_audio.mp3")
    local_transcript = Path("output/example_transcript.json")
    
    if local_video.exists():
        # Upload to R2
        video_url = r2_storage.upload_video(video_id, str(local_video), 'original')
        audio_url = r2_storage.upload_video(video_id, str(local_audio), 'audio')
        transcript_url = r2_storage.upload_video(video_id, str(local_transcript), 'transcript')
        
        # Save URLs to Supabase
        VideoRepository.set_video_urls(
            video_id,
            original_url=video_url,
            audio_url=audio_url,
            transcript_url=transcript_url
        )
        print(f"✓ Uploaded files to R2 and saved URLs")
        print(f"  Video: {video_url}")
    
    # Step 4: Save video metadata
    VideoRepository.set_video_metadata(
        video_id,
        title="Example Video",
        duration=120.5,
        language="en"
    )
    print("✓ Saved metadata")
    
    # Step 5: Continue processing stages
    for stage, progress in [("TRANSCRIBING", 30), ("UNDERSTANDING", 50), ("GROUPING", 70), ("RANKING", 90)]:
        VideoRepository.update_processing_state(
            video_id,
            status=stage,
            current_stage=stage,
            progress=progress
        )
        print(f"✓ Updated to {stage}")
        await asyncio.sleep(0.1)  # Simulate processing time
    
    # Step 6: Save ideas and segments
    idea = IdeaRepository.create_idea(
        video_id=video_id,
        rank=1,
        title="Example Idea",
        description="This is an example idea",
        strength="strong",
        viral_potential=0.85,
        total_duration=45.0,
        segment_count=2
    )
    idea_id = idea['id']
    print(f"✓ Created idea: {idea_id}")
    
    # Create segments for the idea
    segments = [
        {
            'idea_id': idea_id,
            'start_time': 10.0,
            'end_time': 30.0,
            'duration': 20.0,
            'sequence_order': 1,
            'purpose': 'hook'
        },
        {
            'idea_id': idea_id,
            'start_time': 50.0,
            'end_time': 75.0,
            'duration': 25.0,
            'sequence_order': 2,
            'purpose': 'resolution'
        }
    ]
    SegmentRepository.bulk_create_segments(segments)
    print(f"✓ Created {len(segments)} segments")
    
    # Step 7: Mark as complete
    VideoRepository.update_processing_state(
        video_id,
        status="COMPLETE",
        current_stage="COMPLETE",
        progress=100
    )
    print("✓ Processing complete!")
    
    # Step 8: Retrieve everything
    video_data = VideoRepository.get_video(video_id)
    ideas = IdeaRepository.get_ideas_for_video(video_id)
    print(f"\n✓ Retrieved video: {video_data['title']}")
    print(f"✓ Retrieved {len(ideas)} ideas")


if __name__ == "__main__":
    print("=== Supabase + R2 Integration Example ===\n")
    asyncio.run(example_video_processing())
    print("\n=== Example Complete ===")
