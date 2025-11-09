# Testing & Utility Scripts

This directory contains utility scripts used during testing and development.

## Audio Processing Scripts

### `transcribe_all.sh`
Batch transcribe audio files using Whisper.cpp.

**Usage:**
```bash
./scripts/transcribe_all.sh
```

**Requirements:**
- Whisper.cpp installed and built
- Audio files in `EXAMPLE_RECORDINGS/` directory
- Model file at `whisper.cpp/models/ggml-base.en.bin`

**Output:** Individual `.txt` files in `transcriptions/` directory

---

### `parse_all.sh`
Batch parse transcriptions using NLP endpoint (LM Studio or Cloudflare AI).

**Usage:**
```bash
./scripts/parse_all.sh
```

**Requirements:**
- FastAPI server running (localhost:8000)
- Transcription files in `transcriptions/` directory
- LM Studio running (for local mode) or Cloudflare AI configured

**Output:** JSON files in `nlp_results/` directory

---

## Analysis Scripts

### `accuracy_analysis.sh`
Analyze NLP parsing accuracy across all test cases.

**Usage:**
```bash
./scripts/accuracy_analysis.sh
```

**Requirements:**
- NLP results in `nlp_results/` directory

**Output:**
- Console summary
- `accuracy_analysis_detailed.md` report

---

## Database Scripts

### `add_examples.py`
Add example reminders to the database for testing/demo purposes.

**Usage:**
```bash
uv run python scripts/add_examples.py
```

**What it does:**
- Adds 10 diverse example reminders
- Covers different priorities, categories, dates
- Useful for UI testing and demos

**Output:** Reminders added to `reminders.db`

---

## Notes

- All scripts assume they are run from the project root directory
- Audio processing scripts require Whisper.cpp to be installed
- NLP scripts require the FastAPI server to be running
- See `docs/testing/README.md` for test data organization

---

*Last updated: November 8, 2025*
