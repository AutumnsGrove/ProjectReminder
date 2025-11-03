# Phase 8 Architecture Plan: Voice Input (MVP)

**Created:** November 3, 2025
**Status:** ✅ COMPLETE
**Completion Date:** November 3, 2025
**Implementation Time:** ~5-6 hours (8 subagents)
**Scope:** Voice-to-Text Only (LLM parsing deferred to Phase 8.1)

**📄 Completion Report:** See [`phase8_completion.md`](./phase8_completion.md) for full implementation details

---

## Executive Summary

Phase 8 MVP focuses exclusively on **voice transcription** using Whisper.cpp. Users can speak into their microphone and have the audio transcribed to text, which populates the reminder text field. All other fields (due date, time, priority, location) are manually filled by the user.

**Smart parsing with LLM is intentionally deferred to Phase 8.1** to ensure the core voice-to-text functionality works reliably first.

---

## Technology Stack

### Voice-to-Text
- **Whisper.cpp** - OpenAI's Whisper model in C++
- **Model:** base.en (fastest, English-only, 74MB)
- **Integration:** Python subprocess wrapper
- **Performance:** 3-8 seconds for typical voice note

### Why Whisper.cpp?
- ✅ Runs locally (offline, private)
- ✅ No API costs
- ✅ Industry-leading accuracy
- ✅ Fast C++ implementation
- ✅ Proven, stable, widely used
- ✅ Easy installation (single binary + model)

### Deferred to Phase 8.1
- **LLM Parsing:** Llama 3.2 1B or Phi-3 Mini
- **Smart Extraction:** Dates, times, priorities, locations
- **Natural Language:** "tomorrow at 3pm" → structured data

---

## Architecture Overview

### Simple Data Flow (Phase 8 MVP)

```
User clicks microphone button (🎤)
    ↓
Browser requests microphone permission
    ↓
MediaRecorder starts recording (🔴 recording)
    ↓
User speaks: "Call mom about Thanksgiving"
    ↓
User clicks stop or auto-stop after 30s
    ↓
Audio blob (WebM/Opus) created
    ↓
Frontend uploads to POST /api/voice/transcribe
    ↓
Backend saves temp file
    ↓
Whisper.cpp subprocess transcribes
    ↓
Text returned: "Call mom about Thanksgiving"
    ↓
Frontend populates reminder text field
    ↓
User manually sets: due_date, priority, etc.
    ↓
User clicks Save (normal form submission)
```

### Future Flow (Phase 8.1 with LLM)

```
[Same as above until text is returned]
    ↓
Frontend sends text to POST /api/voice/parse
    ↓
LLM (Llama 3.2 1B) parses natural language
    ↓
Structured data returned:
    {
      "text": "Call mom about Thanksgiving",
      "due_date": "2025-11-28",  // (parsed "Thanksgiving")
      "priority": "important",    // (inferred from context)
      "category": "Calls"         // (extracted from "call")
    }
    ↓
Frontend auto-fills ALL form fields
    ↓
User reviews and saves
```

---

## Component Breakdown (8 Subagents)

Each subagent produces **one atomic commit** with focused changes.

### Subagent 1: Install Whisper.cpp
**Scope:** System setup, model download, CLI testing
**Deliverable:** Working Whisper.cpp installation
**Commit:** `chore: install and configure Whisper.cpp for voice transcription`

**Tasks:**
1. Clone whisper.cpp repo or download pre-built binary
2. Build if needed (make, gcc/clang required)
3. Download base.en model (~74MB)
4. Test CLI: `./main -m models/ggml-base.en.bin -f sample.wav`
5. Document installation steps in `docs/whisper_setup.md`
6. Add `.gitignore` entries for models and temp audio files

**Files Created:**
- `docs/whisper_setup.md` - Installation guide
- `.gitignore` updates - Ignore whisper models and temp files

**Success Criteria:**
- Whisper.cpp CLI successfully transcribes sample audio
- Model downloaded and working
- Installation documented for reproducibility

---

### Subagent 2: Python Wrapper for Whisper.cpp
**Scope:** Create Python interface to Whisper subprocess
**Deliverable:** `server/voice/whisper.py` module
**Commit:** `feat: add Python wrapper for Whisper.cpp transcription`

**Tasks:**
1. Create `server/voice/` directory
2. Create `server/voice/__init__.py`
3. Create `server/voice/whisper.py` with:
   - `transcribe_audio(audio_path: str) -> str` function
   - Subprocess call to whisper.cpp binary
   - Parse stdout for transcription text
   - Error handling (binary not found, transcription failed)
   - Logging for debugging

