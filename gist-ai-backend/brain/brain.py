"""
Brain - Editorial intelligence layer (TWO-STAGE PROCESS)
Stage 1: Identify complete ideas
Stage 2: Find all segments for each idea

Uses provider-based LLM architecture (OpenRouter primary, Groq fallback)
"""

import json
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Brain:
    """
    Brain - Editorial intelligence layer for video content analysis.
    
    Two-stage process:
    - Stage 1: Identify complete ideas from transcript
    - Stage 2: Find all segments for each idea
    
    Public API:
        __init__(provider=None) - Initialize with LLM provider
        process(transcript_path) - Run full two-stage pipeline
        save_output(ideas_data, output_dir="output") - Save results to JSON
        
    Internal methods (used by process):
        stage1_identify_ideas(formatted_transcript) - Stage 1 processing
        stage2_find_segments(formatted_transcript, idea, transcript_data) - Stage 2 processing
        query_llm(prompt, temperature=0.3) - Send prompt to LLM provider
        generate(prompt, temperature=0.3) - Alias for query_llm
    """
    
    def __init__(self, provider=None):
        """
        Initialize Brain with an LLM provider.
        
        Args:
            provider: LLMProvider instance (from providers.py)
                     If None, will auto-select from available providers
        """
        if provider is None:
            # Auto-select provider if not provided
            from .providers import ProviderFactory
            providers = ProviderFactory.create_provider_chain()
            provider = ProviderFactory.select_provider_with_preflight(providers)
        
        self.provider = provider
        print(f"Brain initialized with provider: {self.provider.name()} ({self.provider.get_model_name()})")
        
        # Brain runtime invariants (fixed configuration):
        # - Strict mode only (no permissive/local mode)
        # - Fixed segment duration bounds for quality control
        # - Consistent validation thresholds
        
        # Segment duration constraints (seconds)
        self.min_segment_duration = 15  # Minimum viable segment length
        self.max_segment_duration = 120  # Maximum to keep clips focused
        self.min_total_duration = 25  # Minimum total duration for an idea
        self.max_total_duration = 120  # Maximum total duration for an idea
        
        # Idea validation thresholds
        self.min_ideas = 3  # Minimum ideas to extract
        self.max_ideas = 10  # Maximum ideas to prevent overload
        self.min_segments_per_idea = 1  # Minimum segments per idea
        self.max_segments = 5  # Maximum segments per idea
        self.min_avg_segment = 15  # Minimum average segment duration
        
        # Sanity check: Ensure all required attributes are set
        assert hasattr(self, 'provider'), "Brain must have provider"
        assert hasattr(self, 'min_segment_duration'), "Brain must have min_segment_duration"
        assert hasattr(self, 'max_segment_duration'), "Brain must have max_segment_duration"


    
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
    
    def get_validation_thresholds(self):
        """Get validation thresholds (uses instance attributes set in __init__)"""
        return {
            'min_ideas': self.min_ideas,
            'max_ideas': self.max_ideas,
            'min_segments_per_idea': self.min_segments_per_idea,
            'min_segment_duration': self.min_segment_duration,
            'max_segment_duration': self.max_segment_duration,
            'min_total_duration': self.min_total_duration,
            'max_total_duration': self.max_total_duration,
            'max_segments': self.max_segments,
            'min_avg_segment': self.min_avg_segment
        }
    
    def build_stage1_prompt(self, formatted_transcript):
        """
        STAGE 1: Identify what complete ideas exist
        Routes to strict (Groq) or permissive (Ollama) variant
        """
        return self.build_stage1_prompt_strict(formatted_transcript)
    
    def build_stage1_prompt_strict(self, formatted_transcript):
        """
        STAGE 1 (STRICT): For Groq/OpenRouter - High precision, selective
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
    
    def build_stage1_prompt_permissive(self, formatted_transcript):
        """
        STAGE 1 (PERMISSIVE): For Ollama - Exploratory, more accepting
        """
        prompt = f"""You are a video editor reviewing a full transcript.

