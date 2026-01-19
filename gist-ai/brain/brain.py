"""
Brain - Editorial intelligence layer (TWO-STAGE PROCESS)
Stage 1: Identify complete ideas
Stage 2: Find all segments for each idea

Supports: local LLM, OpenAI API, Groq API
"""

import json
import ollama
from openai import OpenAI
from groq import Groq
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Brain:
    def __init__(self, mode="local", model=None):
        """
        mode: "local", "openai", or "groq"
        model: 
            - For local: "llama3" (default)
            - For openai: "gpt-4o-mini" (default) or "gpt-4o"
            - For groq: "llama-3.3-70b-versatile" (default, free)
        """
        self.mode = mode
        
        if mode == "local":
            self.model = model or "llama3"
            print(f"Brain initialized [LOCAL MODE] with model: {self.model}")
        
        elif mode == "openai":
            self.model = model or "gpt-4o-mini"
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment. Add to .env file.")
            self.client = OpenAI(api_key=api_key)
            print(f"Brain initialized [OPENAI MODE] with model: {self.model}")
        
        elif mode == "groq":
            self.model = model or "llama-3.3-70b-versatile"
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment. Add to .env file.")
            self.client = Groq(api_key=api_key)
            print(f"Brain initialized [GROQ MODE] with model: {self.model}")
        
        else:
            raise ValueError(f"Invalid mode: {mode}. Use 'local', 'openai', or 'groq'")
    
    def load_transcript(self, transcript_path):
        """Load transcript JSON from ingestion output"""
        with open(transcript_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Loaded transcript: {transcript_path}")
        print(f"Duration: {data['duration']:.1f}s")
        print(f"Segments: {len(data['segments'])}")
        
        return data
    
    def format_transcript_for_llm(self, transcript_data):
        """
        Convert transcript JSON to readable text with timestamps
        Format: [00:00] Text here
        """
        formatted_lines = []
        
        for segment in transcript_data['segments']:
            timestamp = self._format_timestamp(segment['start'])
            text = segment['text']
            formatted_lines.append(f"[{timestamp}] {text}")
        
        return "\n".join(formatted_lines)
    
    def _format_timestamp(self, seconds):
        """Convert seconds to MM:SS format"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def build_stage1_prompt(self, formatted_transcript):
        """
        STAGE 1: Identify what complete ideas exist
        Does NOT find timestamps yet
        UPDATED: Stricter criteria for self-contained moments
        """
        prompt = f"""You are a video editor reviewing a full transcript.

Your task: Identify self-contained moments that could work as standalone short-form videos (30-90 seconds total).

CRITICAL: You are looking for SPECIFIC moments, NOT broad topics.

TRANSCRIPT:
{formatted_transcript}

RULES:
1. Each idea must answer ONE specific question or tell ONE specific story
2. Target duration: 30-90 seconds (will be enforced later)
3. Must have: clear hook → development → resolution
4. Must be COMPLETE - viewer doesn't need to watch full video to understand
5. An idea can span scattered moments, but should not be the entire video topic

GOOD IDEAS (specific, self-contained):
✓ "Why burnout happens even when you love your work"
✓ "The surprising origin of the word 'burnout' in the 1950s"
✓ "What ancient philosophers knew about rest that we forgot"
✓ "The hidden cost of 'bullshit jobs' according to David Graber"

BAD IDEAS (too broad, just topics):
✗ "The History of Burnout" (this is the whole video)
✗ "Understanding Burnout" (too vague)
✗ "What is Burnout?" (topic, not a moment)
✗ "All About Productivity" (entire subject)

TEST: Can you describe this idea in one sentence that would make someone click?
If no → it's too broad.

Do NOT find timestamps yet. Just identify what specific moments exist.

OUTPUT FORMAT (JSON):
{{
  "ideas": [
    {{
      "title": "Specific, clickable title that describes ONE moment",
      "description": "What question does this answer or what story does this tell? How does it have hook, development, and resolution?"
    }}
  ]
}}

Be selective. Quality over quantity.
Aim for 3-8 specific ideas, not 20 vague topics.

Output ONLY valid JSON, no extra text."""

        return prompt
    
    def build_stage2_prompt(self, formatted_transcript, idea_title, idea_description):
        """
        STAGE 2: Find ALL segments that contribute to one specific idea
        UPDATED: Stricter segmentation rules
        """
        prompt = f"""You are a video editor finding ALL moments that contribute to a specific idea.

IDEA TO FIND:
Title: {idea_title}
Description: {idea_description}

TRANSCRIPT:
{formatted_transcript}

Your task: Find ALL segments needed to tell this ONE specific story.

CRITICAL SEGMENTATION RULES:
1. Each segment should be 15-60 seconds long (not 2-5 seconds)
2. Only create a new segment when there's a BREAK in the narrative (not for every sentence)
3. If someone is explaining one continuous point, keep it as ONE segment
4. Segments can be scattered across the video, but should not micro-chop continuous speech
5. Target: 1-5 segments total (not 20+)
6. Total duration across all segments: 30-90 seconds

GOOD SEGMENTATION (continuous speech = one segment):
✓ [02:00-02:45] "Hook and setup of the problem"
✓ [05:30-06:15] "Resolution and answer"
Total: 2 segments, 90 seconds

BAD SEGMENTATION (micro-chopping):
✗ [02:00-02:05] "First sentence"
✗ [02:05-02:10] "Second sentence"
✗ [02:10-02:15] "Third sentence"
Total: 40 segments, unusable

WHEN TO CREATE A NEW SEGMENT:
- Speaker moves to different topic and comes back later
- There's a tangent you want to skip
- The idea is discussed at start and resolved at end

WHEN NOT TO CREATE A NEW SEGMENT:
- Speaker is continuously developing the same point
- It's just the next sentence
- You're still in the same explanation

OUTPUT FORMAT (JSON):
{{
  "segments": [
    {{"start": "MM:SS", "end": "MM:SS", "purpose": "What this segment contributes (hook/development/resolution)"}},
    {{"start": "MM:SS", "end": "MM:SS", "purpose": "What this segment contributes"}}
  ],
  "reasoning": "Explain how these segments connect to form the complete idea. If scattered, explain why these specific moments belong together.",
  "transcript_excerpt": "Key quotes that show the hook and resolution"
}}

Be selective. Find the essential moments only.
If the idea would require more than 90 seconds or 5 segments, it's too broad.

Output ONLY valid JSON, no extra text."""

        return prompt
    
    def query_llm(self, prompt):
        """Send prompt to LLM (local, OpenAI, or Groq)"""
        if self.mode == "local":
            return self._query_local_llm(prompt)
        elif self.mode == "openai":
            return self._query_openai_llm(prompt)
        else:  # groq
            return self._query_groq_llm(prompt)
    
    def _query_local_llm(self, prompt):
        """Query local Ollama model"""
        print("Querying local LLM...")
        
        response = ollama.chat(
            model=self.model,
            messages=[{
                'role': 'user',
                'content': prompt
            }]
        )
        
        return response['message']['content']
    
    def _query_openai_llm(self, prompt):
        """Query OpenAI API"""
        print(f"Querying OpenAI API ({self.model})...")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    def _query_groq_llm(self, prompt):
        """Query Groq API"""
        print(f"Querying Groq API ({self.model})...")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    def parse_llm_response(self, response_text):
        """Extract JSON from LLM response"""
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            raise ValueError("No JSON found in LLM response")
        
        json_str = response_text[start_idx:end_idx]
        
        try:
            data = json.loads(json_str)
            return data
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            print(f"Raw response: {response_text}")
            raise
    
    def convert_timestamp_to_seconds(self, timestamp_str):
        """Convert MM:SS to seconds"""
        parts = timestamp_str.split(':')
        mins = int(parts[0])
        secs = int(parts[1])
        return mins * 60 + secs
    
    def run_stage1(self, formatted_transcript):
        """
        STAGE 1: Identify complete ideas
        Returns: List of idea titles and descriptions
        """
        print("\n=== STAGE 1: Identifying complete ideas ===")
        
        prompt = self.build_stage1_prompt(formatted_transcript)
        response = self.query_llm(prompt)
        ideas_list = self.parse_llm_response(response)
        
        print(f"Found {len(ideas_list.get('ideas', []))} complete ideas")
        
        return ideas_list.get('ideas', [])
    
    def run_stage2(self, formatted_transcript, idea):
        """
        STAGE 2: Find all segments for one specific idea
        Returns: Segments with timestamps
        """
        print(f"\n=== STAGE 2: Finding segments for '{idea['title']}' ===")
        
        prompt = self.build_stage2_prompt(
            formatted_transcript,
            idea['title'],
            idea['description']
        )
        
        response = self.query_llm(prompt)
        segments_data = self.parse_llm_response(response)
        
        print(f"Found {len(segments_data.get('segments', []))} segments")
        
        return segments_data
    
    def enrich_segments(self, segments_data, transcript_data, idea_title):
        """
        Convert MM:SS timestamps to seconds
        Validate segments
        UPDATED: Add validation for duration and segment count
        """
        segments = []
        total_duration = 0
        
        for segment in segments_data.get('segments', []):
            start_seconds = self.convert_timestamp_to_seconds(segment['start'])
            end_seconds = self.convert_timestamp_to_seconds(segment['end'])
            
            # Validate timestamps
            if start_seconds >= transcript_data['duration']:
                print(f"Warning: Invalid start time {segment['start']}")
                continue
            
            if end_seconds > transcript_data['duration']:
                end_seconds = transcript_data['duration']
            
            segment_duration = end_seconds - start_seconds
            
            # Warn about micro-segments (too short)
            if segment_duration < 10:
                print(f"Warning: Very short segment ({segment_duration}s) in '{idea_title}' - may be micro-chopped")
            
            segments.append({
                'start_time_formatted': segment['start'],
                'end_time_formatted': segment['end'],
                'start_seconds': start_seconds,
                'end_seconds': end_seconds,
                'duration_seconds': segment_duration,
                'purpose': segment.get('purpose', '')
            })
            
            total_duration += segment_duration
        
        return segments, total_duration
    
    def process(self, transcript_path):
        """
        Full two-stage Brain pipeline
        Input: transcript JSON path
        Output: ideas JSON with multi-segment support
        """
        # Load transcript
        transcript_data = self.load_transcript(transcript_path)
        formatted_transcript = self.format_transcript_for_llm(transcript_data)
        
        # STAGE 1: Identify complete ideas
        ideas_list = self.run_stage1(formatted_transcript)
        
        if not ideas_list:
            print("No complete ideas found.")
            return {
                'video_id': transcript_data['video_id'],
                'source_url': transcript_data['source_url'],
                'total_duration': transcript_data['duration'],
                'model_used': f"{self.mode}:{self.model}",
                'ideas_count': 0,
                'ideas': []
            }
        
        # STAGE 2: Find segments for each idea
        enriched_ideas = []
        
        for idx, idea in enumerate(ideas_list, 1):
            print(f"\n--- Processing idea {idx}/{len(ideas_list)} ---")
            
            try:
                segments_data = self.run_stage2(formatted_transcript, idea)
                segments, total_duration = self.enrich_segments(segments_data, transcript_data, idea['title'])
                
                if not segments:
                    print(f"Warning: No valid segments for '{idea['title']}'")
                    continue
                
                # VALIDATION: Reject ideas that are too long or have too many segments
                if total_duration > 120:  # 2 minutes max (allowing some buffer beyond 90s)
                    print(f"⚠ REJECTED: '{idea['title']}' is too long ({total_duration}s) - likely a topic, not a moment")
                    continue
                
                if len(segments) > 8:  # Max 8 segments
                    print(f"⚠ REJECTED: '{idea['title']}' has too many segments ({len(segments)}) - likely micro-chopped")
                    continue
                
                if total_duration < 20:  # Min 20 seconds
                    print(f"⚠ REJECTED: '{idea['title']}' is too short ({total_duration}s) - incomplete idea")
                    continue
                
                # Warn if mostly micro-segments
                avg_segment_duration = total_duration / len(segments)
                if avg_segment_duration < 12 and len(segments) > 3:
                    print(f"⚠ WARNING: '{idea['title']}' may be micro-chopped (avg {avg_segment_duration:.1f}s per segment)")
                
                enriched_ideas.append({
                    'title': idea['title'],
                    'description': idea['description'],
                    'segments': segments,
                    'segment_count': len(segments),
                    'total_duration_seconds': total_duration,
                    'reasoning': segments_data.get('reasoning', ''),
                    'transcript_excerpt': segments_data.get('transcript_excerpt', '')
                })
                
            except Exception as e:
                print(f"Error processing idea '{idea['title']}': {e}")
                continue
        
        # Build final output
        output = {
            'video_id': transcript_data['video_id'],
            'source_url': transcript_data['source_url'],
            'total_duration': transcript_data['duration'],
            'model_used': f"{self.mode}:{self.model}",
            'processing_method': 'two-stage',
            'ideas_count': len(enriched_ideas),
            'ideas': enriched_ideas
        }
        
        return output
    
    def save_output(self, data, output_dir="output"):
        """Save Brain output to JSON"""
        mode_suffix = self.mode
        output_path = Path(output_dir) / f"{data['video_id']}_ideas_{mode_suffix}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Brain processing complete")
        print(f"✓ Model: {data['model_used']}")
        print(f"✓ Method: {data['processing_method']}")
        print(f"✓ Found {data['ideas_count']} complete ideas")
        print(f"✓ Output: {output_path}")
        
        return output_path


# Command-line usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python brain.py <transcript_json_path> [mode]")
        print("  mode: 'local' (default), 'openai', or 'groq'")
        print("\nExamples:")
        print("  python brain.py output/VIDEO_ID_transcript.json")
        print("  python brain.py output/VIDEO_ID_transcript.json local")
        print("  python brain.py output/VIDEO_ID_transcript.json openai")
        print("  python brain.py output/VIDEO_ID_transcript.json groq")
        sys.exit(1)
    
    transcript_path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "local"
    
    brain = Brain(mode=mode)
    ideas = brain.process(transcript_path)
    brain.save_output(ideas)