**Files Created:**
- `server/voice/__init__.py`
- `server/voice/whisper.py`

**API:**
```python
from server.voice.whisper import transcribe_audio

text = transcribe_audio("/tmp/audio.wav")
# Returns: "Call mom about Thanksgiving"
```

**Success Criteria:**
- Python function successfully calls Whisper.cpp
- Transcription text correctly extracted from output
- Errors handled gracefully (file not found, binary missing)

---

### Subagent 3: Voice Transcription API Endpoint
**Scope:** Add `POST /api/voice/transcribe` endpoint
**Deliverable:** FastAPI endpoint with file upload
**Commit:** `feat: add voice transcription endpoint (POST /api/voice/transcribe)`

**Tasks:**
1. Add Pydantic models to `server/models.py`:
   - `VoiceTranscriptionResponse` - Returns transcribed text
2. Add endpoint to `server/main.py`:
   - `POST /api/voice/transcribe`
   - Accept multipart file upload (audio file)
   - Save to temp file
   - Call `transcribe_audio()`
   - Return transcription text
   - Clean up temp file
3. Add bearer token authentication
4. Add error responses (400, 500)

**Files Modified:**
- `server/models.py` - Add voice models
- `server/main.py` - Add transcription endpoint

**API Spec:**
```python
POST /api/voice/transcribe
Authorization: Bearer <token>
Content-Type: multipart/form-data

Body:
  audio: <audio file (WebM/Opus/WAV)>

Response (200 OK):
{
  "text": "Call mom about Thanksgiving",
  "duration_seconds": 3.2,
  "model": "base.en"
}

Response (400 Bad Request):
{
  "detail": "No audio file provided"
}

Response (500 Internal Server Error):
{
  "detail": "Transcription failed: Whisper binary not found"
}
```

**Success Criteria:**
- Endpoint accepts audio file uploads
- Whisper.cpp transcribes successfully
- JSON response with transcribed text
- Errors handled gracefully

---

### Subagent 4: Browser Audio Recording
**Scope:** Create JavaScript module for audio recording
**Deliverable:** `public/js/voice-recorder.js`
**Commit:** `feat: implement browser audio recording with MediaRecorder API`

**Tasks:**
1. Create `public/js/voice-recorder.js` with:
   - `VoiceRecorder` class
   - Request microphone permission
   - Start/stop recording
   - Handle MediaRecorder events
   - Convert to blob (WebM/Opus preferred)
   - Auto-stop after 30 seconds
2. Add event callbacks:
   - `onPermissionDenied()`
   - `onRecordingStart()`
   - `onRecordingStop(audioBlob)`
   - `onError(error)`

**Files Created:**
- `public/js/voice-recorder.js`

**API:**
```javascript
const recorder = new VoiceRecorder();

await recorder.requestPermission(); // Ask for mic access
recorder.start(); // Start recording
// ... user speaks ...
const audioBlob = await recorder.stop(); // Stop and get audio
```

**Success Criteria:**
- Browser requests microphone permission
- Audio recording starts/stops correctly
- Audio blob created in supported format
- Works in Chrome, Firefox, Safari
- Errors handled (permission denied, no mic)

---

### Subagent 5: Voice Input Button UI
**Scope:** Add microphone button to edit form
**Deliverable:** Voice button with 3 states
**Commit:** `feat: add voice input button UI to reminder form`

**Tasks:**
1. Add button to `public/edit.html`:
   - Position near text field
   - 3 states: idle (🎤), recording (🔴), processing (⏳)
2. Add CSS to `public/css/edit.css`:
   - Button styling (circular, prominent)
   - State animations (pulse during recording)
   - Mobile-friendly size (min 44x44px)
3. Add recording indicator:
   - Visual feedback (red dot pulsing)
   - Timer display (00:05 / 00:30)

**Files Modified:**
- `public/edit.html` - Add voice button
- `public/css/edit.css` - Style voice UI

**UI States:**
```
🎤 Idle     → Gray button, "Click to record"
🔴 Recording → Red button pulsing, timer visible
⏳ Processing → Gray button, spinner icon
```

**Success Criteria:**
- Button visible and accessible
- States transition correctly
- Visual feedback clear
- Mobile-friendly touch target

---

### Subagent 6: Frontend-Backend Integration
**Scope:** Connect recording → upload → transcription → form
**Deliverable:** End-to-end voice input flow
**Commit:** `feat: integrate voice input with backend transcription`

