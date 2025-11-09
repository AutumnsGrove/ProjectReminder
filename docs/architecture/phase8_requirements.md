# Phase 8 Requirements: Voice-to-Text MVP

**Created:** November 3, 2025
**Status:** Ready for Implementation
**Scope:** Voice transcription only (LLM parsing deferred to Phase 8.1)

---

## Overview

Phase 8 implements voice-to-text transcription using Whisper.cpp, allowing users to speak reminders instead of typing. This MVP focuses exclusively on transcription - users will manually fill date, time, priority, and location fields after speaking.

**User Flow:**
1. User clicks microphone button (🎤)
2. Browser requests permission → User allows
3. User speaks: "Call mom about Thanksgiving"
4. Recording stops (auto after 30s or manual)
5. Audio uploads to backend
6. Whisper.cpp transcribes locally
7. Text appears in reminder field
8. User manually sets due date, priority, etc.
9. User saves reminder normally

---

## Functional Requirements

### FR-1: Voice Input UI

**FR-1.1 Microphone Button**
- Add microphone button (🎤) to edit form near reminder text field
- Button must have 3 distinct visual states:
  - **Idle**: Gray button, tooltip "Click to record"
  - **Recording**: Red pulsing button, timer visible (00:05 / 00:30)
  - **Processing**: Gray button with spinner, "Transcribing..."
- Button must be touch-friendly (minimum 44x44px touch target)
- Button must be accessible (ARIA labels, keyboard navigation)

**FR-1.2 Recording Indicator**
- Show visual feedback during recording (red pulsing dot)
- Display elapsed time counter (MM:SS format)
- Show maximum duration countdown (30 seconds default)
- Clear indication when recording is active

**FR-1.3 Permission Handling**
- Request microphone permission on first button click
- Show clear permission prompt if browser supports
- Display helpful error if permission denied
- Provide instructions to enable permission in browser settings
- Fallback to manual text entry if permission denied

### FR-2: Audio Recording

**FR-2.1 Browser Recording**
- Use MediaRecorder API for audio capture
- Capture audio in WebM/Opus format (browser native)
- Fallback to WAV if WebM not supported
- Support Chrome, Firefox, Safari (latest versions)

**FR-2.2 Recording Control**
- Start recording on button click
- Stop recording on second button click (manual)
- Auto-stop after 30 seconds (configurable)
- Prevent concurrent recordings (only one at a time)
- Handle microphone disconnection during recording

**FR-2.3 Audio Validation**
- Reject recordings shorter than 1 second
- Truncate recordings longer than 60 seconds
- Detect silence and warn user
- Validate audio blob before upload

### FR-3: Backend Transcription

**FR-3.1 Whisper.cpp Integration**
- Install Whisper.cpp binary locally
- Download base.en model (~74MB, English-only)
- Create Python wrapper module (`server/voice/whisper.py`)
- Implement `transcribe_audio(audio_path: str) -> str` function
- Handle subprocess execution (timeout: 30 seconds)
- Parse Whisper output for transcribed text

**FR-3.2 Transcription Endpoint**
- Implement `POST /api/voice/transcribe` endpoint
- Accept multipart file upload (audio field)
- Require bearer token authentication
- Save uploaded audio to temporary file
- Call Whisper.cpp wrapper
- Return transcribed text in JSON response
- Clean up temporary files after processing
- Handle audio format conversion if needed (WebM → WAV)

**FR-3.3 Response Format**
```json
{
  "text": "Call mom about Thanksgiving",
  "duration_seconds": 3.2,
  "model": "base.en",
  "language": "en"
}
```

### FR-4: Frontend-Backend Integration

**FR-4.1 API Communication**
- Create `API.transcribeAudio(audioBlob)` function in `public/js/api.js`
- Upload audio as multipart form data
- Include bearer token in Authorization header
- Handle network errors with retry logic (3 attempts)
- Parse JSON response and extract text

**FR-4.2 User Feedback**
- Show loading state during upload ("Uploading...")
- Show processing state during transcription ("Transcribing...")
- Display success message when complete
- Populate text field with transcribed text
- Show toast notification on error
- Provide retry button on failure

