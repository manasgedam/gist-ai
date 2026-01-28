# Storage Architecture Setup Guide

## Prerequisites

- Supabase account (free tier)
- Cloudflare account (free tier)
- Python 3.9+
- Node.js 18+

---

## Step 1: Setup Supabase

### 1.1 Create Project

1. Go to [supabase.com](https://supabase.com)
2. Click "New Project"
3. Choose organization
4. Set project name: `gist-ai`
5. Set database password (save this!)
6. Choose region (closest to you)
7. Click "Create new project"

### 1.2 Run Migration

1. Go to SQL Editor in Supabase dashboard
2. Click "New Query"
3. Copy contents of `migrations/001_initial_schema.sql`
4. Paste and click "Run"
5. Verify tables created in Table Editor

### 1.3 Get Credentials

1. Go to Project Settings → API
2. Copy:
   - Project URL: `https://xxxxx.supabase.co`
   - `anon` public key
   - `service_role` secret key (for backend)

---

## Step 2: Setup Cloudflare R2

### 2.1 Create R2 Bucket

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Click "R2" in sidebar
3. Click "Create bucket"
4. Name: `gist-ai-storage`
5. Location: Automatic
6. Click "Create bucket"

### 2.2 Enable Public Access

1. Click on `gist-ai-storage` bucket
2. Go to "Settings" tab
3. Scroll to "Public access"
4. Click "Allow Access"
5. Set custom domain (optional): `gist-ai.r2.dev`

### 2.3 Create API Token

1. Go to R2 → Manage R2 API Tokens
2. Click "Create API token"
3. Name: `gist-ai-backend`
4. Permissions: Object Read & Write
5. Click "Create API token"
6. Copy:
   - Access Key ID
   - Secret Access Key
   - Endpoint URL

---

## Step 3: Configure Backend

### 3.1 Install Dependencies

```bash
cd gist-ai-backend
pip install supabase boto3
```

### 3.2 Update .env

```bash
# Add to .env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_service_role_key_here

R2_ENDPOINT=https://xxxxx.r2.cloudflarestorage.com
R2_ACCESS_KEY=your_access_key_here
R2_SECRET_KEY=your_secret_key_here
R2_BUCKET=gist-ai-storage
R2_PUBLIC_URL=https://gist-ai.r2.dev
```

### 3.3 Test Connection

```bash
python -c "from api.storage import r2_storage; print('R2 connected!')"
```

---

## Step 4: Configure Frontend

### 4.1 Install Dependencies

```bash
cd gist-ai-editor
npm install @supabase/supabase-js
```

### 4.2 Update .env.local

```bash
# Add to .env.local
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
```

---

## Step 5: Test End-to-End

### 5.1 Backend Test

```python
# test_storage.py
from api.storage import r2_storage
from api.database import supabase

# Test R2 upload
url = r2_storage.upload_file('test.txt', 'test/hello.txt')
print(f"Uploaded to: {url}")

# Test Supabase insert
result = supabase.table('videos').insert({
    'source_url': 'https://youtube.com/watch?v=test',
    'source_type': 'youtube',
    'status': 'PENDING'
}).execute()
print(f"Created video: {result.data}")
```

### 5.2 Frontend Test

```typescript
// test-supabase.ts
import { supabase } from "@/lib/supabase";

const { data, error } = await supabase.from("videos").select("*").limit(10);

console.log("Videos:", data);
```

---

## Step 6: Migrate Existing Data (Optional)

If you have existing videos in the file system:

```python
# migrate_data.py
import os
from pathlib import Path
from api.storage import r2_storage
from api.database import supabase

output_dir = Path('output')

for video_dir in output_dir.glob('*_video.mp4'):
    video_id = video_dir.stem.replace('_video', '')

    # Upload video
    video_url = r2_storage.upload_video(
        video_id,
        str(video_dir),
        'original'
    )

    # Upload audio
    audio_path = output_dir / f"{video_id}_audio.mp3"
    if audio_path.exists():
        audio_url = r2_storage.upload_video(
            video_id,
            str(audio_path),
            'audio'
        )

    # Upload transcript
    transcript_path = output_dir / f"{video_id}_transcript.json"
    if transcript_path.exists():
        transcript_url = r2_storage.upload_video(
            video_id,
            str(transcript_path),
            'transcript'
        )

    print(f"Migrated {video_id}")
```

---

## Troubleshooting

### Supabase Connection Failed

- Check URL and key are correct
- Verify project is not paused (free tier pauses after 7 days inactivity)
- Check firewall/network settings

### R2 Upload Failed

- Verify API token has write permissions
- Check endpoint URL format
- Ensure bucket name is correct

### CORS Issues

If accessing R2 from browser:

1. Go to R2 bucket settings
2. Add CORS policy:

```json
[
  {
    "AllowedOrigins": ["http://localhost:3000", "https://yourdomain.com"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3000
  }
]
```

---

## Cost Monitoring

### Supabase Free Tier Limits

- 500 MB database ← Monitor in dashboard
- 1 GB file storage
- 50,000 monthly active users

### R2 Free Tier Limits

- 10 GB storage ← Monitor in Cloudflare dashboard
- 1M Class A operations/month
- 10M Class B operations/month

**Set up alerts:**

- Supabase: Project Settings → Usage
- Cloudflare: R2 → Usage

---

## Next Steps

1. ✅ Setup Supabase and R2
2. ✅ Configure environment variables
3. ✅ Test connections
4. → Update backend to use Supabase + R2
5. → Update frontend to read from Supabase
6. → Deploy and test