**Tasks:**
1. Add transcription API call to `public/js/api.js`:
   - `API.transcribeAudio(audioBlob)` function
   - Upload audio as multipart form data
   - Handle response (text or error)
2. Integrate in `public/js/app.js`:
   - Wire voice button click handlers
   - Start recording on button click
   - Stop recording on second click or timeout
   - Upload audio to backend
   - Display transcription in text field
   - Handle loading states
3. Add user feedback:
   - "Recording..." message
   - "Transcribing..." message
   - Success: Text appears in field
   - Error: Toast notification

**Files Modified:**
- `public/js/api.js` - Add transcription API
- `public/js/app.js` - Wire voice button
- `public/edit.html` - Include voice-recorder.js script

**Success Criteria:**
- User clicks button → recording starts
- User speaks → audio captured
- Recording stops → upload starts
- Transcription returned → text field populated
- User can edit transcription before saving

---

### Subagent 7: Error Handling & Edge Cases
**Scope:** Graceful error handling for voice input
**Deliverable:** Robust error handling
**Commit:** `fix: add comprehensive error handling for voice input`

**Tasks:**
1. Handle microphone permission denied:
   - Show helpful message
   - Provide instructions to enable
   - Fallback to manual text entry
2. Handle unsupported browser:
   - Detect MediaRecorder API support
   - Hide voice button if unsupported
   - Show warning message
3. Handle transcription failures:
   - Network errors (timeout, connection lost)
   - Server errors (Whisper crash, 500)
   - Empty transcription (silence detected)
   - Retry logic (up to 3 attempts)
4. Handle edge cases:
   - No audio devices available
   - Audio too short (<1 second)
   - Audio too long (>60 seconds, truncate)
   - Concurrent recordings prevented
5. Add user-friendly error messages:
   - "Microphone permission denied. Please allow access in browser settings."
   - "No microphone detected. Please connect a microphone."
   - "Transcription failed. Please try again."
   - "Recording too short. Please speak longer."

**Files Modified:**
- `public/js/voice-recorder.js` - Add error handling
- `public/js/app.js` - Display error messages
- `server/main.py` - Add error responses

**Success Criteria:**
- All error scenarios handled gracefully
- User always knows what went wrong
- System never crashes on errors
- Retry logic works correctly

---

### Subagent 8: Testing & Documentation
**Scope:** Manual testing and documentation
**Deliverable:** Test results and user guide
**Commit:** `docs: add Phase 8 testing results and user guide`

**Tasks:**
1. Manual testing:
   - Test in Chrome, Firefox, Safari
   - Test permission flows (allow/deny)
   - Test various speech lengths (short/long)
   - Test error scenarios (no mic, network failure)
   - Test transcription accuracy (various accents)
2. Document testing results in `docs/phase8_testing.md`
3. Create user guide in `docs/voice_input_guide.md`:
   - How to use voice input
   - Troubleshooting tips
   - Browser compatibility
4. Update `TODOS.md` with Phase 8 completion

**Files Created:**
- `docs/phase8_testing.md` - Test results
- `docs/voice_input_guide.md` - User guide

**Files Modified:**
- `TODOS.md` - Mark Phase 8 complete

**Success Criteria:**
- All critical paths tested
- Known issues documented
- User guide clear and helpful
- Ready for human testing

---

## API Design

### POST /api/voice/transcribe

**Endpoint:** `POST /api/voice/transcribe`
**Authentication:** Required (Bearer token)
**Content-Type:** `multipart/form-data`

**Request:**
```
POST /api/voice/transcribe HTTP/1.1
Host: localhost:8000
Authorization: Bearer YOUR_TOKEN
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="audio"; filename="recording.webm"
Content-Type: audio/webm

[binary audio data]
------WebKitFormBoundary--
```

**Response (Success):**
```json
{
  "text": "Call mom about Thanksgiving",
  "duration_seconds": 3.2,
  "model": "base.en",
  "language": "en"
}
```

**Response (Error - No File):**
```json
{
  "detail": "No audio file provided"
}
```

**Response (Error - Transcription Failed):**
```json
{
  "detail": "Transcription failed: Whisper binary not found at /usr/local/bin/whisper"
}
```

**Response (Error - Invalid Format):**
```json
{
  "detail": "Unsupported audio format. Please provide WebM, Opus, WAV, or MP3."
}
```

---

## File Structure

### New Files
```
server/voice/
├── __init__.py              # Package init
└── whisper.py               # Whisper.cpp wrapper

public/js/
└── voice-recorder.js        # Audio recording module

docs/
├── whisper_setup.md         # Installation guide
├── phase8_testing.md        # Test results
└── voice_input_guide.md     # User guide
```

