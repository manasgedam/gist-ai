import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export async function GET() {
  try {
    // Point to the gist-ai output directory
    const outputDir = path.join(process.cwd(), '..', 'gist-ai', 'output')
    
    // Check if output directory exists
    if (!fs.existsSync(outputDir)) {
      return NextResponse.json(
        { error: 'Output directory not found. Run the pipeline first.' },
        { status: 404 }
      )
    }
    
    // Get all ideas files
    const files = fs.readdirSync(outputDir)
    const ideasFiles = files.filter(f => f.includes('_ideas_') && f.endsWith('.json'))
    
    if (ideasFiles.length === 0) {
      return NextResponse.json(
        { error: 'No ideas found. Run the Brain component first.' },
        { status: 404 }
      )
    }
    
    // Get most recent ideas file (by modification time)
    const latestIdeasFile = ideasFiles
      .map(f => ({
        name: f,
        time: fs.statSync(path.join(outputDir, f)).mtime.getTime()
      }))
      .sort((a, b) => b.time - a.time)[0].name
    
    // Extract video_id from filename (e.g., "abc123_ideas_groq.json" -> "abc123")
    const videoId = latestIdeasFile.split('_ideas_')[0]
    
    // Load ideas JSON
    const ideasPath = path.join(outputDir, latestIdeasFile)
    const ideasData = JSON.parse(fs.readFileSync(ideasPath, 'utf-8'))
    
    // Load transcript JSON
    const transcriptPath = path.join(outputDir, `${videoId}_transcript.json`)
    if (!fs.existsSync(transcriptPath)) {
      return NextResponse.json(
        { error: 'Transcript not found for this video.' },
        { status: 404 }
      )
    }
    const transcriptData = JSON.parse(fs.readFileSync(transcriptPath, 'utf-8'))
    
    // Check if video file exists
    const videoPath = path.join(outputDir, `${videoId}_video.mp4`)
    if (!fs.existsSync(videoPath)) {
      return NextResponse.json(
        { error: 'Video file not found. Re-run ingestion with updated code.' },
        { status: 404 }
      )
    }
    
    return NextResponse.json({
      ideas: ideasData,
      transcript: transcriptData,
      videoId: videoId
    })
    
  } catch (error) {
    console.error('Error in get-latest-video:', error)
    return NextResponse.json(
      { error: 'Failed to load video data' },
      { status: 500 }
    )
  }
}