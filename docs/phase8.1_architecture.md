# Phase 8.1 Architecture Plan: Dual-Mode NLP Parsing

**Created:** November 4, 2025
**Status:** PLANNING (Research Phase)
**Author:** Claude Sonnet 4.5 (Architecture Planning Subagent)
**Parent:** Phase 8 Voice Input (MVP)

---

## Executive Summary

Phase 8.1 adds intelligent NLP parsing to the voice transcription system established in Phase 8. Users will be able to speak naturally ("Important: Call mom tomorrow at 3pm") and have the system automatically extract structured data (priority, due date, due time, category, location) from the transcribed text.

**Key Innovation:** Dual-mode architecture that supports both local (Llama 3.2 1B) and cloud (Cloudflare Workers AI) parsing, with user-configurable mode selection and intelligent fallback.

**Design Goal:** Zero additional user friction - voice input becomes truly "speak and save" with minimal manual field filling.

---

## Architecture Overview

### Dual-Mode Philosophy

```
┌─────────────────────────────────────────────────────────────┐
│                   Voice Recording (Phase 8)                  │
│                  Browser → /api/voice/transcribe             │
│                     ↓                                        │
│                Transcribed Text                              │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    NLP Parsing (Phase 8.1)                   │
│                                                              │
│  ┌─────────────────────┐      ┌─────────────────────┐      │
│  │   LOCAL MODE        │      │   CLOUD MODE        │      │
│  │  (Primary Default)  │      │    (Fallback)       │      │
│  ├─────────────────────┤      ├─────────────────────┤      │
│  │ FastAPI Server      │      │ Cloudflare Workers  │      │
│  │ Llama 3.2 1B        │      │ Workers AI          │      │
│  │ @meta-llama/...     │      │ @cf/meta/llama-...  │      │
│  │                     │      │                     │      │
│  │ POST /api/voice/    │      │ POST /api/voice/    │      │
│  │      parse          │      │      parse          │      │
│  │                     │      │                     │      │
│  │ Offline-capable     │      │ Online-only         │      │
│  │ Fast (local GPU)    │      │ No local resources  │      │
│  │ Privacy-preserving  │      │ Data to Cloudflare  │      │
│  └─────────────────────┘      └─────────────────────┘      │
│           ↓                              ↓                  │
│  ┌─────────────────────────────────────────────┐           │
│  │    Parsed Structured Data (JSON)            │           │
│  │  {                                           │           │
│  │    "text": "Call mom",                       │           │
│  │    "priority": "important",                  │           │
│  │    "due_date": "2025-11-05",                 │           │
│  │    "due_time": "15:00:00",                   │           │
│  │    "category": "Calls",                      │           │
│  │    "confidence": 0.89                        │           │
│  │  }                                           │           │
│  └─────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│               Frontend Auto-Population                       │
│    All form fields populated, user reviews & saves          │
└─────────────────────────────────────────────────────────────┘
```

### Mode Selection Strategy

**User Control (Primary)**
- Settings panel: "NLP Parsing Mode: Local / Cloud / Auto"
- Stored in localStorage (key: `nlp_mode`)
- Default: `auto` (try local → fallback to cloud)

**Auto Mode Logic**
```
User speaks → Transcribe → Try Local Parse
                              ↓
                         Success? → Use result
                              ↓ No
                         Try Cloud Parse
                              ↓
                         Success? → Use result
                              ↓ No
                         Manual fallback (text only)
```

---

## Component Architecture

### 1. Backend: FastAPI Local Endpoint

**File:** `server/nlp/parser.py` (new module)

**Endpoint:** `POST /api/voice/parse`

**Responsibilities:**
- Load Llama 3.2 1B model on server startup
- Parse natural language text into structured fields
- Return confidence scores for each extracted field
- Handle errors gracefully (model not loaded, parsing failure)

**Request Model:**
```python
class VoiceParseRequest(BaseModel):
    text: str = Field(..., description="Transcribed text to parse")
    context: Optional[dict] = Field(None, description="Optional context (user preferences, location)")
```

