# R2 Public Access Configuration

## Issue

You're getting: "That domain was not found on your account" when trying to set up a custom domain.

## Solution

You don't need a custom domain! R2 provides an auto-generated public URL.

---

## Step 1: Enable Public Access

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Click **R2** in the sidebar
3. Click on your bucket (`gist-ai-storage`)
4. Go to **Settings** tab
5. Scroll to **Public access**
6. Click **Allow Access**
7. Click **Connect Domain** → **R2.dev subdomain**
8. Copy the generated URL (e.g., `https://pub-xxxxxxxxxxxxx.r2.dev`)

---

## Step 2: Update .env

Update your `.env` file with the R2.dev URL:

```bash
# Replace this line:
R2_PUBLIC_URL=https://gist-ai.r2.dev

# With your actual R2.dev URL from step 1:
R2_PUBLIC_URL=https://pub-xxxxxxxxxxxxx.r2.dev
```

**Important**: Use the URL from the Cloudflare dashboard, NOT a custom domain.

---

## Step 3: Restart Backend

```bash
# Stop the backend (Ctrl+C)
# Then restart:
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Custom Domain (Optional - Advanced)

If you want a custom domain like `cdn.yourdomain.com`:

### Requirements:

1. You must own a domain
2. Domain must be managed by Cloudflare DNS
3. Domain must be on your Cloudflare account

### Steps:

1. Add your domain to Cloudflare
2. Update nameservers to Cloudflare
3. Wait for DNS propagation (24-48 hours)
4. Then you can connect custom domain to R2

**For now, just use the R2.dev subdomain - it works perfectly!**

---

## Verification

After updating `.env` and restarting:

1. Submit a YouTube URL
2. Watch console for:
   ```
   📤 Uploading files to R2...
     ✓ Video uploaded: https://pub-xxxxx.r2.dev/videos/abc-123/original.mp4
   ```
3. Copy the URL and paste in browser - should play the video

---

## Troubleshooting

### "Access Denied" when accessing URL

- Go to R2 bucket settings
- Verify "Public access" is enabled
- Check the R2.dev subdomain is connected

### "Invalid endpoint" error

- Verify `R2_ENDPOINT` in `.env` is correct
- Should look like: `https://xxxxxxxxxxxxx.r2.cloudflarestorage.com`
- Get this from R2 API tokens page

### Files not uploading

- Check R2 API token has write permissions
- Verify `R2_ACCESS_KEY` and `R2_SECRET_KEY` are correct
- Check bucket name matches `R2_BUCKET` in `.env`