**FR-4.3 Form Integration**
- Integrate voice recorder with existing edit form
- Populate reminder text field with transcription
- Allow user to edit transcribed text before saving
- Preserve existing form validation
- Maintain existing save/cancel behavior

---

## Non-Functional Requirements

### NFR-1: Performance

**NFR-1.1 Transcription Latency**
- End-to-end latency: <8 seconds for typical voice note (3-5 seconds)
- Recording start: <500ms after button click
- Upload time: <2 seconds for 30-second audio
- Whisper.cpp processing: <5 seconds for typical voice note
- UI responsiveness: No blocking during transcription

**NFR-1.2 Resource Usage**
- Whisper base.en model: ~74MB disk space
- Peak memory usage: <500MB during transcription
- CPU usage: Acceptable on modern laptops (2017+)
- No GPU required (CPU-only Whisper.cpp)

### NFR-2: Offline-First Preservation

**NFR-2.1 Local Processing**
- Whisper.cpp runs locally (no cloud API)
- No internet required after initial setup
- Transcription works when offline
- Privacy preserved (audio never leaves device)

**NFR-2.2 Installation**
- Whisper.cpp binary installed once
- Model downloaded once (~74MB)
- No ongoing downloads or updates required
- Documented installation process for reproducibility

### NFR-3: Reliability

**NFR-3.1 Error Handling**
- Handle microphone permission denied gracefully
- Handle no microphone detected
- Handle Whisper binary not found
- Handle transcription failures (timeout, crash)
- Handle empty transcription (silence detected)
- Handle network errors during upload
- All errors display user-friendly messages
- System never crashes on errors

**NFR-3.2 Fallback Behavior**
- Always allow manual text entry as fallback
- Voice button hidden if browser unsupported
- Transcription failure allows retry
- User can cancel recording and type manually

### NFR-4: Usability

**NFR-4.1 ADHD-Friendly Design**
- Low friction (single button click to start)
- Clear visual feedback (button states, timer)
- No unnecessary steps or confirmations
- Forgiving (can retry, can edit transcription)
- No notification fatigue (quiet processing)

**NFR-4.2 Accessibility**
- Keyboard navigation support
- Screen reader compatible (ARIA labels)
- High contrast button states
- Touch-friendly button sizes (44x44px minimum)
- Clear error messages

### NFR-5: Accuracy

**NFR-5.1 Transcription Quality**
- Target accuracy: >85% for clear speech
- Support for common English accents
- Handle background noise reasonably
- Detect and handle silence
- Clean up Whisper artifacts ([BLANK_AUDIO], etc.)

**NFR-5.2 User Expectations**
- User can review and edit transcription
- User understands this is transcription, not parsing
- User knows to manually fill other fields
- Clear that this is an MVP feature

### NFR-6: Security

**NFR-6.1 Authentication**
- Transcription endpoint requires bearer token
- Same authentication as other API endpoints
- No anonymous transcription allowed

**NFR-6.2 Privacy**
- Audio processed locally (never sent to cloud)
- Temporary audio files deleted after transcription
- No audio storage or logging
- No telemetry or analytics

---

## Success Criteria

Phase 8 MVP is complete when ALL of the following are true:

### Critical Success Criteria (Must Have)

1. ✅ **Voice Button Visible**: Microphone button appears in edit form
2. ✅ **Permission Flow**: Browser requests microphone permission correctly
3. ✅ **Recording Works**: Audio recording starts with visual feedback
4. ✅ **User Can Speak**: User can speak into microphone and see timer
5. ✅ **Recording Stops**: Recording stops manually or auto after 30s
6. ✅ **Upload Succeeds**: Audio uploads to backend successfully
7. ✅ **Whisper Transcribes**: Whisper.cpp transcribes audio locally
8. ✅ **Text Appears**: Transcribed text populates reminder field
9. ✅ **User Can Edit**: User can edit transcription before saving
10. ✅ **Error Handling**: All error scenarios handled gracefully
11. ✅ **Cross-Browser**: Works in Chrome, Firefox, Safari
12. ✅ **Offline Works**: Works offline after Whisper.cpp installed
13. ✅ **Performance**: End-to-end latency <8 seconds
14. ✅ **Accuracy**: Transcription accuracy >85% for clear speech