**Response Model:**
```python
class VoiceParseResponse(BaseModel):
    # Extracted fields
    text: str = Field(..., description="Cleaned reminder text (without metadata)")
    due_date: Optional[str] = Field(None, description="Parsed date (ISO 8601: YYYY-MM-DD)")
    due_time: Optional[str] = Field(None, description="Parsed time (ISO 8601: HH:MM:SS)")
    priority: Optional[str] = Field(None, description="Extracted priority (someday/chill/important/urgent/waiting)")
    category: Optional[str] = Field(None, description="Inferred category")
    location_name: Optional[str] = Field(None, description="Extracted location name")

    # Confidence metadata
    confidence: float = Field(..., description="Overall confidence score (0-1)")
    field_confidence: dict = Field(..., description="Per-field confidence scores")

    # Processing metadata
    model: str = Field(..., description="Model used for parsing")
    processing_time_ms: int = Field(..., description="Time taken to parse")
```

**Example:**
```json
{
  "text": "Call mom about Thanksgiving",
  "due_date": "2025-11-28",
  "due_time": "15:00:00",
  "priority": "important",
  "category": "Calls",
  "location_name": null,
  "confidence": 0.89,
  "field_confidence": {
    "due_date": 0.95,
    "due_time": 0.82,
    "priority": 0.91,
    "category": 0.87
  },
  "model": "llama-3.2-1b",
  "processing_time_ms": 487
}
```

---

### 2. Backend: Cloudflare Workers Cloud Endpoint

**File:** `workers/src/index.ts` (add endpoint)

**Endpoint:** `POST /api/voice/parse`

**Responsibilities:**
- Call Cloudflare Workers AI with Llama 3.2 1B Instruct
- Parse natural language text into structured fields
- Return same response format as local endpoint
- Handle Workers AI errors (quota exceeded, model unavailable)

**Workers AI Integration:**
```typescript
// Use @cf/meta/llama-3.2-1b-instruct model
const response = await c.env.AI.run('@cf/meta/llama-3.2-1b-instruct', {
  messages: [
    {
      role: 'system',
      content: SYSTEM_PROMPT  // JSON extraction prompt
    },
    {
      role: 'user',
      content: inputText
    }
  ],
  max_tokens: 256,
  temperature: 0.2  // Low temperature for consistent extraction
})
```

**Response Format:** Same as FastAPI endpoint (API parity)

---

### 3. Frontend: Parsing Integration

**File:** `public/js/voice-parser.js` (new module)

**Class:** `VoiceParser`

**Responsibilities:**
- Manage mode selection (local/cloud/auto)
- Call appropriate parsing endpoint
- Handle fallback logic
- Parse and apply results to form

**API:**
```javascript
class VoiceParser {
  constructor(apiClient) {
    this.api = apiClient
    this.mode = localStorage.getItem('nlp_mode') || 'auto'
  }

  /**
   * Parse transcribed text into structured fields
   * @param {string} text - Transcribed text
   * @returns {Promise<ParseResult>}
   */
  async parse(text) {
    if (this.mode === 'local' || this.mode === 'auto') {
      try {
        return await this.parseLocal(text)
      } catch (error) {
        if (this.mode === 'auto') {
          console.warn('Local parsing failed, trying cloud...', error)
          return await this.parseCloud(text)
        }
        throw error
      }
    }

    if (this.mode === 'cloud') {
      return await this.parseCloud(text)
    }
  }

  /**
   * Parse using local FastAPI endpoint
   */
  async parseLocal(text) {
    const response = await this.api.post('/api/voice/parse', { text })
    return response.data
  }

  /**
   * Parse using Cloudflare Workers endpoint
   */
  async parseCloud(text) {
    // Switch to cloud API base URL
    const cloudAPI = this.api.withBaseURL(CLOUD_API_URL)
    const response = await cloudAPI.post('/api/voice/parse', { text })
    return response.data
  }

  /**
   * Apply parsed results to form fields
   */
  applyToForm(parseResult) {
    // Auto-populate form fields with visual feedback
    if (parseResult.text) {
      setFieldValue('text', parseResult.text, parseResult.field_confidence?.text)
    }
    if (parseResult.due_date) {
      setFieldValue('due_date', parseResult.due_date, parseResult.field_confidence?.due_date)
    }
    if (parseResult.due_time) {
      setFieldValue('due_time', parseResult.due_time, parseResult.field_confidence?.due_time)
    }
    if (parseResult.priority) {
      setFieldValue('priority', parseResult.priority, parseResult.field_confidence?.priority)
    }
    if (parseResult.category) {
      setFieldValue('category', parseResult.category, parseResult.field_confidence?.category)
    }
    if (parseResult.location_name) {
      setFieldValue('location_name', parseResult.location_name, parseResult.field_confidence?.location_name)
    }
  }
}
```

