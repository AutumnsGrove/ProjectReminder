# Phase 8.1 Requirements: LLM Natural Language Parsing

**Status**: Research Phase
**Created**: November 4, 2025
**Phase**: 8.1 - NLP Auto-extraction
**Prerequisites**: Phase 8 (Voice Transcription) Complete

---

## Executive Summary

Phase 8.1 implements intelligent natural language parsing to automatically extract reminder metadata (dates, times, priorities, locations, categories) from voice transcriptions using a dual-mode architecture:

1. **Local Mode** - Llama 3.2 1B via LM Studio (offline, privacy-first)
2. **Cloud Mode** - Cloudflare Workers AI (online fallback)

This eliminates the manual form-filling step after voice input, transforming Phase 8's transcription-only workflow into a true voice-to-reminder pipeline.

**Example Transformation**:
```
Voice Input: "Call mom about Thanksgiving tomorrow at 3pm, this is urgent"

Phase 8 Output (Current):
└─ Text: "Call mom about Thanksgiving tomorrow at 3pm, this is urgent"
└─ User manually sets: due_date, due_time, priority, category

Phase 8.1 Output (Target):
├─ Text: "Call mom about Thanksgiving"
├─ Due Date: 2025-11-05 (parsed "tomorrow")
├─ Due Time: 15:00:00 (parsed "3pm")
├─ Priority: urgent (parsed "this is urgent")
├─ Category: Calls (inferred from "call")
└─ Confidence: 0.95 (high confidence auto-fill)
```

---

## 1. Functional Requirements

### FR1: Natural Language Date Parsing
**ID**: FR1
**Priority**: Critical
**Description**: Extract due dates from natural language expressions

**Supported Formats**:
- Relative dates: "today", "tomorrow", "next Friday", "in 3 days"
- Absolute dates: "December 25", "12/25", "2025-12-25", "Dec 25th"
- Day-of-week: "Monday", "this Thursday", "next Tuesday"
- Implicit dates: "tonight" → today with time, "this weekend" → nearest Saturday

**Examples**:
| Input Text | Parsed Date | Notes |
|------------|-------------|-------|
| "tomorrow" | 2025-11-05 | Relative to today (2025-11-04) |
| "next Friday" | 2025-11-08 | Next occurrence of Friday |
| "December 25" | 2025-12-25 | Assumes current year |
| "in 3 days" | 2025-11-07 | Today + 3 days |
| "tonight" | 2025-11-04 | Today with evening time |

**Edge Cases**:
- No date mentioned → due_date = null (manual selection)
- Ambiguous dates ("Monday" when today is Monday) → next Monday
- Past dates ("yesterday") → today (assume user means future)

---

### FR2: Natural Language Time Parsing
**ID**: FR2
**Priority**: Critical
**Description**: Extract due times from natural language expressions

**Supported Formats**:
- 12-hour format: "3pm", "3:30pm", "at 3 o'clock"
- 24-hour format: "15:00", "1500"
- Named times: "noon", "midnight", "morning", "evening", "tonight"
- Relative times: "in 2 hours", "in 30 minutes"

**Examples**:
| Input Text | Parsed Time | time_required |
|------------|-------------|---------------|
| "at 3pm" | 15:00:00 | true |
| "3:30pm" | 15:30:00 | true |
| "noon" | 12:00:00 | true |
| "morning" | 09:00:00 | false |
| "tonight" | 20:00:00 | false |
| "in 2 hours" | (current + 2h) | true |

**time_required Logic**:
- Specific times ("3pm", "3:30pm") → time_required = true
- Vague times ("morning", "evening") → time_required = false
- No time mentioned → due_time = null, time_required = false

**Edge Cases**:
- 12-hour ambiguity ("3 o'clock" → assume PM if afternoon/evening context)
- Timezone handling → Use local time (no timezone conversion in MVP)
- Past times ("2 hours ago") → assume future (add 12 hours if AM/PM flip needed)

---

### FR3: Priority Level Parsing
**ID**: FR3
**Priority**: High
**Description**: Extract priority from keywords and phrases

**Priority Levels**: someday, chill, important, urgent, waiting

**Detection Keywords**:
| Priority | Keywords/Phrases |
|----------|------------------|
| urgent | "urgent", "asap", "right away", "critical", "emergency", "immediately" |
| important | "important", "need to", "must", "should", "don't forget" |
| chill | "chill", "when I get time", "eventually", "no rush" |
| someday | "someday", "maybe", "might", "consider", "think about" |
| waiting | "waiting for", "pending", "blocked by", "when X happens" |

**Default**: chill (if no priority keywords detected)

**Examples**:
| Input Text | Priority | Confidence |
|------------|----------|-----------|
| "Call mom, this is urgent" | urgent | 0.95 |
| "Important: file taxes by April" | important | 0.90 |
| "Maybe buy new laptop someday" | someday | 0.85 |
| "Waiting for email from Sarah" | waiting | 0.90 |
| "Buy groceries" | chill | 0.60 (default) |

**Edge Cases**:
- Multiple priorities mentioned → Use highest priority
- Negations ("not urgent") → Ignore priority keyword
- Contextual hints ("before 5pm" implies urgency) → Boost to important