Your task: Find all potentially usable moments that could work as short-form videos (20-120 seconds).

Be EXPLORATORY - find moments that could work with some editing or refinement.

TRANSCRIPT:
{formatted_transcript}

RULES:
1. Each idea should answer a question or tell a story
2. Target duration: 20-120 seconds (flexible)
3. Should have some narrative structure (beginning, middle, end)
4. Ideas can be refined later - focus on finding workable moments
5. An idea can span multiple segments if they connect

GOOD IDEAS (workable moments):
✓ "Why burnout happens even when you love your work"
✓ "The origin of the word 'burnout'"
✓ "What philosophers knew about rest"
✓ "The cost of 'bullshit jobs'"
✓ "How to recognize burnout symptoms"
✓ "The difference between stress and burnout"

ACCEPTABLE IDEAS (can be refined):
✓ "Understanding burnout" (if there's a specific angle)
✓ "Productivity tips" (if there are concrete examples)
✓ "Work-life balance" (if there's a specific insight)

Do NOT find timestamps yet. Just identify what moments exist.

OUTPUT FORMAT (JSON):
{{
  "ideas": [
    {{
      "title": "Descriptive title for this moment",
      "description": "What does this moment cover? What makes it interesting?"
    }}
  ]
}}

Be exploratory. Find all potentially usable moments.
Aim for 5-15 ideas - we can refine later.

Output ONLY valid JSON, no extra text."""

        return prompt
    
    def build_stage2_prompt(self, formatted_transcript, idea_title, idea_description):
        """
        STAGE 2: Find ALL segments that contribute to one specific idea
        Always uses strict validation for quality
        """
        return self.build_stage2_prompt_strict(formatted_transcript, idea_title, idea_description)
    
    def build_stage2_prompt_strict(self, formatted_transcript, idea_title, idea_description):
        """
        STAGE 2 (STRICT): For Groq/OpenRouter - Precise segmentation
        """
        prompt = f"""You are a video editor finding ALL moments that contribute to a specific idea.

IDEA TO FIND:
Title: {idea_title}
Description: {idea_description}

TRANSCRIPT:
{formatted_transcript}

Your task: Find ALL segments needed to tell this ONE specific story.

CRITICAL SEGMENTATION RULES:
1. MINIMUM segment duration: 15 seconds (not 2-10 seconds)
2. Only create a new segment when there's a CLEAR BREAK in the narrative
3. If someone is explaining one continuous point, keep it as ONE segment
4. If segments would be adjacent or very close (within 5 seconds), MERGE them into one
5. Target: 1-4 segments total (not 5-10+)
6. Total duration across all segments: 30-90 seconds

OUTPUT FORMAT (JSON):
{{
  "segments": [
    {{"start": "MM:SS", "end": "MM:SS", "purpose": "What this segment contributes (hook/development/resolution)"}}
  ],
  "reasoning": "Explain how these segments connect to form the complete idea.",
  "transcript_excerpt": "Key quotes that show the hook and resolution"
}}

STRICT REQUIREMENTS:
- Each segment MUST be at least 15 seconds
- If the idea needs more than 4 segments or 90 seconds total, it's too broad
- Merge adjacent or near-adjacent segments

CRITICAL JSON RULES:
- Output ONLY valid JSON (no markdown, no explanation)
- Do NOT escape apostrophes: use ' not \'
- Use only standard JSON escapes: \" \\ \/ \b \f \n \r \t
- No trailing commas
- Invalid JSON will be DISCARDED without retry (wastes credits)

IMPORTANT: Output ONLY valid JSON. No explanatory text before or after. Ensure all strings are properly quoted and escaped."""


        return prompt
    
    def build_stage2_prompt_permissive(self, formatted_transcript, idea_title, idea_description):
        """
        STAGE 2 (PERMISSIVE): For Ollama - Flexible segmentation
        """
        prompt = f"""You are a video editor finding moments that contribute to a specific idea.

IDEA TO FIND:
Title: {idea_title}
Description: {idea_description}

TRANSCRIPT:
{formatted_transcript}

Your task: Find segments needed to tell this story. Be flexible - segments can be refined later.

SEGMENTATION RULES:
1. MINIMUM segment duration: 10 seconds (can be trimmed in editing)
2. Create a new segment when there's a break in the narrative
3. If someone is explaining one continuous point, keep it as ONE segment
4. If segments are very close (within 3 seconds), consider merging
5. Target: 1-6 segments total
6. Total duration across all segments: 20-120 seconds

OUTPUT FORMAT (JSON):
{{
  "segments": [
    {{"start": "MM:SS", "end": "MM:SS", "purpose": "What this segment contributes"}}
  ],
  "reasoning": "Explain how these segments connect.",
  "transcript_excerpt": "Key quotes from the segments"
}}

REQUIREMENTS:
- Each segment should be at least 10 seconds
- Total duration: 20-120 seconds is acceptable
- Segments can be refined in post-production

IMPORTANT: Output ONLY valid JSON. No explanatory text before or after. Ensure all strings are properly quoted and escaped."""


        return prompt
    
    def generate(self, prompt, temperature=0.3):
        """
        Generate LLM response using configured provider.
        
        Args:
            prompt: Text prompt to send to LLM
            temperature: Sampling temperature (0.0-1.0)
        
        Returns:
            str: LLM response text
        """
        try:
            return self.provider.query(prompt, temperature=temperature)
        except Exception as e:
            print(f"❌ Provider {self.provider.name()} failed: {e}")
            raise

    def query_llm(self, prompt, temperature=0.3):
        """
        Query LLM (alias for generate, for backward compatibility).
        
        Args:
            prompt: Text prompt to send to LLM
            temperature: Sampling temperature (0.0-1.0)
        
        Returns:
            str: LLM response text
        """
        return self.generate(prompt, temperature)
    
    def sanitize_llm_json(self, text: str) -> str:
        """
        Sanitize common LLM JSON errors before parsing.
        MINIMAL and SAFE - only fix known illegal escapes.
        
        This prevents credit burn from retrying on invalid JSON.
        """
        # Fix illegal apostrophe escape (most common LLM error)
        text = text.replace("\\'", "'")
        return text
    
    def clean_json_string(self, json_str):
        """Clean common JSON formatting issues from LLM output"""
        # Remove markdown code blocks
        json_str = json_str.replace('```json', '').replace('```', '')
        
        # Remove trailing commas before closing braces/brackets
        import re
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        return json_str.strip()

    def parse_llm_response(self, response_text):
        """
        Extract and parse JSON from LLM response.
        Uses extract_and_parse_json which includes sanitization.
        """
        return self.extract_and_parse_json(response_text)
    
    def extract_and_parse_json(self, response_text):
        """
        Extract and parse JSON from LLM response.
        Tries multiple strategies to handle common LLM formatting issues.
        """
        # Find JSON boundaries
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            print(f"\nRaw response: {response_text}")
            raise ValueError("No JSON found in LLM response")
        
        json_str = response_text[start_idx:end_idx]
        
        # Sanitize first (fix illegal escapes)
        json_str = self.sanitize_llm_json(json_str)
        
        # Try multiple parsing strategies
        strategies = [
            ("Direct parsing", lambda s: s),
            ("After cleaning", self.clean_json_string),
        ]
        
        last_error = None
        for strategy_name, strategy_func in strategies:
            try:
                processed_json = strategy_func(json_str)
                data = json.loads(processed_json)
                if strategy_name != "Direct parsing":
                    print(f"✓ Successfully parsed using: {strategy_name}")
                return data
            except json.JSONDecodeError as e:
                last_error = e
                continue
        
        # All strategies failed - show detailed error
        print(f"\n{'='*60}")
        print(f"❌ FAILED TO PARSE JSON (tried all strategies)")
        print(f"{'='*60}")
        print(f"Final error: {last_error}")
        print(f"\nProblematic JSON (first 500 chars):")
        print(json_str[:500])
        print(f"\nFull raw response:")
        print(response_text)
        print(f"{'='*60}\n")
        raise RuntimeError(f"Failed to parse LLM JSON response: {str(last_error)}")
    
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
        UPDATED: Better error handling
        """
        print("\n=== STAGE 1: Identifying complete ideas ===")
        print("  🔒 STRICT MODE: Selective filtering, 3-10 ideas expected")
        print("  → Analyzing video content...")
        
        try:
            prompt = self.build_stage1_prompt(formatted_transcript)
            response = self.query_llm(prompt)
            ideas_list = self.parse_llm_response(response)
            
            num_ideas = len(ideas_list.get('ideas', []))
            
            if num_ideas == 0:
                print("  ⚠ No complete ideas identified")
            else:
                print(f"  ✓ Found {num_ideas} complete ideas")
            
            return ideas_list.get('ideas', [])
            
        except Exception as e:
            raise RuntimeError(f"Stage 1 failed: {str(e)}")
    
    def run_stage2(self, formatted_transcript, idea):
        """
        STAGE 2: Find all segments for one specific idea
        Returns: Segments with timestamps
        UPDATED: No-retry guard for JSON failures
        """
        print(f"  → Finding segments for: '{idea['title']}'")
        
        try:
            prompt = self.build_stage2_prompt(
                formatted_transcript,
                idea['title'],
                idea['description']
            )
            
            response = self.query_llm(prompt)
            
            # Parse with sanitization (no retry on failure)
            try:
                segments_data = self.parse_llm_response(response)
            except (json.JSONDecodeError, ValueError) as e:
                # CRITICAL: Do NOT retry - this wastes credits
                print(f"    ✗ JSON parse failed: {str(e)}")
                print(f"    Raw response (first 300 chars): {response[:300]}...")
                raise RuntimeError(f"Invalid JSON from LLM (no retry)")
            
            # Validate required keys
            if 'segments' not in segments_data or 'reasoning' not in segments_data:
                print(f"    ⚠️  Missing required keys (segments/reasoning)")
                raise RuntimeError(f"Incomplete JSON response")
            
            num_segments = len(segments_data.get('segments', []))
            print(f"    ✓ Found {num_segments} segments")
            
            return segments_data
            
        except RuntimeError:
            # Re-raise RuntimeError (JSON failures)
            raise
        except Exception as e:
            raise RuntimeError(f"Stage 2 failed for '{idea['title']}': {str(e)}")

    
    def enrich_segments(self, segments_data, transcript_data, idea_title):
        """
        Convert MM:SS timestamps to seconds
        Validate segments
        UPDATED: Add padding and stricter validation
        """
        segments = []
        total_duration = 0
        
        PADDING_SECONDS = 1.0  # Add 1s padding at start/end for natural cuts
        
        for segment in segments_data.get('segments', []):
            start_seconds = self.convert_timestamp_to_seconds(segment['start'])
            end_seconds = self.convert_timestamp_to_seconds(segment['end'])
            
            # Add padding (but don't go below 0 or beyond video duration)
            start_with_padding = max(0, start_seconds - PADDING_SECONDS)
            end_with_padding = min(transcript_data['duration'], end_seconds + PADDING_SECONDS)
            
            # Validate timestamps
            if start_with_padding >= transcript_data['duration']:
                print(f"    ⚠ Invalid start time {segment['start']}")
                continue
            
            segment_duration = end_with_padding - start_with_padding
            
            # Mode-aware validation
            thresholds = self.get_validation_thresholds()
            if segment_duration < thresholds['min_segment_duration']:
                print(f"    ⚠ Segment too short ({segment_duration:.1f}s): {segment['start']}-{segment['end']} - REJECTED")
                continue
            
            segments.append({
                'start_time_formatted': segment['start'],
                'end_time_formatted': segment['end'],
                'start_seconds': start_with_padding,  # With padding
                'end_seconds': end_with_padding,      # With padding
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
                'model_used': self.provider.get_model_name(),
                'ideas_count': 0,
                'ideas': []
            }
        
        # STAGE 2: Find segments for each idea
        enriched_ideas = []
        skipped_ideas = 0  # Track JSON parse failures
        
        if ideas_list:
            print(f"\n=== STAGE 2: Finding segments for {len(ideas_list)} ideas ===")
        
        for idx, idea in enumerate(ideas_list, 1):
            print(f"\n[{idx}/{len(ideas_list)}] Processing: '{idea['title']}'")
            
            try:
                segments_data = self.run_stage2(formatted_transcript, idea)
                segments, total_duration = self.enrich_segments(segments_data, transcript_data, idea['title'])
                
                if not segments:
                    print(f"    ⚠ No valid segments found (all rejected for being too short)")
                    continue
                
                # VALIDATION: Reject ideas that are too long or have too many segments
                thresholds = self.get_validation_thresholds()
                if total_duration > thresholds['max_total_duration']:
                    print(f"    ⚠ REJECTED: Too long ({total_duration}s) - likely a topic, not a moment")
                    continue
                
                if len(segments) > thresholds['max_segments']:
                    print(f"    ⚠ REJECTED: Too many segments ({len(segments)}) - likely micro-chopped")
                    continue
                
                if total_duration < thresholds['min_total_duration']:
                    print(f"    ⚠ REJECTED: Too short ({total_duration}s) - incomplete idea")
                    continue
                
                # STRICT: Check average segment duration
                avg_segment_duration = total_duration / len(segments)
                if avg_segment_duration < thresholds['min_avg_segment']:
                    print(f"    ⚠ REJECTED: Micro-chopped (avg {avg_segment_duration:.1f}s per segment, need 15s+)")
                    continue
                
                print(f"    ✓ ACCEPTED: {len(segments)} segments, {total_duration:.1f}s total, avg {avg_segment_duration:.1f}s per segment")
                
                enriched_ideas.append({
                    'title': idea['title'],
                    'description': idea['description'],
                    'segments': segments,
                    'segment_count': len(segments),
                    'total_duration_seconds': total_duration,
                    'reasoning': segments_data.get('reasoning', ''),
                    'transcript_excerpt': segments_data.get('transcript_excerpt', '')
                })
                
            except RuntimeError as e:
                # JSON parse failures - don't retry
                error_msg = str(e)
                if "Invalid JSON" in error_msg or "Incomplete JSON" in error_msg:
                    skipped_ideas += 1
                    print(f"    ⚠️  Skipped due to JSON error (no retry to preserve credits)")
                else:
                    print(f"    ✗ Error: {error_msg}")
                continue
            except Exception as e:
                print(f"    ✗ Error: {str(e)}")
                continue
        
        
        # Show summary of skipped ideas
        if skipped_ideas > 0:
            print(f"\n⚠️  Skipped {skipped_ideas} idea(s) due to JSON parse errors (no retries to preserve credits)")
        
        # Build final output
        output = {
            'video_id': transcript_data['video_id'],
            'source_url': transcript_data['source_url'],
            'total_duration': transcript_data['duration'],
            'model_used': self.provider.get_model_name(),
            'processing_method': 'two-stage',
            'ideas_count': len(enriched_ideas),
            'ideas': enriched_ideas
        }
        
        return output
    
    def save_output(self, data, output_dir="output"):
        """Save Brain output to JSON"""
        provider_name = self.provider.name().lower()
        output_path = Path(output_dir) / f"{data['video_id']}_ideas_{provider_name}.json"
        
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
        print("  mode: 'local' (default) or 'groq'")
        print()
        print("Examples:")
        print("  python brain.py output/VIDEO_ID_transcript.json")
        print("  python brain.py output/VIDEO_ID_transcript.json local")
        print("  python brain.py output/VIDEO_ID_transcript.json groq")
        sys.exit(1)
    
    transcript_path = sys.argv[1]
    brain = Brain()
    ideas = brain.process(transcript_path)
    brain.save_output(ideas)