---

### 4. LLM Prompt Engineering

**System Prompt (Shared by Local & Cloud)**

```
You are a precise reminder extraction assistant. Extract structured data from natural language reminder text.

**Input:** Natural language reminder (e.g., "Important: Call mom tomorrow at 3pm")

**Output:** JSON object with extracted fields

**Fields to Extract:**
- text: Core reminder text (cleaned, without metadata)
- due_date: Date in ISO 8601 format (YYYY-MM-DD) - parse relative dates like "tomorrow", "next Friday"
- due_time: Time in ISO 8601 format (HH:MM:SS) - parse "3pm" as "15:00:00"
- priority: One of: someday, chill, important, urgent, waiting
- category: Inferred category (Calls, Work, Shopping, etc.)
- location_name: Extracted location if mentioned

**Rules:**
1. Output ONLY valid JSON, no markdown formatting
2. Use null for fields not mentioned
3. Relative dates: "today" = TODAY, "tomorrow" = TODAY + 1 day
4. Priority keywords: "urgent" → urgent, "important" → important, default → chill
5. Category inference: "call" → Calls, "buy" → Shopping, "work" → Work
6. Remove priority/time/date keywords from text field

**Current Date:** {CURRENT_DATE} (e.g., "2025-11-04")

**Example Input:** "Important: Call mom tomorrow at 3pm about Thanksgiving"

**Example Output:**
{
  "text": "Call mom about Thanksgiving",
  "due_date": "2025-11-05",
  "due_time": "15:00:00",
  "priority": "important",
  "category": "Calls",
  "location_name": null
}

Now extract from the following text:
```

**Dynamic Date Injection:**
- Backend injects `{CURRENT_DATE}` with `datetime.now().date().isoformat()`
- Enables accurate relative date parsing ("tomorrow" depends on current date)

---

### 5. Confidence Scoring Mechanism

**Purpose:** Help users trust auto-populated fields

**Scoring Strategy:**

1. **Date/Time Confidence:**
   - High (0.9-1.0): Absolute date/time ("November 5th", "3:00pm")
   - Medium (0.6-0.9): Relative date/time ("tomorrow", "next week")
   - Low (0.3-0.6): Vague references ("soon", "later")

2. **Priority Confidence:**
   - High (0.9-1.0): Explicit keywords ("urgent", "important")
   - Medium (0.5-0.9): Implied urgency ("ASAP", "need to")
   - Low (0.0-0.5): No indicators (defaults to "chill")

3. **Category Confidence:**
   - High (0.8-1.0): Action verbs ("call", "buy", "email")
   - Medium (0.5-0.8): Context clues ("work project", "grocery store")
   - Low (0.0-0.5): No clear category

4. **Overall Confidence:**
   - Weighted average of field confidences
   - Formula: `(date_conf * 0.3) + (time_conf * 0.2) + (priority_conf * 0.2) + (category_conf * 0.15) + (text_quality * 0.15)`

**Visual Feedback:**
- High confidence (>0.8): Green checkmark ✓
- Medium confidence (0.5-0.8): Yellow warning ⚠
- Low confidence (<0.5): Red alert ⚠ (user should review)

---

## Data Flow Diagram

### Successful Local Parsing Flow