### Test Scenarios (Must Pass)

1. **Happy Path**: Record → Transcribe → Populate → Save ✅
2. **Permission Denied**: Show error, fallback to manual ✅
3. **No Microphone**: Disable voice button ✅
4. **Network Failure**: Retry logic works ✅
5. **Silent Audio**: Detect and prompt to speak ✅
6. **Very Short Audio**: Handle <1 second recordings ✅
7. **Very Long Audio**: Auto-stop at 30 seconds ✅
8. **Different Accents**: Test with various accents ✅
9. **Background Noise**: Transcription quality check ✅
10. **Concurrent Recordings**: Prevent double recording ✅

### Deliverables (Must Exist)

1. ✅ Whisper.cpp installed and working
2. ✅ `server/voice/whisper.py` module created
3. ✅ `POST /api/voice/transcribe` endpoint implemented
4. ✅ `public/js/voice-recorder.js` module created
5. ✅ Voice button UI added to edit form
6. ✅ Frontend-backend integration complete
7. ✅ Error handling implemented
8. ✅ Documentation created (`docs/whisper_setup.md`, `docs/voice_input_guide.md`)
9. ✅ Testing results documented (`docs/phase8_testing.md`)
10. ✅ TODOS.md updated with Phase 8 completion

---

## Out of Scope (Phase 8 MVP)

The following features are **intentionally excluded** from Phase 8 MVP and deferred to Phase 8.1 or later:

### Deferred to Phase 8.1: LLM Parsing

- ❌ Natural language parsing ("tomorrow" → "2025-11-04")
- ❌ Auto-extraction of due dates
- ❌ Auto-extraction of due times
- ❌ Auto-extraction of priorities ("urgent" → urgent)
- ❌ Auto-extraction of locations ("at Kroger" → geocoded)
- ❌ Auto-extraction of categories ("call" → Calls)
- ❌ `POST /api/voice/parse` endpoint
- ❌ Llama 3.2 1B integration
- ❌ Smart task understanding

**Rationale**: Phase 8 MVP proves voice transcription works reliably before adding LLM complexity.

### Deferred to Future Phases

- ❌ Voice commands ("delete this reminder")
- ❌ Multi-language support (Phase 8 is English-only)
- ❌ Speaker identification
- ❌ Continuous listening mode
- ❌ Voice search/filter
- ❌ Voice confirmation ("Saved reminder: Call mom")
- ❌ Audio storage/playback
- ❌ Cloud-based transcription (always local)
- ❌ Real-time transcription (streaming)
- ❌ Custom wake word detection

### Not Included in MVP

- ❌ Audio format conversion (accept WebM/WAV as-is)
- ❌ Audio compression
- ❌ Noise cancellation (rely on Whisper robustness)
- ❌ Voice activity detection (user controls recording)
- ❌ Transcription history
- ❌ Undo transcription
- ❌ Multiple audio languages (English only)
- ❌ Whisper model selection (base.en only)
- ❌ Transcription confidence scores
- ❌ Alternative transcriptions

---

## Dependencies

Phase 8 requires the following to exist BEFORE implementation:

### Existing System Components

1. **FastAPI Backend** (Phase 1)
   - `server/main.py` with existing endpoints
   - Bearer token authentication system
   - Pydantic models structure
   - Error handling patterns

2. **Web UI** (Phase 2)
   - `public/edit.html` form structure
   - `public/css/edit.css` styling patterns
   - Form validation and submission logic

3. **API Client** (Phase 3)
   - `public/js/api.js` with fetch wrappers
   - Bearer token management
   - Error handling with retry logic
   - Toast notifications system

4. **Database** (Phase 1)
   - Reminders table with text field (varchar)
   - No database changes needed for Phase 8

### External Dependencies

1. **Whisper.cpp**
   - Repository: https://github.com/ggerganov/whisper.cpp
   - Build tools: gcc or clang (C++ compiler)
   - Model download: base.en (~74MB)
   - Installation documented in `docs/whisper_setup.md`