---

### FR4: Location Parsing
**ID**: FR4
**Priority**: High
**Description**: Extract location names from natural language

**Detection Patterns**:
- Explicit: "at [location]", "when I'm at [location]"
- Implicit: "when I get to [location]"
- Store names: "at Kroger", "at Home Depot"
- Generic places: "at work", "at home", "at the gym"

**Examples**:
| Input Text | location_name | Notes |
|------------|---------------|-------|
| "Buy milk at Kroger" | Kroger | Store name |
| "When I'm at work, call John" | work | Generic place |
| "Pick up package at Home Depot" | Home Depot | Store name |
| "Buy groceries" | null | No location mentioned |

**Geocoding Requirement**:
- Phase 8.1 extracts location_name only
- MapBox geocoding happens in frontend (existing Phase 6 logic)
- LLM does NOT generate lat/lng (avoid hallucinations)

**Edge Cases**:
- Multiple locations → Use first location mentioned
- Ambiguous locations ("the store") → Extract as-is, let user clarify
- Non-existent locations → Extract anyway (geocoding will fail gracefully)

---

### FR5: Category Inference
**ID**: FR5
**Priority**: Medium
**Description**: Infer category from reminder text context

**Common Categories**: Calls, Shopping, Work, Personal, Health, Finance, Errands, Home

**Inference Examples**:
| Input Text | Category | Confidence |
|------------|----------|-----------|
| "Call mom about dinner" | Calls | 0.95 |
| "Buy groceries at Kroger" | Shopping | 0.90 |
| "Finish project proposal" | Work | 0.85 |
| "Dentist appointment tomorrow" | Health | 0.90 |
| "Pay rent" | Finance | 0.95 |
| "Pick up dry cleaning" | Errands | 0.85 |

**Default**: null (if confidence < 0.70, let user categorize manually)

**Action Verb Hints**:
- "call", "text", "email" → Calls
- "buy", "purchase", "get" → Shopping
- "finish", "complete", "submit" → Work
- "pay", "deposit", "transfer" → Finance
- "pick up", "drop off" → Errands

**Edge Cases**:
- Multiple categories ("Call dentist to schedule appointment") → Choose best fit (Health > Calls)
- Vague text ("Do the thing") → category = null

---

### FR6: Reminder Text Cleaning
**ID**: FR6
**Priority**: High
**Description**: Extract clean reminder text by removing metadata phrases

**Removal Patterns**:
- Dates: "tomorrow", "next Friday", "on December 25"
- Times: "at 3pm", "at noon", "tonight"
- Priority phrases: "this is urgent", "important", "asap"
- Location phrases: "at Kroger", "when I'm at work"

**Examples**:
| Original Transcription | Cleaned Text |
|------------------------|--------------|
| "Call mom tomorrow at 3pm, this is urgent" | "Call mom" |
| "Buy milk at Kroger when I get time" | "Buy milk" |
| "Finish report by Friday, important" | "Finish report" |
| "Pick up dry cleaning on Main Street" | "Pick up dry cleaning" |

**Preservation Rules**:
- Keep subject/object: "Call mom" (keep), "about dinner" (keep)
- Remove modifiers: "tomorrow" (remove), "urgent" (remove)
- Keep prepositions if part of action: "Pick up" (keep), "at 3pm" (remove)