```
User: "Important: Call mom tomorrow at 3pm"
    ↓
[Voice Recorder] (Phase 8)
    ↓ Audio Blob
POST /api/voice/transcribe (Whisper.cpp)
    ↓
{
  "text": "Important: Call mom tomorrow at 3pm",
  "model": "base.en"
}
    ↓
[Voice Parser] (Phase 8.1)
    ↓ Mode: Auto (try local first)
POST /api/voice/parse (FastAPI + Llama 3.2 1B)
    ↓
{
  "text": "Call mom",
  "due_date": "2025-11-05",
  "due_time": "15:00:00",
  "priority": "important",
  "category": "Calls",
  "confidence": 0.89
}
    ↓
[Form Auto-Population]
    ↓
┌────────────────────────────────┐
│ Text: "Call mom" ✓             │
│ Date: 2025-11-05 ✓             │
│ Time: 15:00:00 ⚠               │
│ Priority: Important ✓          │
│ Category: Calls ✓              │
└────────────────────────────────┘
    ↓
User reviews & clicks Save
    ↓
POST /api/reminders (standard reminder creation)
```

### Fallback Flow (Local → Cloud)

```
User: "Urgent: Meeting at work next Tuesday"
    ↓
[Transcribe] → "Urgent: Meeting at work next Tuesday"
    ↓
POST /api/voice/parse (Local) → 503 Service Unavailable
    ↓ Auto mode detects failure
POST /api/voice/parse (Cloud) → Success
    ↓
{
  "text": "Meeting at work",
  "due_date": "2025-11-12",
  "priority": "urgent",
  "category": "Work",
  "confidence": 0.82
}
    ↓
Form auto-populated (user reviews & saves)
```

---

## Configuration Management

### User Settings Panel

**Location:** `public/settings.html` (add NLP section)

**UI:**
```html
<div class="setting-group">
  <h3>Voice NLP Parsing</h3>

  <label>
    <input type="radio" name="nlp_mode" value="auto" checked>
    Auto (Try Local → Fallback to Cloud)
  </label>

  <label>
    <input type="radio" name="nlp_mode" value="local">
    Local Only (Offline, requires local server)
  </label>

  <label>
    <input type="radio" name="nlp_mode" value="cloud">
    Cloud Only (Requires internet)
  </label>

  <p class="help-text">
    <strong>Auto:</strong> Best experience, tries local first for speed & privacy<br>
    <strong>Local:</strong> Fastest, offline-capable, requires Llama 3.2 1B installed<br>
    <strong>Cloud:</strong> Slower, online-only, no local setup required
  </p>
</div>
```

**Storage:**
```javascript
// Save mode to localStorage
localStorage.setItem('nlp_mode', selectedMode)

// Load on page init
const nlpMode = localStorage.getItem('nlp_mode') || 'auto'
```

---

## Error Handling Strategy

### Error Scenarios

**1. Local Model Not Loaded**
```json
{
  "detail": "NLP parsing unavailable: Model not loaded",
  "error": "model_not_loaded",
  "suggestion": "Install Llama 3.2 1B or switch to cloud mode"
}
```
**Response:** 503 Service Unavailable
**Action:** If auto mode → retry with cloud

**2. Cloud Quota Exceeded**
```json
{
  "detail": "Workers AI quota exceeded",
  "error": "quota_exceeded",
  "suggestion": "Try again later or use local mode"
}
```
**Response:** 429 Too Many Requests
**Action:** Show user-friendly message, suggest local mode

**3. Invalid Parsing Output**
```json
{
  "detail": "Failed to parse text into structured data",
  "error": "parse_failed",
  "raw_output": "Model returned invalid JSON"
}
```
**Response:** 422 Unprocessable Entity
**Action:** Fallback to manual input (transcription text only)

**4. Network Timeout**
```
Timeout after 10 seconds
```
**Action:** If auto mode → retry once with cloud
**UI:** Show "Parsing took too long, falling back to manual input"

### Graceful Degradation

**Priority Order:**
1. **Best:** Successful parsing (local or cloud)
2. **Good:** Partial parsing (some fields extracted)
3. **Acceptable:** Transcription only (no parsing)
4. **Fallback:** Manual text entry (no voice at all)

