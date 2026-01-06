import json
import os
import sys
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Configuration for high-quality short-form content
MIN_DURATION = 25.0  # Attention span floor
MAX_DURATION = 85.0  # Attention span ceiling
CHUNK_SIZE = 40      # Larger context for better narrative flow
STEP_SIZE = 30       # Overlap to ensure no "Hook" is missed

def map_all_ideas(transcript_json_path):
    if not os.path.exists(transcript_json_path):
        raise FileNotFoundError(f"Transcript not found: {transcript_json_path}")
    
    with open(transcript_json_path, 'r') as f:
        data = json.load(f)
    
    segments = data.get('segments', [])
    if not segments:
        return []

    all_extracted_ideas = []
    
    # Iterate through transcript with overlapping windows
    for i in range(0, len(segments), STEP_SIZE):
        chunk = segments[i : i + CHUNK_SIZE]
        if not chunk: break
        
        # Minified JSON to save tokens while keeping context
        chunk_text = json.dumps([{ "s": round(s['start'], 2), "e": round(s['end'], 2), "t": s['text']} for s in chunk])

        prompt = f"""
            You are a Senior Video Editor for a high-growth media company.
            Analyze this transcript: {chunk_text}

            TASK:
            Extract 2-4 high-retention "Narrative Arcs". 
            These are segments that tell a complete story, make a strong point, or deliver a punchline.

            STRICT QUALITY RULES:
            1. DURATION: Each clip MUST be between 25 and 75 seconds.
            2. HOOK: Must start with a strong sentence (a question, a bold claim, or the start of a story).
            3. RESOLUTION: Must end at a logical pause or conclusion of a thought.
            4. FREQUENCY: If the content is generally "plain," you MUST still find the most engaging 45-second continuous blocks. Do NOT return an empty list.

            OUTPUT FORMAT (JSON):
            {{
                "ideas": [
                    {{
                        "title": "Punchy Hook Title",
                        "explanation": "Why this specific 30-60s block captures attention.",
                        "timestamps": [[start_time, end_time]],
                        "salience_score": 1-10
                    }}
                ]
            }}"""

        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.6
            )
            
            chunk_response = json.loads(completion.choices[0].message.content)
            raw_ideas = chunk_response.get("ideas", [])

            # --- DYNAMIC RECOVERY ---
            # If AI fails, we manually grab a contextually relevant block
            if not raw_ideas:
                f_start = chunk[0]['start']
                f_end = chunk[-1]['end']
                # Clip to 60s if the chunk is too massive
                if (f_end - f_start) > MAX_DURATION: f_end = f_start + 60.0
                
                raw_ideas = [{
                    "title": "Valuable Context",
                    "explanation": "System fallback for continuous flow.",
                    "timestamps": [[f_start, f_end]],
                    "salience_score": 5
                }]

            for idea in raw_ideas:
                start, end = idea['timestamps'][0]
                duration = end - start
                
                # Validation Filter
                if duration < 15.0 or duration > 120.0: continue 

                # Deduplication: Check if we already have a clip starting near this time
                if any(abs(start - seen['timestamps'][0][0]) < 10.0 for seen in all_extracted_ideas):
                    continue
                
                all_extracted_ideas.append(idea)
                print(f"   ✅ Identified: {idea['title']} ({round(duration, 1)}s)")

        except Exception as e:
            print(f"   ❌ Error processing window at segment {i}: {e}")
            continue

    return all_extracted_ideas

if __name__ == "__main__":
    # Standard CLI logic for standalone testing
    if len(sys.argv) > 1:
        TARGET = sys.argv[1]
    else:
        transcripts = [f for f in os.listdir("downloads") if f.endswith("_transcript.json")]
        if not transcripts: sys.exit(1)
        transcripts.sort(key=lambda x: os.path.getmtime(os.path.join("downloads", x)), reverse=True)
        TARGET = os.path.join("downloads", transcripts[0])

    print(f"🚀 Analyzing Narrative Value: {TARGET}")
    results = map_all_ideas(TARGET)
    
    with open(TARGET.replace("_transcript.json", "_map.json"), "w") as f:
        json.dump(results, f, indent=4)
    print(f"✨ Found {len(results)} high-quality segments.")