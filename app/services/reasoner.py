import os
import ollama
import logging
from typing import List, Dict
from pydantic import BaseModel
from faster_whisper import WhisperModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATA MODELS ---
class TopicSummary(BaseModel):
    topic: str
    summary: str
    segments: List[int] # Indices of chunks where this topic appears

class FinalShortClip(BaseModel):
    title: str
    topic: str
    timestamps: List[Dict[str, float]] # List of [{start, end}, {start, end}] for cross-video stitching
    hook_reason: str

# --- THE GIST ENGINE ---
class GistAIEngine:
    def __init__(self):
        # Using base model for speed; use 'large-v3' for accuracy
        self.transcriber = WhisperModel("base", device="cpu", compute_type="int8")
        self.model = "llama3.1:8b"

    def process_video(self, video_path: str):
        # 1. TRANSCRIPTION
        logger.info("Transcribing video...")
        segments, _ = self.transcriber.transcribe(video_path)
        full_transcript = list(segments)

        # 2. MAP: Skim the video in 5-minute chunks (300 seconds)
        logger.info("Skimming video for global context...")
        chunks = self._chunk_transcript(full_transcript, window_size=300)
        chunk_summaries = []
        
        for i, chunk_text in enumerate(chunks):
            summary = self._get_chunk_summary(i, chunk_text)
            chunk_summaries.append(summary)

        # 3. REDUCE: Identify High-Priority Global Topics
        logger.info("Identifying high-priority themes across the whole video...")
        global_map = "\n".join(chunk_summaries)
        priority_topics = self._get_priority_topics(global_map)

        # 4. REFINE: Get precise timestamps for related moments across the video
        logger.info("Extracting related segments for final short video...")
        final_clips = []
        for topic in priority_topics:
            clip_data = self._get_precise_timestamps_for_topic(topic, full_transcript)
            final_clips.append(clip_data)

        return final_clips, full_transcript

    def _chunk_transcript(self, segments, window_size=300):
        chunks = []
        current_chunk = ""
        current_time = 0
        
        for seg in segments:
            current_chunk += f"[{seg.start:.1f}s] {seg.text} "
            if seg.end > current_time + window_size:
                chunks.append(current_chunk)
                current_chunk = ""
                current_time = seg.end
        if current_chunk: chunks.append(current_chunk)
        return chunks

    def _get_chunk_summary(self, index, text):
        prompt = f"Analyze this 5-minute video segment (ID: {index}) and list the key topics discussed. Transcript: {text}"
        response = ollama.generate(model=self.model, prompt=prompt)
        return f"Segment {index} Summary: {response['response']}"

    def _get_priority_topics(self, global_map):
        prompt = f"""
        Based on these segment summaries of a long video, identify the top 2 'Mega-Themes'. 
        Look for topics that appear in multiple segments or have high viral potential.
        Summaries: {global_map}
        Return a simple list of the 2 themes.
        """
        response = ollama.generate(model=self.model, prompt=prompt)
        return response['response'].split('\n')[:2] # Simplified for this example

    def _get_precise_timestamps_for_topic(self, topic, full_segments):
        # This is where the AI finds moments from different parts of the video
        # We pass the full transcript but tell the AI to look specifically for the chosen topic
        text_context = "\n".join([f"{s.start}-{s.end}: {s.text}" for s in full_segments[:100]]) # Sample for brevity
        prompt = f"""
        Target Topic: {topic}
        Find all moments in the transcript where this topic is discussed.
        Provide exact start and end timestamps. 
        If the topic is discussed at the start and the end, include both segments.
        Format: JSON {{ 'timestamps': [ {{'start': 10.5, 'end': 25.0}}, {{'start': 500.2, 'end': 530.0}} ] }}
        Transcript: {text_context}
        """
        response = ollama.chat(model=self.model, messages=[{'role':'user', 'content':prompt}], format='json')
        return response['message']['content']

# --- EXECUTION ---
if __name__ == "__main__":
    engine = GistAIEngine()
    results = engine.process_video("data/video.mp4")
    print("FINAL CLIP DATA FOR EDITOR:", results)