**User Experience:**
- System NEVER blocks user from creating reminder
- Parsing failures are silent (log to console)
- User always sees transcription text at minimum
- Clear visual indicators when parsing succeeds/fails

---

## Integration with Existing Voice System

### Modified Voice Input Flow (Phase 8 → 8.1)

**Phase 8 (Original):**
```javascript
// Phase 8 MVP flow
async function handleVoiceInput() {
  const audioBlob = await recorder.stop()
  const transcription = await API.transcribeAudio(audioBlob)

  // Only populate text field
  document.getElementById('text').value = transcription.text
}
```

**Phase 8.1 (Enhanced):**
```javascript
// Phase 8.1 enhanced flow
async function handleVoiceInput() {
  // Step 1: Transcribe audio (unchanged)
  const audioBlob = await recorder.stop()
  const transcription = await API.transcribeAudio(audioBlob)

  // Step 2: Parse transcription (NEW)
  try {
    const parseResult = await voiceParser.parse(transcription.text)
    voiceParser.applyToForm(parseResult)
    showConfidenceIndicators(parseResult.field_confidence)
  } catch (error) {
    console.warn('NLP parsing failed, using transcription only', error)
    document.getElementById('text').value = transcription.text
  }
}
```

**Backward Compatibility:**
- Phase 8 functionality remains unchanged if NLP parsing fails
- Users can disable NLP parsing and use Phase 8 behavior
- No breaking changes to existing endpoints

---

## Model Installation & Setup

### Local Mode: Llama 3.2 1B Setup

**Prerequisites:**
- Python 3.11+
- 8GB RAM minimum
- GPU optional (faster with CUDA/Metal)

**Installation Steps:**

```bash
# 1. Install dependencies
uv pip install transformers torch accelerate

# 2. Download model (first run)
python -c "from transformers import AutoModelForCausalLM; \
           AutoModelForCausalLM.from_pretrained('meta-llama/Llama-3.2-1B-Instruct')"

# 3. Test model loading
python server/nlp/test_model.py
```

**Model Loading Pattern:**
```python
# server/nlp/parser.py
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Load once on server startup
MODEL = None
TOKENIZER = None

def load_model():
    global MODEL, TOKENIZER
    if MODEL is None:
        MODEL = AutoModelForCausalLM.from_pretrained(
            "meta-llama/Llama-3.2-1B-Instruct",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )
        TOKENIZER = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-1B-Instruct")
    return MODEL, TOKENIZER

# Load on startup (not per-request)
load_model()
```

**Performance:**
- Cold start: ~5-10 seconds (first load)
- Inference: ~200-500ms per parse (CPU)
- Inference: ~50-150ms per parse (GPU)

### Cloud Mode: Workers AI Setup

**Prerequisites:**
- Cloudflare account with Workers AI enabled
- Wrangler CLI configured

**Configuration:**
```toml
# wrangler.toml
[ai]
binding = "AI"

[[ai.bindings]]
binding = "AI"
```

**No Installation Required:**
- Model runs on Cloudflare's infrastructure
- Automatic scaling and optimization
- Pay-per-request pricing

**Performance:**
- Cold start: N/A (serverless)
- Inference: ~500-1500ms per parse (network + compute)
- Quota: 10,000 requests/day (free tier)

---

## Testing Strategy

### Unit Tests

**Local Endpoint Tests:**
```python
# tests/test_nlp_parser.py
def test_parse_basic_reminder():
    result = parse_text("Call mom tomorrow at 3pm")
    assert result["text"] == "Call mom"
    assert result["due_date"] == (datetime.now() + timedelta(days=1)).date().isoformat()
    assert result["due_time"] == "15:00:00"
    assert result["category"] == "Calls"

def test_parse_with_priority():
    result = parse_text("Urgent: Submit report by Friday")
    assert result["priority"] == "urgent"
    assert result["text"] == "Submit report"

def test_parse_with_location():
    result = parse_text("Buy milk at Kroger")
    assert result["location_name"] == "Kroger"
    assert result["category"] == "Shopping"
```