### Modified Files
```
server/
├── main.py                  # Add /api/voice/transcribe endpoint
└── models.py                # Add VoiceTranscriptionResponse

public/
├── edit.html                # Add voice button
├── css/edit.css             # Style voice UI
└── js/
    ├── api.js               # Add API.transcribeAudio()
    └── app.js               # Wire voice button events

.gitignore                   # Ignore whisper models, temp audio
TODOS.md                     # Mark Phase 8 complete
```

---

## Whisper.cpp Integration Details

### Installation Steps
```bash
# Clone repository
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp

# Build (requires gcc or clang)
make

# Download base.en model (~74MB)
bash ./models/download-ggml-model.sh base.en

# Test
./main -m models/ggml-base.en.bin -f samples/jfk.wav
```

### Python Wrapper Pattern
```python
import subprocess
import os
from pathlib import Path

WHISPER_BIN = "/usr/local/bin/whisper"  # Or path to ./main binary
MODEL_PATH = "/usr/local/share/whisper/models/ggml-base.en.bin"

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio file using Whisper.cpp.

    Args:
        audio_path: Path to audio file (WAV, MP3, WebM, etc.)

    Returns:
        Transcribed text

    Raises:
        FileNotFoundError: Whisper binary not found
        RuntimeError: Transcription failed
    """
    if not os.path.exists(WHISPER_BIN):
        raise FileNotFoundError(f"Whisper binary not found at {WHISPER_BIN}")

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Run whisper.cpp
    result = subprocess.run(
        [WHISPER_BIN, "-m", MODEL_PATH, "-f", audio_path, "-otxt"],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode != 0:
        raise RuntimeError(f"Whisper failed: {result.stderr}")

    # Parse output (Whisper writes to stdout)
    text = result.stdout.strip()

    # Clean up (remove transcription artifacts)
    text = text.replace("[BLANK_AUDIO]", "").strip()

    return text
```

### Audio Format Handling
- **Preferred:** WebM/Opus (browser native)
- **Fallback:** WAV (universal)
- **Conversion:** Use ffmpeg if needed (not required for MVP)

---

## Frontend Implementation Details

### Voice Recording Flow

**1. Request Permission**
```javascript
async requestPermission() {
    try {
        this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        return true;
    } catch (err) {
        if (err.name === 'NotAllowedError') {
            this.onPermissionDenied();
        } else if (err.name === 'NotFoundError') {
            this.onNoMicrophone();
        }
        return false;
    }
}
```

**2. Start Recording**
```javascript
start() {
    this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: 'audio/webm;codecs=opus'
    });

    this.chunks = [];
    this.mediaRecorder.ondataavailable = (e) => {
        this.chunks.push(e.data);
    };

    this.mediaRecorder.onstop = () => {
        const blob = new Blob(this.chunks, { type: 'audio/webm' });
        this.onRecordingStop(blob);
    };

    this.mediaRecorder.start();
    this.onRecordingStart();

    // Auto-stop after 30 seconds
    this.autoStopTimer = setTimeout(() => this.stop(), 30000);
}
```

**3. Stop Recording**
```javascript
stop() {
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
        this.mediaRecorder.stop();
        clearTimeout(this.autoStopTimer);
    }
}
```

**4. Upload Audio**
```javascript
async transcribeAudio(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');

    const response = await fetch(`${this.baseURL}/api/voice/transcribe`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${this.token}`
        },
        body: formData
    });

    if (!response.ok) {
        throw new Error(`Transcription failed: ${response.statusText}`);
    }

    return await response.json();
}
```

---

## Error Handling Strategy

### Permission Errors
```
Error: NotAllowedError (permission denied)
→ Show: "Microphone permission denied. Please allow access in browser settings."
→ Action: Hide voice button, show manual input
```

### Device Errors
```
Error: NotFoundError (no microphone)
→ Show: "No microphone detected. Please connect a microphone and try again."
→ Action: Disable voice button
```

### Network Errors
```
Error: Failed to fetch (network error)
→ Show: "Network error. Please check your connection and try again."
→ Action: Retry button (up to 3 times)
```

### Transcription Errors
```
Error: Whisper binary not found
→ Show: "Voice input is not configured. Please contact support."
→ Action: Log error, disable voice feature