2. **Browser APIs**
   - MediaRecorder API (Chrome 47+, Firefox 25+, Safari 14+)
   - getUserMedia API (microphone access)
   - Blob API (audio file handling)
   - FormData API (multipart uploads)

3. **Python Packages**
   - `subprocess` (standard library, for Whisper.cpp)
   - `tempfile` (standard library, for temp audio files)
   - `pathlib` (standard library, for file paths)
   - No new dependencies to install

### System Requirements

1. **Server Environment**
   - Python 3.11+
   - FastAPI installed
   - Disk space: 100MB for Whisper.cpp + model
   - CPU: Modern processor (2017+)
   - RAM: 1GB available for transcription

2. **Client Environment**
   - Modern web browser (Chrome/Firefox/Safari latest)
   - Microphone hardware (USB or built-in)
   - Browser microphone permission granted
   - Internet connection (for initial setup only)

### Pre-Implementation Checklist

Before starting Phase 8 implementation, verify:

- ✅ Phases 1-7 completed and tested
- ✅ FastAPI server running on localhost:8000
- ✅ Edit form accessible at `/public/edit.html`
- ✅ Bearer token authentication working
- ✅ `public/js/api.js` has working fetch wrappers
- ✅ C++ compiler available (gcc or clang)
- ✅ Disk space available for Whisper.cpp
- ✅ Microphone available for testing

---

## Risk Assessment

### High Risk (Requires Mitigation)

**Risk: Whisper.cpp Installation Complexity**
- **Impact**: High (blocks entire feature)
- **Likelihood**: Medium (different OS/architectures)
- **Mitigation**: Detailed installation guide, troubleshooting section, pre-built binaries where available

**Risk: Transcription Latency**
- **Impact**: Medium (poor UX if too slow)
- **Likelihood**: Medium (varies by hardware)
- **Mitigation**: Use base.en model (fastest), document minimum requirements, show clear loading states

**Risk: Browser Compatibility**
- **Impact**: Medium (some users can't use feature)
- **Likelihood**: Low (MediaRecorder widely supported)
- **Mitigation**: Feature detection, graceful degradation, fallback to manual entry

### Medium Risk (Monitor)

**Risk: Microphone Permission Denied**
- **Impact**: Medium (feature unusable)
- **Likelihood**: Medium (users may deny)
- **Mitigation**: Clear permission instructions, helpful error messages, fallback to typing

**Risk: Transcription Accuracy**
- **Impact**: Medium (frustrating if inaccurate)
- **Likelihood**: Medium (varies by accent, noise)
- **Mitigation**: Allow editing, clear expectations, base.en model has good accuracy

### Low Risk (Accept)

**Risk: Disk Space Requirements**
- **Impact**: Low (100MB reasonable)
- **Likelihood**: Low (modern systems)
- **Mitigation**: Document requirements

**Risk: Audio Format Compatibility**
- **Impact**: Low (WebM widely supported)
- **Likelihood**: Low (modern browsers)
- **Mitigation**: Fallback to WAV if needed

---

## Acceptance Criteria

Phase 8 MVP is **ACCEPTED** when:

1. ✅ All 14 critical success criteria pass
2. ✅ All 10 test scenarios pass
3. ✅ All 10 deliverables exist and work
4. ✅ Manual testing complete in 3 browsers
5. ✅ Documentation complete and accurate
6. ✅ Human tester successfully creates reminder via voice
7. ✅ TODOS.md updated with Phase 8 completion
8. ✅ Code committed to git with proper commit messages

---

## Next Steps

After Phase 8 MVP acceptance:

1. **Gather Feedback**: Test with real users (ADHD focus)
2. **Measure Performance**: Actual latency, accuracy metrics
3. **Identify Issues**: Edge cases, browser quirks, UX pain points
4. **Plan Phase 8.1**: LLM parsing implementation (8-10 hours)
5. **Consider Enhancements**: Longer recordings, model selection, etc.

---

*Requirements Document Created: November 3, 2025*
*Phase 8 Implementation Ready*
*Estimated Completion: 12-15 hours*