**Cloud Endpoint Tests:**
```typescript
// workers/test/parse.test.ts
describe('POST /api/voice/parse', () => {
  it('should parse basic reminder', async () => {
    const response = await request('/api/voice/parse', {
      method: 'POST',
      body: JSON.stringify({ text: 'Call mom tomorrow at 3pm' })
    })
    expect(response.status).toBe(200)
    expect(response.data.text).toBe('Call mom')
    expect(response.data.due_time).toBe('15:00:00')
  })
})
```

### Integration Tests

**End-to-End Flow:**
```javascript
// tests/e2e/voice_parse.test.js
describe('Voice NLP Parsing', () => {
  it('should parse and populate form fields', async () => {
    // 1. Transcribe audio
    const transcription = await API.transcribeAudio(audioBlob)

    // 2. Parse transcription
    const parsed = await voiceParser.parse(transcription.text)

    // 3. Verify extraction
    expect(parsed.text).toBe('Call mom')
    expect(parsed.priority).toBe('important')
    expect(parsed.due_date).toBe('2025-11-05')

    // 4. Apply to form
    voiceParser.applyToForm(parsed)

    // 5. Verify form populated
    expect(document.getElementById('text').value).toBe('Call mom')
    expect(document.getElementById('priority').value).toBe('important')
  })
})
```

### Manual Test Cases

1. **Basic Time/Date Parsing**
   - Input: "Call dentist tomorrow at 2pm"
   - Expected: date=tomorrow, time=14:00:00, category=Calls

2. **Priority Keywords**
   - Input: "URGENT: Fix production bug"
   - Expected: priority=urgent, category=Work

3. **Location Extraction**
   - Input: "Buy groceries at Kroger"
   - Expected: location=Kroger, category=Shopping

4. **Relative Dates**
   - Input: "Meeting next Friday at noon"
   - Expected: date=next_friday, time=12:00:00

5. **Complex Parsing**
   - Input: "Important: Schedule dentist appointment for next Tuesday afternoon"
   - Expected: priority=important, date=next_tuesday, time=null (afternoon is vague)

---

## Performance Optimization

### Caching Strategy

**Problem:** Parsing same text multiple times wastes compute

**Solution:** In-memory LRU cache

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def parse_text_cached(text_hash: str, text: str):
    return parse_text(text)

def parse_with_cache(text: str):
    text_hash = hashlib.md5(text.encode()).hexdigest()
    return parse_text_cached(text_hash, text)
```

**Benefit:** Instant responses for repeated queries

### Model Quantization

**Problem:** Llama 3.2 1B uses ~4GB RAM

**Solution:** Use INT8 quantization

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_8bit=True,
    bnb_8bit_compute_dtype=torch.float16
)

MODEL = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-1B-Instruct",
    quantization_config=quantization_config,
    device_map="auto"
)
```

**Benefit:** Reduces memory usage to ~2GB with minimal accuracy loss

### Prompt Optimization

**Goal:** Minimize token usage while maintaining accuracy

**Strategy:**
- Use shorter system prompts (tested examples removed after validation)
- Use JSON mode if supported by model
- Set max_tokens=256 (JSON output rarely exceeds this)
- Temperature=0.2 (low variance for consistency)

---

## Security & Privacy Considerations

### Data Flow

**Local Mode:**
- ✅ Transcription never leaves device
- ✅ Parsing happens on local server
- ✅ No external API calls
- ✅ ADHD-friendly (private thoughts stay private)

**Cloud Mode:**
- ⚠️ Transcription sent to Cloudflare Workers
- ⚠️ Processed by Workers AI (ephemeral, not stored)
- ⚠️ Network transmission (HTTPS encrypted)
- ℹ️ Cloudflare's data policy applies

### User Transparency

**Settings Panel Disclaimer:**
```
🔒 Privacy Notice:
- Local Mode: Your voice data never leaves your device
- Cloud Mode: Transcriptions are sent to Cloudflare for processing
  (not stored, ephemeral processing only)
- Auto Mode: Tries local first, falls back to cloud if needed

We recommend Local Mode for sensitive reminders.
```

---

## Success Criteria

