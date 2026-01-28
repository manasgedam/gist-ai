# Supabase + R2 Integration Guide

## What We've Set Up

✅ **Backend:**

- `api/supabase_client.py` - Database client with repositories
- `api/storage.py` - R2 upload service
- `migrations/001_initial_schema.sql` - Database schema

✅ **Frontend:**

- `lib/supabase.ts` - Supabase client with TypeScript types
- Installed `@supabase/supabase-js`

✅ **Verified:**

- R2 connection working
- Supabase connection working
- Can query database

---

## Integration Pattern (Dual-Write)

For safe migration, we use a **dual-write pattern**:

1. **Write to SQLite** (existing) - keeps current system working
2. **Also write to Supabase** (new) - builds cloud data
3. **Upload to R2** (new) - stores files in cloud

This allows you to:

- Keep existing system running
- Build cloud data in parallel
- Switch over when ready
- Rollback if needed

---

## How to Integrate into Pipeline

### Option 1: Manual Integration (Recommended)

Add Supabase calls alongside existing SQLite calls in `api/pipeline_runner.py`:

```python
# After creating video in SQLite
try:
    VideoRepository.create_video(
        source_url=youtube_url,
        source_type='youtube',
        youtube_id=yt_id
    )
except Exception as e:
    print(f"Warning: Supabase write failed: {e}")

# After ingestion completes
try:
    # Upload files to R2
    video_url = r2_storage.upload_video(video_id, video_path, 'original')
    audio_url = r2_storage.upload_video(video_id, audio_path, 'audio')
    transcript_url = r2_storage.upload_video(video_id, transcript_path, 'transcript')

    # Save URLs to Supabase
    VideoRepository.set_video_urls(video_id, video_url, audio_url, transcript_url)
    VideoRepository.set_video_metadata(video_id, title, duration, language)
except Exception as e:
    print(f"Warning: R2 upload failed: {e}")

# Update processing state
try:
    VideoRepository.update_processing_state(
        video_id, status, current_stage, progress
    )
except Exception as e:
    print(f"Warning: Supabase update failed: {e}")
```

### Option 2: Run Example Script

See `example_supabase_integration.py` for a complete working example.

---

## Frontend Integration

### 1. Create Supabase Client Hook

```typescript
// lib/hooks/use-supabase-video.ts
import { useEffect, useState } from "react";
import { supabase, Video } from "@/lib/supabase";

export function useSupabaseVideo(videoId: string | null) {
  const [video, setVideo] = useState<Video | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!videoId) return;

    // Fetch initial data
    const fetchVideo = async () => {
      setLoading(true);
      const { data } = await supabase
        .from("videos")
        .select("*")
        .eq("id", videoId)
        .single();

      setVideo(data);
      setLoading(false);
    };

    fetchVideo();

    // Subscribe to realtime updates
    const channel = supabase
      .channel(`video:${videoId}`)
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "videos",
          filter: `id=eq.${videoId}`,
        },
        (payload) => {
          setVideo(payload.new as Video);
        },
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [videoId]);

  return { video, loading };
}
```

### 2. Use in Components

```typescript
// components/video-editor.tsx
import { useSupabaseVideo } from '@/lib/hooks/use-supabase-video'

export function VideoEditor() {
  const { video, loading } = useSupabaseVideo(videoId)

  // Video data updates automatically via Supabase Realtime!
  return (
    <div>
      <h1>{video?.title}</h1>
      <p>Status: {video?.status}</p>
      <p>Progress: {video?.progress}%</p>
      {video?.original_video_url && (
        <video src={video.original_video_url} />
      )}
    </div>
  )
}
```

---

## Testing

### Test Backend Integration

```bash
cd gist-ai-backend
python example_supabase_integration.py
```

Expected output:

```
=== Supabase + R2 Integration Example ===

✓ Created video in Supabase: abc-123-def
✓ Updated to INGESTING
✓ Uploaded files to R2 and saved URLs
  Video: https://gist-ai.r2.dev/videos/abc-123-def/original.mp4
✓ Saved metadata
✓ Updated to TRANSCRIBING
✓ Updated to UNDERSTANDING
✓ Updated to GROUPING
✓ Updated to RANKING
✓ Created idea: def-456-ghi
✓ Created 2 segments
✓ Processing complete!

✓ Retrieved video: Example Video
✓ Retrieved 1 ideas

=== Example Complete ===
```

### Test Frontend Integration

```bash
cd gist-ai-editor
# Add test component that uses useSupabaseVideo hook
npm run dev
```

---

## Migration Checklist

- [x] Setup Supabase account
- [x] Run database migration
- [x] Setup Cloudflare R2
- [x] Install dependencies
- [x] Create database client
- [x] Create storage client
- [x] Test connections
- [ ] Add dual-write to pipeline_runner.py
- [ ] Test end-to-end with real video
- [ ] Add frontend Supabase hooks
- [ ] Test realtime updates
- [ ] Monitor for errors
- [ ] Switch reads to Supabase
- [ ] Remove SQLite writes

---

## Benefits You'll Get

### Immediate

- ✅ Cloud backup of all data
- ✅ R2 CDN for fast video delivery
- ✅ No file system limits

### After Full Migration

- ✅ Realtime UI updates (no WebSocket needed)
- ✅ Multi-device sync
- ✅ Better scalability
- ✅ Built-in REST API
- ✅ Row-level security

---

## Cost Monitoring

### Current Usage (Free Tier)

- Supabase: 0 / 500 MB database
- R2: 0 / 10 GB storage

### Set Alerts

1. Supabase: Project Settings → Usage → Set alert at 400 MB
2. Cloudflare: R2 → Usage → Set alert at 8 GB

---

## Next Steps

1. **Test the example script** to verify everything works
2. **Add dual-write** to one endpoint (e.g., video creation)
3. **Test with real video** submission
4. **Gradually add** to other endpoints
5. **Monitor** for any errors
6. **Switch reads** to Supabase when confident
7. **Remove SQLite** writes when fully migrated

---

## Troubleshooting

### "Supabase connection failed"

- Check `.env` has correct `SUPABASE_URL` and `SUPABASE_KEY`
- Verify project is not paused in Supabase dashboard

### "R2 upload failed"

- Check `.env` has correct R2 credentials
- Verify bucket exists and has public access enabled

### "Frontend can't connect"

- Check `.env.local` has `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- Restart Next.js dev server after adding env vars

---

## Support

If you encounter issues:

1. Check the example script works
2. Verify environment variables
3. Check Supabase and R2 dashboards for errors
4. Review logs in terminal
