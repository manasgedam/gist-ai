# Manas's Meaning-Preserving Compression Engine (Phase 1)

A sophisticated AI-driven video pipeline that identifies high-salience "Knowledge Bombs" across long-form content and reconstructs them into cohesive micro-content.

---

## 🧩 System Architecture

The system is built as a modular pipeline to ensure scalability and high-fidelity "meaning preservation."

[Image of an asynchronous AI video processing pipeline architecture]

### 1. Ingestion Engine (`ingest.py`)
**Technical Focus:** Resource Optimization & Stream Decoupling.
- **How it works:** Uses `yt-dlp` and `FFmpeg` to download YouTube content.
- **Key Feature:** Decouples the High-Res Video stream from the Audio stream. 
- **Interview Note:** Extracted lightweight M4A audio for AI processing to minimize latency and bandwidth costs, keeping the 4K/HD video local for the final stitch.

### 2. Transcription Layer (`ingest.py`)
**Technical Focus:** Millisecond Precision.
- **How it works:** Orchestrates `Groq API` (Whisper-large-v3) in `verbose_json` mode.
- **Key Feature:** Word-level timestamping.
- **Interview Note:** Leveraged Groq's LPU inference for near-instant transcription. Word-level timestamps are used as the "anchor" for surgical video cutting.

### 3. Knowledge Mapper (`brain.py`)
**Technical Focus:** Semantic Clustering & Narrative Logic.
- **How it works:** Implements a "Sliding Window" algorithm using `Llama-3.1-8b-instant`.
- **Key Feature:** **Hook-Context-Resolution** arc enforcement.
- **Interview Note:** The AI is prompted as a "Senior Executive Editor" to find ideas that span across time (non-linear). It rejects fragments shorter than 15 seconds to ensure context preservation.

### 4. Temporal Stitcher (`batch_stitcher.py`)
**Technical Focus:** Media Engineering & Algorithmic Logic.
- **How it works:** Uses **FFmpeg Filter Complexes** to cut and join segments.
- **Key Algorithms:** - **Interval Merging:** Collapses overlapping timestamps into a continuous stream to prevent repetition.
    - **PTS Re-stamping:** Resets Presentation Time Stamps for seamless playback.
- **Interview Note:** Implemented audio cross-fades (`afade`) and contextual padding (0.3s) to remove the "choppy" feel of automated edits.

---

## 🚀 Growth & Learning Milestones

- [x] **API Orchestration:** Sequenced multiple third-party AI services.
- [x] **Data Integrity:** Handled overlapping temporal data through interval merging algorithms.
- [x] **FFmpeg Mastery:** Managed complex video filters programmatically rather than using simple CLI commands.
- [x] **Context Window Management:** Solved LLM memory limitations by chunking long-form transcripts.

---

## 🛠 Tech Stack (Phase 1)

- **Language:** Python 3.12+
- **AI Inference:** Groq LPU (Whisper-large-v3 & Llama-3.1)
- **Media Engine:** FFmpeg
- **CLI Tools:** yt-dlp