### Phase 8.1 Complete When:

**Core Functionality:**
- ✅ Local parsing endpoint working (`POST /api/voice/parse`)
- ✅ Cloud parsing endpoint working (Cloudflare Workers)
- ✅ Frontend mode selection UI implemented
- ✅ Fallback logic working (local → cloud → manual)
- ✅ Form auto-population working with visual feedback
- ✅ Confidence scores calculated and displayed

**Quality Metrics:**
- ✅ Date parsing accuracy >90% for common phrases
- ✅ Time parsing accuracy >85% for common formats
- ✅ Priority extraction accuracy >80%
- ✅ Category inference accuracy >70%
- ✅ Overall confidence calibration (high confidence = high accuracy)

**Performance Targets:**
- ✅ Local parsing latency <500ms (CPU) or <150ms (GPU)
- ✅ Cloud parsing latency <2 seconds
- ✅ End-to-end flow (voice → parsed form) <10 seconds

**User Experience:**
- ✅ Zero additional clicks for successful parsing
- ✅ Clear visual feedback for parsed fields
- ✅ Graceful degradation on parsing failures
- ✅ Settings panel working with mode persistence

**Documentation:**
- ✅ Model installation guide for local mode
- ✅ Workers AI setup guide for cloud mode
- ✅ User guide with examples
- ✅ Testing results documented

---

## Implementation Roadmap

### Subagent Breakdown (8 subagents)

**Research Phase (THIS DOCUMENT - COMPLETE)**
1. ✅ Architecture Planning Subagent (this document)

**Development Phase (7 subagents)**

1. **LLM Prompt Engineering Subagent** (~2 hours)
   - Design and test system prompt
   - Validate JSON output format
   - Test date/time parsing accuracy
   - Document prompt patterns
   - Commit: `feat(nlp): design LLM prompt for reminder extraction`

2. **Local NLP Parser Subagent** (~3 hours)
   - Create `server/nlp/parser.py`
   - Implement model loading (Llama 3.2 1B)
   - Implement parse_text() function
   - Add confidence scoring logic
   - Commit: `feat(nlp): implement local Llama 3.2 1B parser`

3. **Local Parse Endpoint Subagent** (~2 hours)
   - Add `POST /api/voice/parse` to `server/main.py`
   - Add Pydantic models to `server/models.py`
   - Integrate parser module
   - Add error handling
   - Commit: `feat(api): add local voice parse endpoint`

4. **Cloud Parse Endpoint Subagent** (~2 hours)
   - Add `POST /api/voice/parse` to `workers/src/index.ts`
   - Integrate Workers AI
   - Match local endpoint response format
   - Add error handling
   - Commit: `feat(cloud): add Workers AI parse endpoint`

5. **Frontend Parser Integration Subagent** (~3 hours)
   - Create `public/js/voice-parser.js`
   - Implement VoiceParser class
   - Add mode selection logic
   - Add fallback logic
   - Commit: `feat(frontend): implement voice parser with dual-mode support`

6. **Settings UI Subagent** (~2 hours)
   - Add NLP settings section to `public/settings.html`
   - Add mode selection radio buttons
   - Implement localStorage persistence
   - Add help text and privacy notice
   - Commit: `feat(ui): add NLP mode settings panel`

7. **Form Auto-Population Subagent** (~3 hours)
   - Implement applyToForm() logic
   - Add confidence visual indicators
   - Add field-level validation
   - Integrate with existing edit form
   - Commit: `feat(ui): add auto-population with confidence indicators`

8. **Testing & Documentation Subagent** (~3 hours)
   - Write unit tests (Python + TypeScript)
   - Write integration tests
   - Manual test all scenarios
   - Document installation steps
   - Update user guide
   - Commit: `docs(nlp): add Phase 8.1 testing results and user guide`

**Total Estimated Time:** ~20 hours (2.5 work days)

---

## Alternative Approaches Considered

### Why Not OpenAI GPT-4?
- ❌ Requires API key and internet (no offline mode)
- ❌ Costs per request ($0.01-0.03 per parse)
- ❌ Privacy concerns (data sent to OpenAI)
- ✅ Llama 3.2 1B runs locally and is free