**Edge Cases**:
- Ambiguous removal: "Call about tomorrow's meeting" → Keep "tomorrow's" (it's the subject, not a date)
- Over-cleaning: Ensure minimum 3 words remain if possible
- Under-cleaning: If unsure, keep the text (user can edit)

---

### FR7: Confidence Scoring
**ID**: FR7
**Priority**: Critical
**Description**: Generate confidence scores for each parsed field

**Confidence Levels**:
- High: 0.80-1.00 → Auto-fill, no warning
- Medium: 0.60-0.79 → Auto-fill with yellow highlight (editable)
- Low: 0.00-0.59 → Do not auto-fill, leave blank

**Per-Field Scoring**:
| Field | High Confidence | Medium Confidence | Low Confidence |
|-------|----------------|-------------------|----------------|
| due_date | "tomorrow", "Friday" | "next week", "soon" | "later", "sometime" |
| due_time | "3pm", "noon" | "morning", "evening" | "later", vague |
| priority | Exact keyword match | Contextual hint | No keywords |
| location_name | "at [Store]" | Generic "at work" | Ambiguous "there" |
| category | Strong verb match | Weak contextual hint | No clear category |

**Global Confidence Threshold**:
- If overall_confidence < 0.50 → Fallback to manual entry
- Display message: "Couldn't parse reminder details, please fill manually"

**Examples**:
| Input Text | Overall Confidence | Action |
|------------|-------------------|--------|
| "Call mom tomorrow at 3pm" | 0.95 (high) | Auto-fill all fields |
| "Buy groceries sometime soon" | 0.65 (medium) | Auto-fill with yellow highlights |
| "Do the thing" | 0.30 (low) | Manual entry fallback |

---

### FR8: Ambiguity Handling
**ID**: FR8
**Priority**: High
**Description**: Gracefully handle ambiguous or incomplete inputs

**Ambiguity Types**:

**A. Multiple Dates**:
- Input: "Call mom tomorrow and schedule dentist for Friday"
- Strategy: Use first date mentioned (tomorrow)
- Note: Future enhancement could split into 2 reminders

**B. Conflicting Priorities**:
- Input: "Important but not urgent, call Sarah"
- Strategy: Use explicit keywords > contextual hints (important wins)

**C. Vague Timing**:
- Input: "Buy milk soon"
- Strategy: due_date = null, confidence = 0.40 (manual entry)

**D. Implicit Context**:
- Input: "Same time as last week"
- Strategy: Cannot resolve without history → confidence = 0.20 (manual)

**E. Typos/Misspellings**:
- Input: "Call mom tommorow" (typo: "tommorow")
- Strategy: Use fuzzy matching for common date keywords

**Fallback Strategy**:
1. Attempt to parse each field independently
2. If field confidence < 0.60 → Leave field empty
3. If overall confidence < 0.50 → Return empty parse (manual fallback)
4. Always preserve original transcription text

---

## 2. Dual-Mode Architecture Requirements

### AR1: Local Mode (Llama 3.2 1B via LM Studio)
**ID**: AR1
**Priority**: Critical

**Configuration**:
- **Model**: Llama 3.2 1B Instruct (already installed via LM Studio)
- **Access**: HTTP API at `http://127.0.0.1:1234/v1/chat/completions`
- **Endpoint**: `POST /api/voice/parse` (FastAPI)
- **Advantages**:
  - Offline operation (privacy-first)
  - No API costs
  - Fast inference (<1s on M4)
  - Full control over prompts

**Request Format** (OpenAI-compatible):
```json
{
  "model": "llama-3.2-1b-instruct",
  "messages": [
    {"role": "system", "content": "[System prompt]"},
    {"role": "user", "content": "Call mom tomorrow at 3pm, urgent"}
  ],
  "temperature": 0.1,
  "max_tokens": 300,
  "response_format": {"type": "json_object"}
}
```

**Expected Response**:
```json
{
  "text": "Call mom",
  "due_date": "2025-11-05",
  "due_time": "15:00:00",
  "time_required": true,
  "priority": "urgent",
  "category": "Calls",
  "location_name": null,
  "confidence": {
    "overall": 0.95,
    "due_date": 0.98,
    "due_time": 0.95,
    "priority": 0.90,
    "category": 0.85
  }
}
```

**Performance Requirements**:
- Latency: <3 seconds end-to-end
- Accuracy: >80% for dates/times, >70% for priorities
- Fallback: If LM Studio not running → Return 503 error with helpful message

---

### AR2: Cloud Mode (Cloudflare Workers AI)
**ID**: AR2
**Priority**: High

**Configuration**:
- **Model**: `@cf/meta/llama-3.2-1b-instruct` (Cloudflare's hosted version)
- **Access**: Workers AI API (requires Cloudflare account)
- **Endpoint**: `POST /api/voice/parse` (Cloudflare Workers)
- **Advantages**:
  - No local installation required
  - Accessible from cloud API (multi-device sync)
  - Automatic scaling

**Request Format** (Cloudflare Workers AI):
```typescript
const response = await env.AI.run('@cf/meta/llama-3.2-1b-instruct', {
  messages: [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: reminderText }
  ],
  temperature: 0.1,
  max_tokens: 300
});
```

**Expected Response**: Same JSON structure as local mode

**Performance Requirements**:
- Latency: <5 seconds end-to-end (includes network latency)
- Accuracy: Same as local mode (same model)
- Fallback: If Workers AI fails → Return 503 error

**Cost Considerations**:
- Free tier: 10,000 requests/day (sufficient for personal use)
- Paid tier: $0.01 per 1,000 requests (after free tier)

---

### AR3: Mode Selection & Fallback
**ID**: AR3
**Priority**: Critical

**Default Mode**: Local (if available)

**Mode Selection Logic**:
```
1. User clicks voice button
2. Check if local API (localhost:8000) is reachable
   ├─ Yes → Use local mode (Llama 3.2 1B via LM Studio)
   └─ No → Use cloud mode (Cloudflare Workers AI)
3. If both fail → Manual entry fallback
```

**Configuration Toggle** (secrets.json):
```json
{
  "parsing_mode": "auto",  // Options: "auto", "local", "cloud", "manual"
  "local_llm_url": "http://127.0.0.1:1234/v1/chat/completions",
  "cloudflare_account_id": "your-account-id",
  "cloudflare_api_token": "your-api-token"
}
```

**Fallback Hierarchy**:
1. Local mode (LM Studio)
2. Cloud mode (Cloudflare Workers AI)
3. Manual entry (original Phase 8 behavior)

**User Notification**:
- Display parsing mode in UI: "Parsing locally..." or "Parsing via cloud..."
- If fallback to manual: "Couldn't parse automatically, please fill fields manually"

---

## 3. API Contract Specifications

### API3.1: POST /api/voice/parse (FastAPI Local)

**Endpoint**: `POST /api/voice/parse`
**Auth**: Bearer token required
**Request Body**:
```json
{
  "text": "Call mom tomorrow at 3pm, this is urgent",
  "current_datetime": "2025-11-04T14:30:00Z"  // Optional, defaults to server time
}
```

**Response 200 OK**:
```json
{
  "text": "Call mom",
  "due_date": "2025-11-05",
  "due_time": "15:00:00",
  "time_required": true,
  "priority": "urgent",
  "category": "Calls",
  "location_name": null,
  "confidence": {
    "overall": 0.95,
    "due_date": 0.98,
    "due_time": 0.95,
    "priority": 0.90,
    "category": 0.85,
    "location_name": 0.0
  },
  "parse_mode": "local",
  "model": "llama-3.2-1b-instruct"
}
```

**Response 400 Bad Request**:
```json
{
  "detail": "Text field is required",
  "error": "validation_error"
}
```

**Response 503 Service Unavailable**:
```json
{
  "detail": "LLM parsing service unavailable. Please ensure LM Studio is running at http://127.0.0.1:1234",
  "error": "llm_unavailable",
  "fallback": "manual_entry"
}
```

**Response 504 Gateway Timeout**:
```json
{
  "detail": "LLM parsing timeout (>5 seconds). Please try again.",
  "error": "llm_timeout",
  "fallback": "manual_entry"
}
```

---

### API3.2: POST /api/voice/parse (Cloudflare Workers)

**Endpoint**: `POST /api/voice/parse`
**Auth**: Bearer token required
**Request/Response**: Same as local mode (API parity)

**Additional Error Responses**:

**Response 429 Too Many Requests**:
```json
{
  "detail": "Cloudflare Workers AI rate limit exceeded (10,000 requests/day)",
  "error": "rate_limit_exceeded",
  "fallback": "manual_entry"
}
```

**Response 402 Payment Required**:
```json
{
  "detail": "Cloudflare Workers AI free tier exhausted. Please upgrade or use local mode.",
  "error": "quota_exceeded",
  "fallback": "local_mode"
}
```

---

### API3.3: Pydantic Models (FastAPI)

**Request Model**:
```python
class VoiceParseRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, description="Transcribed reminder text")
    current_datetime: Optional[str] = Field(None, description="ISO 8601 timestamp for relative date parsing")
```

**Response Model**:
```python
class ConfidenceScores(BaseModel):
    overall: float = Field(..., ge=0.0, le=1.0)
    due_date: float = Field(..., ge=0.0, le=1.0)
    due_time: float = Field(..., ge=0.0, le=1.0)
    priority: float = Field(..., ge=0.0, le=1.0)
    category: float = Field(..., ge=0.0, le=1.0)
    location_name: float = Field(..., ge=0.0, le=1.0)

class VoiceParseResponse(BaseModel):
    text: str = Field(..., description="Cleaned reminder text")
    due_date: Optional[str] = Field(None, description="ISO 8601 date (YYYY-MM-DD)")
    due_time: Optional[str] = Field(None, description="ISO 8601 time (HH:MM:SS)")
    time_required: bool = Field(False, description="Time is specific (not flexible)")
    priority: Literal["someday", "chill", "important", "urgent", "waiting"] = Field("chill")
    category: Optional[str] = Field(None, max_length=100)
    location_name: Optional[str] = Field(None, max_length=500)
    confidence: ConfidenceScores
    parse_mode: Literal["local", "cloud"] = Field(..., description="Which LLM mode was used")
    model: str = Field(..., description="LLM model name")
```

---

## 4. Success Criteria

Phase 8.1 is considered complete when ALL of the following criteria are met:

### SC1: Date Parsing Accuracy
- ✅ Correctly parse "tomorrow", "next Friday", "in 3 days" (relative dates)
- ✅ Correctly parse "December 25", "12/25", "Dec 25th" (absolute dates)
- ✅ Handle edge cases: No date → null, past dates → today, ambiguous → next occurrence
- ✅ Accuracy: >85% on 20+ test cases

### SC2: Time Parsing Accuracy
- ✅ Correctly parse "3pm", "3:30pm", "noon", "midnight" (specific times)
- ✅ Correctly parse "morning", "evening", "tonight" (flexible times)
- ✅ Set time_required = true for specific, false for flexible
- ✅ Accuracy: >80% on 20+ test cases

### SC3: Priority Detection Accuracy
- ✅ Correctly identify "urgent", "important", "chill", "someday", "waiting"
- ✅ Default to "chill" when no keywords present
- ✅ Handle multiple priorities (choose highest)
- ✅ Accuracy: >75% on 20+ test cases

### SC4: Location Extraction Accuracy
- ✅ Extract location names from "at [location]" patterns
- ✅ Handle store names ("Kroger", "Home Depot")
- ✅ Handle generic places ("work", "home")
- ✅ Accuracy: >70% on 20+ test cases

### SC5: Category Inference Accuracy
- ✅ Infer categories from action verbs and context
- ✅ Return null if confidence < 0.70
- ✅ Common categories: Calls, Shopping, Work, Health, Finance, Errands
- ✅ Accuracy: >65% on 20+ test cases

### SC6: Text Cleaning Quality
- ✅ Remove date/time/priority/location phrases
- ✅ Preserve subject and action ("Call mom", "Buy groceries")
- ✅ Maintain readability (min 2-3 words if possible)
- ✅ Quality: >80% of cleaned texts are clear and concise

### SC7: Confidence Scoring Reliability
- ✅ Generate per-field confidence scores (0.0-1.0)
- ✅ Overall confidence reflects parsing quality
- ✅ High confidence (>0.80) → Auto-fill without warning
- ✅ Low confidence (<0.60) → Leave field empty
- ✅ Fallback to manual entry if overall < 0.50

### SC8: Dual-Mode Operation
- ✅ Local mode works with LM Studio (llama-3.2-1b-instruct)
- ✅ Cloud mode works with Cloudflare Workers AI
- ✅ Mode selection: auto-detect local availability → fallback to cloud
- ✅ Configuration toggle in secrets.json

### SC9: Performance Requirements
- ✅ Local mode latency: <3 seconds (transcribe + parse)
- ✅ Cloud mode latency: <5 seconds (transcribe + parse + network)
- ✅ No blocking: UI remains responsive during parsing
- ✅ Graceful degradation: Fallback to manual entry on failure

### SC10: Integration with Existing System
- ✅ Voice button triggers: Record → Transcribe → Parse → Auto-fill
- ✅ Parsed fields populate edit form automatically
- ✅ User can edit any auto-filled field
- ✅ Low confidence fields highlighted (yellow border) as editable suggestions
- ✅ Manual entry still available if parsing fails

### SC11: Error Handling
- ✅ Handle LLM unavailable (503 error with helpful message)
- ✅ Handle LLM timeout (>5s → fallback to manual)
- ✅ Handle rate limits (Cloudflare Workers AI free tier)
- ✅ Handle invalid responses (malformed JSON → retry once)
- ✅ All errors display user-friendly toast notifications

### SC12: Testing Coverage
- ✅ 20+ unit tests for parsing logic (dates, times, priorities, locations, categories)
- ✅ 10+ integration tests for API endpoints (local and cloud)
- ✅ 5+ end-to-end tests (voice → transcribe → parse → display)
- ✅ Manual testing with real voice inputs (20+ varied scenarios)

---

## 5. Non-Functional Requirements

### NFR1: Performance
- Parsing latency: <3 seconds (local), <5 seconds (cloud)
- LLM response time: <2 seconds (95th percentile)
- No UI blocking during parsing (async operations)
- Memory usage: <100MB additional (for LLM client libraries)

### NFR2: Accuracy
- Overall parsing accuracy: >75% across all fields
- Date parsing: >85% accuracy
- Time parsing: >80% accuracy
- Priority detection: >75% accuracy
- Category inference: >65% accuracy

### NFR3: Privacy & Security
- Local mode: Zero data leaves device (100% offline)
- Cloud mode: Only reminder text sent to Cloudflare (no PII)
- No audio storage on cloud (already handled in Phase 8)
- API tokens stored in secrets.json (never committed to git)

### NFR4: Reliability
- Fallback to manual entry: 100% of cases where parsing fails
- No crashes on malformed LLM responses (validate JSON)
- Graceful degradation: System works without LLM (Phase 8 behavior)
- Error recovery: Retry once on transient failures, then fallback

### NFR5: Usability
- Confidence indicators: Visual cues (green = high, yellow = medium, empty = low)
- Editable fields: All auto-filled fields remain user-editable
- Clear feedback: Toast notifications for parsing status
- Discoverability: No UI changes (parsing happens transparently)

### NFR6: Maintainability
- System prompt externalized (easy to tune without code changes)
- Parsing logic isolated in separate module (server/voice/parsing.py)
- Unit tests cover edge cases (regression prevention)
- Logging for debugging (LLM requests/responses, parsing failures)

### NFR7: Scalability
- Local mode: No scalability concerns (single-user device)
- Cloud mode: Cloudflare Workers AI auto-scales (10k req/day free tier)
- Rate limiting: Enforce 100 requests/minute per user (prevent abuse)

---

## 6. Integration Requirements

### INT1: Voice Recorder Integration
**Touchpoint**: `public/js/voice-recorder.js` → `public/js/app.js`

**Current Flow** (Phase 8):
```
1. User clicks mic button
2. VoiceRecorder.startRecording()
3. User speaks → VoiceRecorder.stopRecording()
4. Audio blob → API.transcribeAudio()
5. Text → Populate reminder text field
6. User manually fills: date, time, priority, category, location
```

**New Flow** (Phase 8.1):
```
1-4. [Same as Phase 8]
5. Text → API.parseReminderText()  ← NEW
6. Auto-fill fields:
   ├─ reminder_text (cleaned)
   ├─ due_date (if confidence > 0.60)
   ├─ due_time (if confidence > 0.60)
   ├─ time_required (from parsing)
   ├─ priority (if confidence > 0.60)
   ├─ category (if confidence > 0.70)
   └─ location_name (if confidence > 0.60)
7. Apply visual confidence indicators (green/yellow borders)
8. User edits any field if needed
```

**Code Changes**:
- `public/js/api.js`: Add `parseReminderText(text)` function
- `public/js/app.js`: Call `parseReminderText()` after `transcribeAudio()`
- `public/js/app.js`: Populate form fields with parsed data
- `public/css/edit.css`: Add `.field-high-confidence` and `.field-medium-confidence` styles

---

### INT2: Edit Form Integration
**Touchpoint**: `public/edit.html` → Form field population

**Auto-Fill Logic**:
```javascript
function applyParsedData(parseResult) {
  // Text field (always fill)
  document.getElementById('reminder-text').value = parseResult.text;

  // Date field (if confidence > 0.60)
  if (parseResult.due_date && parseResult.confidence.due_date > 0.60) {
    document.getElementById('due-date').value = parseResult.due_date;
    applyConfidenceStyle('due-date', parseResult.confidence.due_date);
  }

  // Time field (if confidence > 0.60)
  if (parseResult.due_time && parseResult.confidence.due_time > 0.60) {
    document.getElementById('due-time').value = parseResult.due_time;
    document.getElementById('time-required').checked = parseResult.time_required;
    applyConfidenceStyle('due-time', parseResult.confidence.due_time);
  }

  // Priority field (if confidence > 0.60)
  if (parseResult.priority && parseResult.confidence.priority > 0.60) {
    document.getElementById('priority').value = parseResult.priority;
    applyConfidenceStyle('priority', parseResult.confidence.priority);
  }

  // Category field (if confidence > 0.70)
  if (parseResult.category && parseResult.confidence.category > 0.70) {
    document.getElementById('category').value = parseResult.category;
    applyConfidenceStyle('category', parseResult.confidence.category);
  }

  // Location field (if confidence > 0.60)
  if (parseResult.location_name && parseResult.confidence.location_name > 0.60) {
    document.getElementById('location-name').value = parseResult.location_name;
    applyConfidenceStyle('location-name', parseResult.confidence.location_name);
  }
}

function applyConfidenceStyle(fieldId, confidence) {
  const field = document.getElementById(fieldId);
  if (confidence >= 0.80) {
    field.classList.add('field-high-confidence');  // Green border
  } else if (confidence >= 0.60) {
    field.classList.add('field-medium-confidence');  // Yellow border
  }
}
```

**CSS Additions** (`public/css/edit.css`):
```css
.field-high-confidence {
  border: 2px solid #10b981;  /* Green */
  background-color: #f0fdf4;  /* Light green tint */
}

.field-medium-confidence {
  border: 2px solid #f59e0b;  /* Yellow */
  background-color: #fffbeb;  /* Light yellow tint */
  animation: pulse-yellow 2s infinite;
}

@keyframes pulse-yellow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.4); }
  50% { box-shadow: 0 0 0 6px rgba(245, 158, 11, 0); }
}
```

---

### INT3: Database Integration
**Touchpoint**: `server/database.py` → No changes required

**Reason**: Parsing extracts metadata but does NOT create reminders. The edit form still calls existing `POST /api/reminders` endpoint with user-confirmed data.

**Flow**:
```
1. Parse extracts metadata → Populate form
2. User reviews/edits fields
3. User clicks "Save Reminder"
4. Existing API endpoint: POST /api/reminders (unchanged)
5. Database: create_reminder() (unchanged)
```

No database schema changes needed.

---

### INT4: API Client Integration
**Touchpoint**: `public/js/api.js`

**New Function**:
```javascript
/**
 * Parse reminder text to extract metadata
 * @param {string} text - Reminder text from transcription
 * @returns {Promise<Object>} - Parsed metadata (date, time, priority, etc.)
 */
async function parseReminderText(text) {
  const response = await fetch(`${API_BASE_URL}/api/voice/parse`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      text: text,
      current_datetime: new Date().toISOString()
    })
  });

  if (!response.ok) {
    // Fallback to manual entry on error
    console.warn('Parsing failed, falling back to manual entry');
    return null;
  }

  return await response.json();
}
```

**Error Handling**:
- 503 Service Unavailable → Show toast: "Parsing unavailable, please fill manually"
- 504 Gateway Timeout → Show toast: "Parsing timeout, please fill manually"
- Network error → Fallback to manual entry (no toast)

---

### INT5: Mode Selection Integration
**Touchpoint**: `server/config.py` (new file)

**Configuration Loading**:
```python
import os
import json

def load_parsing_config():
    """Load LLM parsing configuration from secrets.json"""
    secrets_path = os.path.join(os.path.dirname(__file__), "..", "secrets.json")

    with open(secrets_path, 'r') as f:
        secrets = json.load(f)

    return {
        "mode": secrets.get("parsing_mode", "auto"),  # auto, local, cloud, manual
        "local_url": secrets.get("local_llm_url", "http://127.0.0.1:1234/v1/chat/completions"),
        "cloudflare_account_id": secrets.get("cloudflare_account_id"),
        "cloudflare_api_token": secrets.get("cloudflare_api_token")
    }
```

**Mode Selection Logic**:
```python
def get_parsing_mode(config):
    """Determine which parsing mode to use"""
    if config["mode"] == "manual":
        return "manual"

    if config["mode"] == "local" or config["mode"] == "auto":
        # Check if local LM Studio is reachable
        if is_local_llm_available(config["local_url"]):
            return "local"

    if config["mode"] == "cloud" or config["mode"] == "auto":
        # Check if Cloudflare credentials present
        if config["cloudflare_account_id"] and config["cloudflare_api_token"]:
            return "cloud"

    # Final fallback
    return "manual"
```

---

## 7. Out of Scope (Future Enhancements)

The following features are explicitly OUT OF SCOPE for Phase 8.1:

### Future Phase 8.2: Advanced Parsing
- Multi-reminder splitting: "Buy milk and call mom" → 2 reminders
- Contextual understanding: "Same time as last week" (requires history lookup)
- Smart defaults: "Buy groceries" → auto-set location to nearest supermarket
- Sentiment analysis: Detect stress/urgency from tone (requires audio analysis)

### Future Phase 8.3: Continuous Learning
- User correction feedback: Learn from manual edits to improve accuracy
- Personalized prompts: Adapt to user's language patterns over time
- Custom categories: Learn user's preferred categories from manual entries

### Future Phase 9: Multi-Language Support
- Support languages beyond English (Spanish, French, German, etc.)
- Language detection from voice input
- Localized date/time parsing (regional formats)

### Future Phase 10: Voice Commands
- "Delete this reminder" → Delete instead of create
- "Mark as completed" → Update status
- "Show me all urgent reminders" → Query and read results

---

## 8. System Prompt Design

### System Prompt (LLM Instructions)
```
You are a reminder parsing assistant. Extract metadata from natural language reminder text.

Today's date: {current_date}
Current time: {current_time}

Extract the following fields:
1. text: Cleaned reminder text (remove date/time/priority phrases)
2. due_date: ISO 8601 date (YYYY-MM-DD) or null
3. due_time: ISO 8601 time (HH:MM:SS) or null
4. time_required: true if time is specific, false if flexible
5. priority: "urgent", "important", "chill", "someday", or "waiting"
6. category: One of [Calls, Shopping, Work, Personal, Health, Finance, Errands, Home] or null
7. location_name: Location name or null
8. confidence: Confidence score (0.0-1.0) for each field

Rules:
- Relative dates: "tomorrow" = {tomorrow_date}, "next Friday" = {next_friday_date}
- Times: "3pm" = "15:00:00", "morning" = "09:00:00" (time_required=false)
- Priorities: Default to "chill" if not mentioned
- Categories: Infer from action verbs (call→Calls, buy→Shopping, etc.)
- Text cleaning: Remove all date/time/priority/location phrases
- Confidence: High (>0.8) for exact matches, Medium (0.6-0.8) for inferences, Low (<0.6) for guesses

Respond ONLY with valid JSON matching this schema:
{
  "text": "string",
  "due_date": "YYYY-MM-DD or null",
  "due_time": "HH:MM:SS or null",
  "time_required": boolean,
  "priority": "urgent|important|chill|someday|waiting",
  "category": "string or null",
  "location_name": "string or null",
  "confidence": {
    "overall": float,
    "due_date": float,
    "due_time": float,
    "priority": float,
    "category": float,
    "location_name": float
  }
}

Example:
User: "Call mom tomorrow at 3pm, this is urgent"
Response:
{
  "text": "Call mom",
  "due_date": "{tomorrow_date}",
  "due_time": "15:00:00",
  "time_required": true,
  "priority": "urgent",
  "category": "Calls",
  "location_name": null,
  "confidence": {
    "overall": 0.95,
    "due_date": 0.98,
    "due_time": 0.95,
    "priority": 0.90,
    "category": 0.85,
    "location_name": 0.0
  }
}
```

**Prompt Variables** (injected at runtime):
- `{current_date}`: Current date in YYYY-MM-DD format
- `{current_time}`: Current time in HH:MM:SS format
- `{tomorrow_date}`: Tomorrow's date in YYYY-MM-DD format
- `{next_friday_date}`: Next Friday's date in YYYY-MM-DD format

**Prompt Tuning Strategy**:
1. Start with baseline prompt (above)
2. Collect 20+ test cases with expected outputs
3. Measure accuracy per field type
4. Adjust prompt based on failure patterns
5. Iterate until accuracy thresholds met (SC1-SC7)

---

## 9. Testing Requirements

### Test Suite Structure
```
server/tests/
├── test_parsing_dates.py       # 20+ date parsing tests
├── test_parsing_times.py       # 20+ time parsing tests
├── test_parsing_priorities.py  # 15+ priority tests
├── test_parsing_locations.py   # 15+ location tests
├── test_parsing_categories.py  # 15+ category tests
├── test_parsing_integration.py # 10+ end-to-end tests
└── test_parsing_edge_cases.py  # 20+ edge case tests
```

### Test Case Examples

**Date Parsing Tests**:
```python
@pytest.mark.parametrize("input_text,expected_date", [
    ("tomorrow", "2025-11-05"),
    ("next Friday", "2025-11-08"),
    ("in 3 days", "2025-11-07"),
    ("December 25", "2025-12-25"),
    ("12/25", "2025-12-25"),
    ("this weekend", "2025-11-09"),  # Next Saturday
    ("tonight", "2025-11-04"),  # Today with evening time
])
def test_date_parsing(input_text, expected_date):
    result = parse_reminder_text(input_text, current_date="2025-11-04")
    assert result["due_date"] == expected_date
    assert result["confidence"]["due_date"] > 0.80
```

**Time Parsing Tests**:
```python
@pytest.mark.parametrize("input_text,expected_time,time_required", [
    ("at 3pm", "15:00:00", True),
    ("3:30pm", "15:30:00", True),
    ("noon", "12:00:00", True),
    ("morning", "09:00:00", False),
    ("evening", "18:00:00", False),
    ("tonight", "20:00:00", False),
])
def test_time_parsing(input_text, expected_time, time_required):
    result = parse_reminder_text(f"Call mom {input_text}")
    assert result["due_time"] == expected_time
    assert result["time_required"] == time_required
```

**Integration Test**:
```python
def test_full_parsing_flow():
    """Test complete voice → transcribe → parse → auto-fill flow"""
    # 1. Simulate voice transcription
    transcription = "Call mom tomorrow at 3pm, this is urgent"

    # 2. Parse transcription
    result = parse_reminder_text(transcription, current_date="2025-11-04")

    # 3. Verify all fields
    assert result["text"] == "Call mom"
    assert result["due_date"] == "2025-11-05"
    assert result["due_time"] == "15:00:00"
    assert result["time_required"] == True
    assert result["priority"] == "urgent"
    assert result["category"] == "Calls"
    assert result["confidence"]["overall"] > 0.85
```

### Manual Testing Checklist
```
User Testing (20+ scenarios):
[ ] "Buy milk tomorrow" → due_date = tomorrow, category = Shopping
[ ] "Call dentist at 2pm" → due_time = 14:00:00, time_required = true
[ ] "Important: file taxes by April 15" → priority = important, due_date = 2025-04-15
[ ] "Pick up dry cleaning at Main Street Cleaners" → location_name = Main Street Cleaners
[ ] "Urgent: finish report asap" → priority = urgent, time_required = false
[ ] "Buy groceries at Kroger when I get time" → location = Kroger, priority = chill
[ ] "Call about tomorrow's meeting" → text = "Call about tomorrow's meeting" (keep "tomorrow")
[ ] "Do something later" → due_date = null, due_time = null (low confidence)
[ ] "Maybe buy new laptop someday" → priority = someday, category = null
[ ] "Waiting for email from Sarah" → priority = waiting
[ ] [10 more varied scenarios...]
```

---

## 10. Documentation Requirements

Phase 8.1 documentation deliverables:

1. **This Document**: `docs/phase8.1_requirements.md` (you are here)
2. **Technical Research**: `docs/phase8.1_technical_research.md` (Cloudflare Workers AI patterns, LM Studio API, prompt engineering)
3. **Architecture Plan**: `docs/phase8.1_architecture.md` (dual-mode design, component diagrams, data flow)
4. **Edge Case Analysis**: `docs/phase8.1_edge_cases.md` (ambiguity handling, error scenarios, fallback strategies)
5. **Completion Report**: `docs/phase8.1_completion.md` (implementation summary, test results, success criteria checklist)

---

## 11. Success Metrics

**Quantitative Metrics**:
- Date parsing accuracy: >85% (target: 90%)
- Time parsing accuracy: >80% (target: 85%)
- Priority accuracy: >75% (target: 80%)
- Location extraction: >70% (target: 75%)
- Category inference: >65% (target: 70%)
- Overall parsing success: >75% (target: 80%)
- Local mode latency: <3s (target: <2s)
- Cloud mode latency: <5s (target: <4s)

**Qualitative Metrics**:
- User satisfaction: "Saves time vs manual entry" (user feedback)
- Editing frequency: <20% of auto-filled fields require edits (goal)
- Fallback rate: <10% of voice inputs require full manual entry (goal)

**Acceptance Criteria**:
Phase 8.1 is ACCEPTED when:
- All 12 success criteria (SC1-SC12) are met
- 100+ pytest tests pass (covering all parsing logic)
- Manual testing with 20+ varied inputs shows >75% accuracy
- User confirms: "Voice input feels natural and saves time"

---

## 12. Related Documentation

- **Phase 8 Completion**: `docs/phase8_completion.md` (Voice transcription foundation)
- **Cloudflare Workers AI Guide**: `docs/cloudflare_workers_ai_guide.md` (Cloud mode implementation)
- **LM Studio Setup**: (Future: `docs/lm_studio_setup.md`)
- **Prompt Engineering**: (Future: `docs/prompt_tuning_guide.md`)

---

**End of Requirements Document**

*Phase 8.1 Requirements Analysis*
*Created: November 4, 2025*
*Subagent: Requirements Analysis*
*Status: Ready for Technical Research Phase*