Error: Empty transcription (silence)
→ Show: "No speech detected. Please speak louder and try again."
→ Action: Retry recording
```

---

## Success Criteria

### Phase 8 MVP Complete When:
- ✅ User can click microphone button
- ✅ Browser requests microphone permission
- ✅ Audio recording starts (visual feedback)
- ✅ User speaks into microphone
- ✅ Recording stops (manual or auto after 30s)
- ✅ Audio uploads to backend
- ✅ Whisper.cpp transcribes audio (locally)
- ✅ Transcribed text appears in reminder field
- ✅ User can edit text before saving
- ✅ All errors handled gracefully
- ✅ Works in Chrome, Firefox, Safari
- ✅ Works offline after installation
- ✅ End-to-end latency <8 seconds
- ✅ Transcription accuracy >85% for clear speech

### Test Scenarios
1. **Happy Path:** Record → Transcribe → Populate → Save
2. **Permission Denied:** Show error, fallback to manual
3. **No Microphone:** Disable voice button
4. **Network Failure:** Retry logic works
5. **Silent Audio:** Detect and prompt to speak
6. **Very Short Audio:** Handle <1 second recordings
7. **Very Long Audio:** Auto-stop at 30 seconds
8. **Multiple Languages:** Test with different accents
9. **Background Noise:** Transcription quality check
10. **Concurrent Recordings:** Prevent double recording

---

## Phase 8.1 Preview (LLM Parsing)

**What Phase 8.1 Adds:**
- Second endpoint: `POST /api/voice/parse`
- Llama 3.2 1B integration for NLP
- Auto-extraction of:
  - `due_date`: "tomorrow", "next Friday", "November 15"
  - `due_time`: "at 3pm", "5:30", "noon"
  - `priority`: "urgent", "important", inferred
  - `location`: "at Kroger", "Home Depot", "work"
  - `category`: "call", "buy", "work", etc.
- Smart task understanding

**Example:**
```
Voice: "Important: Call mom tomorrow at 3pm about Thanksgiving"

Phase 8 Output:
{
  "text": "Important: Call mom tomorrow at 3pm about Thanksgiving"
}

Phase 8.1 Output:
{
  "text": "Call mom about Thanksgiving",
  "due_date": "2025-11-04",
  "due_time": "15:00:00",
  "priority": "important",
  "category": "Calls"
}
```

**When to Implement:**
- After Phase 8 MVP is validated
- When Llama 3.2 1B is successfully installed
- When parsing accuracy targets are defined
- Estimated: 8-10 additional hours

---

## Estimated Timeline

### Total: 12-15 hours

**Subagent 1-2 (Setup):** 3-4 hours
- Whisper.cpp installation
- Python wrapper

**Subagent 3 (Backend):** 2 hours
- API endpoint

**Subagent 4-5 (Frontend):** 4-5 hours
- Audio recording
- Voice button UI

**Subagent 6 (Integration):** 2-3 hours
- Connect all pieces

**Subagent 7-8 (Polish):** 2-3 hours
- Error handling
- Testing & docs

---

## Code Statistics

**New Files:** 6
- `server/voice/__init__.py` (~5 lines)
- `server/voice/whisper.py` (~80 lines)
- `public/js/voice-recorder.js` (~200 lines)
- `docs/whisper_setup.md` (~50 lines)
- `docs/phase8_testing.md` (~100 lines)
- `docs/voice_input_guide.md` (~80 lines)

**Modified Files:** 6
- `server/main.py` (+60 lines)
- `server/models.py` (+30 lines)
- `public/edit.html` (+40 lines)
- `public/css/edit.css` (+80 lines)
- `public/js/api.js` (+40 lines)
- `public/js/app.js` (+70 lines)

**Total:** ~740 lines new/modified

---

## Next Agent Instructions

**To start Phase 8 implementation:**

1. Read this architecture document fully
2. Execute subagents 1-8 in order
3. Each subagent = one focused task = one commit
4. Test after each subagent (smoke test)
5. Update todos as you progress
6. Document any deviations from plan

**Quick Start:**
```bash
# Pull latest
git pull origin main

# Create feature branch (optional)
git checkout -b phase8-voice-input

# Start with Subagent 1
# Follow installation steps in whisper.cpp docs
# Document setup process
# Commit when complete

# Then proceed to Subagent 2, 3, etc.
```

**Remember:**
- ✅ One subagent at a time
- ✅ Atomic commits (no batching)
- ✅ Test after each change
- ✅ Document as you go
- ✅ Ask questions if stuck

---

*Architecture Plan Created: November 3, 2025*
*Ready for Implementation*
*Estimated Completion: Phase 8 MVP complete in 12-15 hours*