### Why Not Phi-3 Mini?
- ⚠️ Similar size and capabilities to Llama 3.2 1B
- ⚠️ Less tested for JSON extraction tasks
- ✅ Llama 3.2 has better Instruct variant

### Why Not Cloud-Only?
- ❌ Breaks offline-first philosophy
- ❌ Adds latency (network round-trip)
- ❌ Privacy concerns for ADHD users
- ✅ Dual-mode gives best of both worlds

### Why Not On-Device Browser Models?
- ❌ TensorFlow.js/ONNX too slow for 1B model
- ❌ WebGPU support still limited
- ❌ Model quantization complex in browser
- ✅ Local server has full Python ecosystem

---

## Risk Analysis

### Technical Risks

**Risk 1: Model Loading Time**
- **Likelihood:** High
- **Impact:** Medium
- **Mitigation:** Load model on server startup, not per-request

**Risk 2: Parsing Accuracy**
- **Likelihood:** Medium
- **Impact:** High
- **Mitigation:** Confidence scoring, manual review, extensive testing

**Risk 3: Workers AI Quota**
- **Likelihood:** Low (free tier = 10k/day)
- **Impact:** Medium
- **Mitigation:** Fallback to local, user notification

### User Experience Risks

**Risk 1: User Confusion (Auto vs Manual)**
- **Likelihood:** Medium
- **Impact:** Low
- **Mitigation:** Clear onboarding, default to auto mode

**Risk 2: Over-Trust in Parsing**
- **Likelihood:** Medium
- **Impact:** Medium
- **Mitigation:** Visual confidence indicators, encourage review

**Risk 3: Installation Complexity (Local Mode)**
- **Likelihood:** High (technical users only)
- **Impact:** Medium
- **Mitigation:** Detailed guide, cloud fallback, auto mode default

---

## Next Steps

**For Development Subagent:**

1. Read this architecture document fully
2. Start with Subagent 1 (Prompt Engineering)
3. Proceed sequentially through subagents 1-8
4. Each subagent = one focused task = one commit
5. Test after each subagent
6. Document deviations from plan

**Quick Start Commands:**
```bash
# Pull latest
git pull origin main

# Install NLP dependencies
cd server
uv pip install transformers torch accelerate

# Test model loading
python -c "from transformers import AutoTokenizer; \
           AutoTokenizer.from_pretrained('meta-llama/Llama-3.2-1B-Instruct')"

# Start development
# (Follow subagent 1 instructions)
```

---

## Appendix: Example Parsing Cases

### Test Case 1: Basic Time/Date
**Input:** "Call dentist tomorrow at 2pm"

**Expected Output:**
```json
{
  "text": "Call dentist",
  "due_date": "2025-11-05",
  "due_time": "14:00:00",
  "priority": "chill",
  "category": "Calls",
  "location_name": null,
  "confidence": 0.87
}
```

### Test Case 2: Priority + Relative Date
**Input:** "Important: Submit report next Friday"

**Expected Output:**
```json
{
  "text": "Submit report",
  "due_date": "2025-11-08",
  "due_time": null,
  "priority": "important",
  "category": "Work",
  "location_name": null,
  "confidence": 0.82
}
```

### Test Case 3: Location-Based
**Input:** "Buy milk and eggs at Kroger"

**Expected Output:**
```json
{
  "text": "Buy milk and eggs",
  "due_date": null,
  "due_time": null,
  "priority": "chill",
  "category": "Shopping",
  "location_name": "Kroger",
  "confidence": 0.76
}
```

### Test Case 4: Complex Urgency
**Input:** "URGENT: Fix production server ASAP"

**Expected Output:**
```json
{
  "text": "Fix production server",
  "due_date": null,
  "due_time": null,
  "priority": "urgent",
  "category": "Work",
  "location_name": null,
  "confidence": 0.91
}
```

---

*Architecture Plan Created: November 4, 2025*
*Ready for Development Phase*
*Estimated Completion: Phase 8.1 complete in ~20 hours*
