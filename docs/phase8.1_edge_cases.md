# Phase 8.1: NLP Parsing Edge Case Analysis

**Subagent**: Edge Case Analysis
**Phase**: Research
**Date**: 2025-11-04
**Status**: Complete

---

## Executive Summary

This document identifies and analyzes edge cases for the NLP-based reminder parsing system (Phase 8.1). It covers ambiguous date/time inputs, priority inference, library comparisons, timezone handling, and graceful degradation strategies. The analysis is based on current best practices from 2025 research and real-world NLP parsing pitfalls.

**Key Findings:**
- **Recommended Library**: `dateparser` for natural language date parsing
- **Fallback Strategy**: Progressive degradation with explicit user clarification
- **Critical Edge Cases**: 27+ identified scenarios requiring special handling
- **Validation Approach**: Multi-layer validation with clear error messages
- **Test Coverage**: Minimum 85% coverage with edge case focus

---

## Table of Contents

1. [Date/Time Parsing Edge Cases](#datetime-parsing-edge-cases)
2. [Date Parsing Library Comparison](#date-parsing-library-comparison)
3. [Priority and Category Inference Rules](#priority-and-category-inference-rules)
4. [Contradictory Input Handling](#contradictory-input-handling)
5. [Timezone Handling Strategy](#timezone-handling-strategy)
6. [Graceful Degradation Paths](#graceful-degradation-paths)
7. [Validation Requirements](#validation-requirements)
8. [Common NLP Parsing Pitfalls](#common-nlp-parsing-pitfalls)
9. [Test Case Recommendations](#test-case-recommendations)
10. [Implementation Checklist](#implementation-checklist)

---

## Date/Time Parsing Edge Cases

### Category 1: Relative Date Ambiguity (7 cases)

#### 1.1 "Next Tuesday" Ambiguity
- **Input**: "Remind me next Tuesday"
- **Issue**: Does "next Tuesday" mean:
  - The upcoming Tuesday (3 days away)?
  - The Tuesday after the upcoming one (10 days away)?
- **Resolution**: Use `:CONTEXT :FUTURE` and define "next" as the first occurrence after current week
- **Test Case**: Run on Monday, Wednesday, and Sunday to verify consistency

#### 1.2 "Tomorrow" at Edge of Day
- **Input**: "Remind me tomorrow" at 11:58 PM
- **Issue**: System processes at 12:01 AM - is it still "tomorrow"?
- **Resolution**: Parse relative to user's intent timestamp, not processing timestamp
- **Test Case**: Submit at 23:59:59 and verify date calculation

#### 1.3 "In 2 Weeks" vs "2 Weeks From Now"
- **Input**: "In 2 weeks" vs "2 weeks from now"
- **Issue**: Both should be identical, but NLP might interpret differently
- **Resolution**: Normalize both to same calculation: `current_date + timedelta(weeks=2)`
- **Test Case**: Compare outputs for semantic equivalence

#### 1.4 "This Weekend" Ambiguity
- **Input**: "Remind me this weekend"
- **Issue**: Saturday? Sunday? Both? What time?
- **Resolution**: Default to Saturday 10:00 AM, allow user to clarify
- **Test Case**: Run on Wednesday, Friday, and Saturday to test interpretation

#### 1.5 "End of Month" Boundary
- **Input**: "Remind me at the end of the month"
- **Issue**: Last day? Last business day? Specific date?
- **Resolution**: Default to last calendar day at 9:00 AM
- **Test Case**: Test in February (leap year), April (30 days), May (31 days)

#### 1.6 "Next Month" with Day Overflow
- **Input**: "Remind me next month on the 31st"
- **Issue**: Current date is January 31st, next month is February (28/29 days)
- **Resolution**: Clamp to last valid day of month (Feb 28/29)
- **Test Case**: Test from Jan 31, Mar 31, May 31

#### 1.7 "In a Couple Days"
- **Input**: "In a couple days"
- **Issue**: 2 days? 3 days? Fuzzy quantifier
- **Resolution**: Default to 2 days, document in system behavior
- **Test Case**: Verify consistent interpretation

### Category 2: Time Format Ambiguity (6 cases)

#### 2.1 12-Hour Time Without Meridiem
- **Input**: "Remind me at 5:00"
- **Issue**: 5:00 AM or 5:00 PM?
- **Resolution**: Use context heuristic:
  - If current time is AM and input time > current time in AM range → AM
  - Otherwise → PM
  - For 5:00: default to PM (most common usage)
- **Test Case**: Test at 3 AM, 3 PM, 6 PM

#### 2.2 Midnight vs Noon Confusion
- **Input**: "Remind me at 12:00 PM" (noon) vs "12:00 AM" (midnight)
- **Issue**: Common user confusion about 12-hour clock
- **Resolution**: Validate and confirm with user; offer 24-hour alternative
- **Test Case**: Parse "12:00 PM", "12:00 AM", "noon", "midnight"

#### 2.3 24-Hour Time in Natural Language
- **Input**: "Remind me at 17:30"
- **Issue**: User switches to 24-hour format mid-sentence
- **Resolution**: Support both 12-hour and 24-hour formats
- **Test Case**: "5:30 PM", "17:30", "1730 hours"

#### 2.4 "Morning", "Afternoon", "Evening" Ranges
- **Input**: "Remind me tomorrow morning"
- **Issue**: What specific time does "morning" mean?
- **Resolution**: Define time ranges:
  - Morning: 9:00 AM
  - Afternoon: 2:00 PM
  - Evening: 6:00 PM
  - Night: 9:00 PM
- **Test Case**: Verify all four time-of-day keywords

#### 2.5 "In 90 Minutes" vs "1.5 Hours"
- **Input**: "90 minutes" vs "1.5 hours" vs "hour and a half"
- **Issue**: Multiple representations of same duration
- **Resolution**: Normalize all to minutes internally, then convert
- **Test Case**: Compare all three formats for equivalence

#### 2.6 "Half Past" and "Quarter To" Formats
- **Input**: "half past 3", "quarter to 5"
- **Issue**: Colloquial time expressions
- **Resolution**: Pattern matching for common phrases:
  - "half past X" → X:30
  - "quarter past X" → X:15
  - "quarter to X" → (X-1):45
- **Test Case**: All three formats with multiple hours

### Category 3: Date Format Ambiguity (5 cases)

#### 3.1 MM/DD vs DD/MM Confusion
- **Input**: "01/03/2025"
- **Issue**: January 3rd or March 1st?
- **Resolution**: Use locale detection from browser/system, default to US format (MM/DD/YYYY)
- **Test Case**: Parse "13/03/2025" (unambiguous DD/MM), "03/13/2025" (unambiguous MM/DD)

#### 3.2 Two-Digit Year Ambiguity
- **Input**: "03/15/25"
- **Issue**: 1925, 2025, or 2125?
- **Resolution**: Use sliding window: 00-49 → 2000-2049, 50-99 → 1950-1999
- **Test Case**: Parse "03/15/25", "03/15/49", "03/15/50"

#### 3.3 Month Name Abbreviations
- **Input**: "Mar 15", "March 15", "3/15"
- **Issue**: Multiple valid formats for same date
- **Resolution**: Support all common formats, normalize internally
- **Test Case**: Test abbreviated (Jan, Feb), full (January, February), numeric (1, 2)

#### 3.4 Ordinal Dates
- **Input**: "March 3rd" vs "March 3" vs "3 March" vs "the 3rd of March"
- **Issue**: Multiple syntactic variations
- **Resolution**: Regex patterns for ordinals (1st, 2nd, 3rd, 4th, etc.)
- **Test Case**: All ordinal suffixes (1st-31st)

#### 3.5 "In YYYY-MM-DD Format" (ISO 8601)
- **Input**: "2025-11-04"
- **Issue**: Unambiguous but different format from conversational input
- **Resolution**: Always support ISO 8601 as primary format for programmatic input
- **Test Case**: Parse ISO format, validate ordering

### Category 4: Contextual Ambiguity (5 cases)

#### 4.1 "This Friday" on a Friday
- **Input**: "Remind me this Friday" (spoken on Friday)
- **Issue**: Today or next Friday?
- **Resolution**: "this Friday" on Friday → today; "next Friday" → in 7 days
- **Test Case**: Run on each day of week, verify interpretation

#### 4.2 "Later Today" at 11:30 PM
- **Input**: "Remind me later today" at 11:30 PM
- **Issue**: Only 30 minutes left in day
- **Resolution**: If less than 1 hour remaining, suggest "tomorrow morning" instead
- **Test Case**: Test at 23:00, 23:30, 23:59

#### 4.3 Past Date References
- **Input**: "Remind me January 3rd" (spoken on January 5th)
- **Issue**: Past date - user probably means next year
- **Resolution**: If date is in past, assume next occurrence (next year)
- **Test Case**: Parse past dates, verify year increment

#### 4.4 "Week" vs "Workweek"
- **Input**: "In a week" vs "in a business week"
- **Issue**: 7 calendar days vs 5 business days
- **Resolution**: Default to calendar week (7 days); support "business week" keyword for 5 days
- **Test Case**: Calculate both, verify weekend handling

#### 4.5 Holidays and Special Dates
- **Input**: "Remind me on Christmas", "Black Friday", "tax day"
- **Issue**: Cultural/regional holiday references
- **Resolution**: Phase 8.1 MVP: Don't parse holidays, ask for explicit date
  - Future enhancement: Holiday lookup table
- **Test Case**: Return "unrecognized date" for holiday names

### Category 5: Duration vs Point-in-Time (4 cases)

#### 5.1 "In 3 Days" vs "For 3 Days"
- **Input**: "In 3 days" (point-in-time) vs "for 3 days" (duration)
- **Issue**: Different semantic meanings
- **Resolution**:
  - "in X" → trigger at future point
  - "for X" → duration (currently not supported, requires recurring reminders)
- **Test Case**: Parse both, validate different interpretations

#### 5.2 "Every Monday" (Recurring)
- **Input**: "Remind me every Monday"
- **Issue**: Recurring reminder (Phase 8.1 doesn't support this)
- **Resolution**: Detect "every", "each", "weekly" keywords and return error: "Recurring reminders not yet supported"
- **Test Case**: Validate rejection of recurring patterns

#### 5.3 "Until Friday" (End Condition)
- **Input**: "Remind me until Friday"
- **Issue**: Requires end date (not supported in Phase 8.1)
- **Resolution**: Parse as single reminder on Friday, note limitation
- **Test Case**: Convert end condition to single point-in-time

#### 5.4 "Between 2-4 PM" (Time Range)
- **Input**: "Remind me between 2-4 PM"
- **Issue**: Flexible time window (not rigid time)
- **Resolution**: Pick midpoint (3:00 PM), document as approximation
- **Test Case**: Verify midpoint calculation for various ranges

---

## Date Parsing Library Comparison

Based on 2025 research, here's a comprehensive comparison of Python date parsing libraries:

### Comparison Table

| Feature | **dateparser** | **arrow** | **pendulum** | **python-dateutil** |
|---------|---------------|-----------|--------------|---------------------|
| **Natural Language** | ✅ Excellent | ⚠️ Limited | ⚠️ Limited | ⚠️ Limited |
| **Multi-Language** | ✅ Yes (40+ languages) | ❌ No | ❌ No | ❌ No |
| **Timezone Handling** | ✅ Good | ⚠️ Unpredictable | ✅ Excellent (DST) | ✅ Good |
| **Relative Dates** | ✅ Excellent | ✅ Good | ✅ Good | ✅ Good |
| **Ambiguity Settings** | ✅ Yes (context, endian) | ❌ No | ❌ No | ⚠️ Partial |
| **Performance** | ⚠️ Moderate | ❌ Slow (16x slower) | ❌ Slow (19x slower) | ✅ Fast |
| **Active Maintenance** | ✅ Active (2025) | ⚠️ Declining | ✅ Active | ✅ Active |
| **ISO 8601 Support** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Fuzzy Parsing** | ✅ Yes | ❌ No | ❌ No | ⚠️ Limited |
| **Calendar Support** | ✅ Jalali, Hijri | ❌ Gregorian only | ❌ Gregorian only | ❌ Gregorian only |
| **API Simplicity** | ✅ Simple | ✅ Simple | ✅ Simple | ⚠️ Complex |
| **LLM Integration** | ✅ Good for validation | N/A | N/A | N/A |

### Detailed Analysis

#### **dateparser** (RECOMMENDED)
**Strengths:**
- Designed specifically for natural language date parsing
- Handles fuzzy inputs: "In about 2 weeks", "sometime next month"
- Multi-language support (not needed for MVP, but nice for future)
- Configurable ambiguity resolution (FUTURE context, date order)
- ISO 8601 support as fallback

**Weaknesses:**
- Slower than python-dateutil (acceptable tradeoff for NL parsing)
- Can produce unexpected results without proper settings configuration

**Configuration for ADHD Reminder System:**
```python
from dateparser import parse
from dateparser.conf import Settings

settings = Settings(
    PREFER_DATES_FROM='future',  # Default to future dates
    PREFER_DAY_OF_MONTH='current',  # If day mentioned, prefer current month
    TIMEZONE='America/Los_Angeles',  # User's local timezone
    RETURN_AS_TIMEZONE_AWARE=True,  # Always timezone-aware
    DATE_ORDER='MDY',  # US format (configurable per user)
    STRICT_PARSING=False,  # Allow fuzzy parsing
)

parsed_date = parse("remind me in 2 weeks", settings=settings)
```

**Why Best for Phase 8.1:**
1. Handles the exact use case: natural language → datetime
2. Configurable ambiguity resolution aligns with our edge case needs
3. Good fallback parsing when LLM output is ambiguous
4. Active maintenance with 2025 updates

#### **arrow**
**Use Case:** Human-friendly datetime manipulation after parsing
**Verdict:** Good for formatting output, not for parsing NL input

#### **pendulum**
**Use Case:** Timezone-heavy applications, DST-critical systems
**Verdict:** Excellent for tz handling, but overkill for Phase 8.1 MVP

#### **python-dateutil**
**Use Case:** Fast parsing of structured datetime strings
**Verdict:** Great for ISO 8601 and common formats, poor for NL parsing

### Final Recommendation

**Primary Library:** `dateparser`
**Secondary (validation):** `python-dateutil` for structured formats
**Fallback:** If dateparser fails, attempt python-dateutil.parser.parse() with fuzzy=True

**Hybrid Approach:**
```python
def parse_datetime_hybrid(text: str, settings: Settings) -> Optional[datetime]:
    """
    Hybrid parsing: dateparser (primary), python-dateutil (fallback)
    """
    # Try dateparser first (handles NL)
    result = dateparser.parse(text, settings=settings)
    if result:
        return result

    # Fallback to python-dateutil (handles structured formats)
    try:
        result = dateutil.parser.parse(text, fuzzy=True)
        return result
    except (ValueError, ParserError):
        return None
```

---

## Priority and Category Inference Rules

### Priority Inference from Keywords

LLM should extract priority based on these keyword patterns:

#### **URGENT Priority**
**Trigger Words/Phrases:**
- "urgent", "ASAP", "emergency", "critical", "immediately"
- "as soon as possible", "right now", "today"
- "before [deadline]", "must do", "have to", "need to"

**Examples:**
- "URGENT: Call dentist about broken tooth" → URGENT
- "Need to submit report ASAP" → URGENT
- "Emergency: Pick up medication before 6 PM" → URGENT

#### **IMPORTANT Priority**
**Trigger Words/Phrases:**
- "important", "priority", "don't forget", "remember to"
- "make sure", "be sure to", "should", "supposed to"
- Explicit time mentions (3 PM, Tuesday at 2, etc.)

**Examples:**
- "Important: Email client proposal by Friday" → IMPORTANT
- "Don't forget to call mom on her birthday" → IMPORTANT
- "Make sure to take medication at 3 PM" → IMPORTANT

#### **CHILL Priority**
**Trigger Words/Phrases:**
- "chill", "when you can", "sometime", "eventually"
- "if you have time", "no rush", "when convenient"
- "maybe", "consider", "think about"
- No urgency indicators + vague timing

**Examples:**
- "Chill reminder to water plants sometime this week" → CHILL
- "When you have time, organize closet" → CHILL
- "Maybe clean out garage this month" → CHILL

#### **Default Fallback**
If no priority keywords detected:
- **Has specific date/time** → IMPORTANT
- **Vague timing** → CHILL

**Examples:**
- "Buy milk" → CHILL (no time, no urgency)
- "Buy milk tomorrow" → IMPORTANT (specific time)

### Category Inference Rules

Phase 8.1 MVP doesn't have categories, but LLM should classify for future use:

#### Potential Categories (Future Enhancement)
1. **Health** - medication, appointments, exercise
2. **Errands** - shopping, pick up, drop off
3. **Work** - tasks, meetings, deadlines
4. **Personal** - birthdays, calls, messages
5. **Chores** - cleaning, maintenance, repairs
6. **Finance** - bills, payments, budgeting
7. **Other** - default catch-all

**MVP Behavior:** Store in "Other" category, ignore for Phase 8.1

---

## Contradictory Input Handling

When user input contains contradictory information, the system must resolve conflicts predictably.

### Conflict Type 1: Priority vs Timing Mismatch

#### Case 1: "Urgent but someday"
- **Input**: "Urgent: Clean out garage someday"
- **Conflict**: Urgent priority + vague timing
- **Resolution**: Priority wins → set to URGENT, but flag as "needs specific date"
- **Action**: Prompt user: "You marked this as urgent. When should this be done?"

#### Case 2: "Chill but today"
- **Input**: "Chill reminder to call dentist today at 3 PM"
- **Conflict**: Chill priority + specific immediate timing
- **Resolution**: Timing wins → upgrade to IMPORTANT (specific time overrides chill)
- **Rationale**: Specific time implies user wants to be reminded at that time

#### Case 3: "Important chill task"
- **Input**: "Important chill task: organize files"
- **Conflict**: Explicit priority contradiction
- **Resolution**: First mentioned wins → IMPORTANT
- **Alternative**: Ask user to clarify: "Is this important or chill?"

### Conflict Type 2: Multiple Time References

#### Case 4: "Tomorrow at 3 PM next week"
- **Input**: "Remind me tomorrow at 3 PM next week"
- **Conflict**: Two different time frames
- **Resolution**: More specific wins → "next week" is more specific than "tomorrow"
- **Parsed**: Next week, same day of week, 3 PM

#### Case 5: "Monday on the 15th" (when 15th isn't Monday)
- **Input**: "Remind me Monday on the 15th" (15th is actually Wednesday)
- **Conflict**: Day of week vs day of month
- **Resolution**: Day of month wins (more specific)
- **Action**: Flag warning: "Note: March 15th is a Wednesday, not Monday"

### Conflict Type 3: Past vs Future Context

#### Case 6: "Yesterday at 5 PM"
- **Input**: "Remind me yesterday at 5 PM"
- **Conflict**: Past time reference for future reminder
- **Resolution**: Assume user meant "tomorrow at 5 PM", flag for confirmation
- **Action**: Return error: "Cannot create reminder for past date. Did you mean tomorrow?"

#### Case 7: "3 PM" at 4 PM (already passed today)
- **Input**: "Remind me at 3 PM" (current time is 4:15 PM)
- **Conflict**: Specified time has already passed today
- **Resolution**: Assume tomorrow at 3 PM
- **Action**: Confirm with user: "3 PM has passed. Setting reminder for tomorrow at 3 PM."

### Resolution Priority Hierarchy

When conflicts occur, resolve in this order:

1. **Explicit date/time** > Implicit date/time
2. **Specific** > Vague
3. **Earlier mention** > Later mention (in same priority tier)
4. **User clarification** > Automatic resolution (when confidence is low)

### Confidence Scoring for Contradictions

LLM should return confidence score for ambiguous parses:

```json
{
  "text": "Buy milk",
  "datetime": "2025-11-05T09:00:00-08:00",
  "priority": "chill",
  "confidence": 0.85,
  "flags": [],
  "needs_clarification": false
}
```

**Confidence Thresholds:**
- **≥ 0.9** - High confidence, proceed
- **0.7-0.89** - Medium confidence, proceed with logging
- **< 0.7** - Low confidence, ask user to clarify

**Examples of Low Confidence:**
- "urgent chill" (contradictory priority) → confidence: 0.6
- "tomorrow next week" (contradictory timing) → confidence: 0.5
- "maybe ASAP" (contradictory urgency) → confidence: 0.4

---

## Timezone Handling Strategy

Timezone handling is critical for date/time accuracy. Based on 2025 research, here's our strategy:

### Key Pitfalls to Avoid

#### ❌ Pitfall 1: `strptime()` Silently Discards Timezone
**Problem:** `datetime.strptime()` ignores timezone information in strings
**Solution:** Use `dateparser` or `python-dateutil` which preserve timezone

#### ❌ Pitfall 2: Naive Datetime Objects
**Problem:** Naive datetime (no timezone) causes ambiguity
**Solution:** ALWAYS use timezone-aware datetime objects

#### ❌ Pitfall 3: Timezone Abbreviation Ambiguity
**Problem:** "CST" could be Central, China, or Cuba Standard Time
**Solution:** Use IANA timezone names (e.g., "America/Chicago")

#### ❌ Pitfall 4: pytz Localization Issues
**Problem:** pytz requires `.localize()`, not `.replace()`
**Solution:** Use `zoneinfo` (Python 3.9+) which avoids this pitfall

### Phase 8.1 Timezone Strategy

#### User Timezone Detection

**Source Priority:**
1. **User profile setting** (if saved)
2. **Browser/system timezone** (from client)
3. **IP-based geolocation** (fallback)
4. **UTC** (absolute fallback)

**Implementation:**
```python
from zoneinfo import ZoneInfo
from datetime import datetime

def get_user_timezone(user_id: str) -> ZoneInfo:
    """
    Get user's timezone with fallback chain
    """
    # Check user profile
    tz_str = db_get_user_timezone(user_id)
    if tz_str:
        return ZoneInfo(tz_str)

    # Check browser/client
    client_tz = request.headers.get('X-Timezone')
    if client_tz:
        return ZoneInfo(client_tz)

    # Default to UTC
    return ZoneInfo('UTC')
```

#### Storing Datetime in Database

**RULE:** Always store in UTC, display in user's local timezone

```python
# Store (always UTC)
utc_time = datetime.now(ZoneInfo('UTC'))
db.store_reminder(utc_time.isoformat())

# Retrieve and display (convert to user tz)
utc_time = datetime.fromisoformat(db_value)
user_tz = get_user_timezone(user_id)
local_time = utc_time.astimezone(user_tz)
```

#### Daylight Saving Time (DST) Handling

**Problem:** DST transitions can break recurring reminders
**Solution:** Use `zoneinfo` which automatically handles DST

**Example:**
```python
from zoneinfo import ZoneInfo
from datetime import datetime

# DST transition: March 10, 2025 at 2:00 AM → 3:00 AM (America/Los_Angeles)
tz = ZoneInfo('America/Los_Angeles')

# Before DST (PST = UTC-8)
before = datetime(2025, 3, 9, 14, 0, tzinfo=tz)
print(before.isoformat())  # 2025-03-09T14:00:00-08:00

# After DST (PDT = UTC-7)
after = datetime(2025, 3, 11, 14, 0, tzinfo=tz)
print(after.isoformat())  # 2025-03-11T14:00:00-07:00
```

#### Ambiguous Time Handling

**Problem:** "1:30 AM" during DST "fall back" occurs twice
**Solution:** Always prefer first occurrence (before DST ends), log ambiguity

```python
from zoneinfo import ZoneInfo
from datetime import datetime

# DST ends: November 3, 2025 at 2:00 AM → 1:00 AM
tz = ZoneInfo('America/Los_Angeles')

# This time is ambiguous (happens twice)
try:
    ambiguous = datetime(2025, 11, 3, 1, 30, tzinfo=tz)
except Exception as e:
    # Handle ambiguity: default to first occurrence (PDT)
    ambiguous = datetime(2025, 11, 3, 1, 30, tzinfo=tz, fold=0)
```

### Frontend Timezone Display

**Show both UTC and local:**
```
Reminder set for:
  November 5, 2025 at 3:00 PM (PST)
  November 5, 2025 at 23:00 UTC
```

---

## Graceful Degradation Paths

When NLP parsing fails or is ambiguous, the system must degrade gracefully rather than fail hard.

### Degradation Levels

#### Level 1: Full Success (90-100% confidence)
- All fields parsed correctly
- No ambiguity detected
- Proceed without user confirmation

**Example:**
```
Input: "Remind me to buy milk tomorrow at 3 PM"
Output: ✅ Parsed successfully
  - Text: "Buy milk"
  - Date: 2025-11-05 15:00:00 PST
  - Priority: IMPORTANT
  - Confidence: 0.95
```

#### Level 2: Partial Parse (70-89% confidence)
- Some fields parsed, others defaulted
- Minor ambiguity resolved with defaults
- Show confirmation to user

**Example:**
```
Input: "Remind me to buy milk tomorrow"
Output: ⚠️ Parsed with defaults
  - Text: "Buy milk"
  - Date: 2025-11-05 09:00:00 PST (defaulted to 9 AM)
  - Priority: IMPORTANT
  - Confidence: 0.75

Confirmation: "No time specified, set to 9:00 AM. Is this correct?"
```

#### Level 3: Ambiguous Parse (50-69% confidence)
- Multiple interpretations possible
- Require user to choose or clarify

**Example:**
```
Input: "Remind me next Tuesday"
Output: ❓ Ambiguous date

Options:
  A) November 5, 2025 (upcoming Tuesday)
  B) November 12, 2025 (next week Tuesday)

Please select: [A] [B]
```

#### Level 4: Failed Parse (< 50% confidence)
- Cannot reliably parse datetime
- Fall back to manual entry

**Example:**
```
Input: "Remind me to call mom sometime soonish"
Output: ❌ Could not parse date/time

Text parsed: "Call mom"

Please specify:
  📅 Date: [Date Picker]
  🕐 Time: [Time Picker]
  ⭐ Priority: [Chill] [Important] [Urgent]
```

### Fallback Chain

```
LLM NLP Parse
    ↓ (fails/low confidence)
dateparser Library
    ↓ (fails)
python-dateutil (structured)
    ↓ (fails)
Manual Date Picker UI
```

### Error Message Guidelines

**DO:**
- ✅ Explain what couldn't be parsed
- ✅ Show what WAS parsed successfully
- ✅ Offer specific next steps
- ✅ Use friendly, non-technical language

**DON'T:**
- ❌ Show raw error messages
- ❌ Blame the user ("Invalid input")
- ❌ Provide generic "try again" messages
- ❌ Hide what was successfully parsed

**Good Example:**
```
We understood: "Buy milk"
But we're not sure when. Did you mean:
- Today (November 4)
- Tomorrow (November 5)
- Or another day? [Date Picker]
```

**Bad Example:**
```
Error: datetime parsing failed. Code 422. Please try again.
```

### Logging for Improvement

Every degradation should be logged for model improvement:

```json
{
  "timestamp": "2025-11-04T10:30:00Z",
  "user_input": "Remind me to buy milk tomorrow",
  "llm_output": "{ datetime: '2025-11-05T09:00:00', confidence: 0.75 }",
  "degradation_level": 2,
  "user_action": "confirmed",
  "final_datetime": "2025-11-05T15:00:00Z"
}
```

Use this data to:
1. Improve LLM prompt engineering
2. Identify common failure patterns
3. Retrain/fine-tune date parsing model
4. Update default assumptions

---

## Validation Requirements

Multi-layer validation ensures data integrity from user input to database storage.

### Layer 1: Client-Side Validation (JavaScript)

**Validate before sending to server:**

```javascript
function validateReminderInput(input) {
  const errors = [];

  // Text validation
  if (!input.text || input.text.trim().length === 0) {
    errors.push("Reminder text cannot be empty");
  }
  if (input.text.length > 500) {
    errors.push("Reminder text too long (max 500 characters)");
  }

  // Date validation
  const reminderDate = new Date(input.datetime);
  const now = new Date();

  if (isNaN(reminderDate.getTime())) {
    errors.push("Invalid date/time format");
  }
  if (reminderDate < now) {
    errors.push("Reminder cannot be set for past date");
  }
  if (reminderDate > new Date(now.getTime() + 10 * 365 * 24 * 60 * 60 * 1000)) {
    errors.push("Reminder cannot be more than 10 years in future");
  }

  // Priority validation
  const validPriorities = ['chill', 'important', 'urgent'];
  if (!validPriorities.includes(input.priority)) {
    errors.push("Invalid priority value");
  }

  return {
    valid: errors.length === 0,
    errors: errors
  };
}
```

### Layer 2: API Validation (FastAPI/Pydantic)

**Server-side validation with Pydantic models:**

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from typing import Literal

class ReminderCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    datetime: datetime
    priority: Literal['chill', 'important', 'urgent']
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @validator('text')
    def text_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Reminder text cannot be empty')
        return v.strip()

    @validator('datetime')
    def datetime_not_past(cls, v):
        if v < datetime.now(v.tzinfo):
            raise ValueError('Cannot create reminder for past date')
        max_future = datetime.now(v.tzinfo) + timedelta(days=3650)  # 10 years
        if v > max_future:
            raise ValueError('Reminder cannot be more than 10 years in future')
        return v

    @validator('datetime')
    def datetime_timezone_aware(cls, v):
        if v.tzinfo is None:
            raise ValueError('Datetime must be timezone-aware')
        return v
```

### Layer 3: LLM Output Validation

**Validate structured output from LLM:**

```python
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo

def validate_llm_output(llm_output: dict) -> tuple[bool, list[str]]:
    """
    Validate LLM's parsed output
    Returns: (is_valid, errors)
    """
    errors = []

    # Required fields
    required = ['text', 'datetime', 'priority']
    for field in required:
        if field not in llm_output:
            errors.append(f"Missing required field: {field}")

    # Text validation
    if 'text' in llm_output:
        text = llm_output['text']
        if not isinstance(text, str) or len(text.strip()) == 0:
            errors.append("Text must be non-empty string")
        if len(text) > 500:
            errors.append("Text exceeds maximum length")

    # Datetime validation
    if 'datetime' in llm_output:
        try:
            dt = datetime.fromisoformat(llm_output['datetime'])
            if dt.tzinfo is None:
                errors.append("Datetime must include timezone")
            if dt < datetime.now(dt.tzinfo):
                errors.append("Datetime is in the past")
        except (ValueError, TypeError):
            errors.append("Invalid datetime format")

    # Priority validation
    if 'priority' in llm_output:
        valid_priorities = ['chill', 'important', 'urgent']
        if llm_output['priority'] not in valid_priorities:
            errors.append(f"Invalid priority. Must be one of: {valid_priorities}")

    # Confidence validation (optional)
    if 'confidence' in llm_output:
        conf = llm_output['confidence']
        if not isinstance(conf, (int, float)) or conf < 0 or conf > 1:
            errors.append("Confidence must be float between 0 and 1")

    return (len(errors) == 0, errors)
```

### Layer 4: Database Constraints (SQLite)

**Database-level validation:**

```sql
CREATE TABLE reminders (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    text TEXT NOT NULL CHECK(length(text) > 0 AND length(text) <= 500),
    datetime TEXT NOT NULL,  -- ISO 8601 format
    priority TEXT NOT NULL CHECK(priority IN ('chill', 'important', 'urgent')),
    completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Index for date range queries
CREATE INDEX idx_reminders_datetime ON reminders(datetime);
```

### Validation Flow

```
User Input (voice/text)
    ↓
Client Validation (JavaScript) ← catches obvious errors fast
    ↓
LLM Parsing
    ↓
LLM Output Validation ← catches parsing errors
    ↓
API Validation (Pydantic) ← catches malformed requests
    ↓
Database Constraints ← final safety net
    ↓
Stored Reminder
```

---

## Common NLP Parsing Pitfalls

Based on 2025 research, here are the most common pitfalls and how to avoid them:

### Pitfall 1: Inconsistent Granularity
**Problem:** "Earlier this year" vs "January 15th at 3:00 PM"
**Impact:** System must handle both vague and precise inputs
**Solution:**
- Vague inputs → default to reasonable times (e.g., 9 AM)
- Track granularity level in metadata
- Flag low-precision parses for user review

### Pitfall 2: "Second" Ambiguity
**Problem:** "Remind me in a second" vs "Remind me on the second"
**Impact:** Confuses ordinal (2nd day) with time unit (1 second)
**Solution:**
- Context detection: "in a second" → time unit (interpret as "soon", default to 5 minutes)
- "on the second" → ordinal (2nd day of month)
- Tokenize first, then resolve

### Pitfall 3: Time Without Date
**Problem:** "Remind me at 5 PM" (no date specified)
**Impact:** Ambiguous whether today or tomorrow
**Solution:**
- If time has passed today → tomorrow
- If time hasn't passed → today
- Confirm with user for clarity

### Pitfall 4: Timezone Assumptions
**Problem:** Assuming user's timezone without confirmation
**Impact:** Wrong reminder time, especially for travelers
**Solution:**
- Always detect and store timezone explicitly
- Show timezone in confirmation: "3 PM PST"
- Allow timezone override in settings

### Pitfall 5: Month/Day Ambiguity
**Problem:** "01/03" could be Jan 3 or Mar 1
**Impact:** Wrong date interpretation
**Solution:**
- Detect user's locale (US=MDY, Europe=DMY)
- For ambiguous dates, ask for clarification
- Always accept ISO 8601 (YYYY-MM-DD) as unambiguous

### Pitfall 6: Past Date Assumptions
**Problem:** "January 15" spoken in December (is it next year or last month?)
**Impact:** Reminder set for past date
**Solution:**
- Default to FUTURE context (never past)
- If date is past, assume next occurrence (next year)
- Validate and reject true past dates

### Pitfall 7: Prefix/Postfix Modifiers
**Problem:** "Since Monday", "2 weeks ago", "Next Friday"
**Impact:** Misinterpreting direction (past vs future)
**Solution:**
- Pattern matching for temporal modifiers:
  - "ago", "back", "since" → past (reject for reminders)
  - "next", "in", "from now" → future (accept)
- Reject past-indicating modifiers explicitly

### Pitfall 8: Implied Context Loss
**Problem:** "Remind me then" (referring to earlier conversation)
**Impact:** No datetime reference in current input
**Solution:**
- Phase 8.1 MVP: Return error "Please specify a date/time"
- Future: Maintain conversation context for pronouns

### Pitfall 9: Cultural Date Variations
**Problem:** "Black Friday", "tax day", "end of fiscal year"
**Impact:** Cultural/regional date references
**Solution:**
- Phase 8.1: Don't support, ask for explicit date
- Future: Holiday/fiscal calendar lookup table

### Pitfall 10: Overfitting to Training Data
**Problem:** LLM trained on specific date formats may fail on variations
**Impact:** Parsing works on common inputs, fails on edge cases
**Solution:**
- Extensive test coverage (see Test Case Recommendations)
- Fallback to traditional date parsers (dateparser)
- Monitor and log failures for retraining

---

## Test Case Recommendations

### Test Coverage Goals
- **Minimum**: 85% code coverage
- **Focus**: Edge cases > happy path
- **Strategy**: Boundary testing, equivalence partitioning, error path testing

### Test Suite Structure

```
tests/
├── test_date_parsing.py          # Date parsing edge cases
├── test_time_parsing.py          # Time parsing edge cases
├── test_priority_inference.py    # Priority keyword detection
├── test_contradictions.py        # Contradictory input handling
├── test_timezone.py              # Timezone handling
├── test_validation.py            # Multi-layer validation
├── test_degradation.py           # Graceful degradation paths
└── test_integration.py           # End-to-end scenarios
```

### Critical Test Cases (Minimum)

#### Date Parsing (20 test cases)
1. Relative dates: "tomorrow", "next week", "in 2 weeks"
2. Ambiguous relative: "next Tuesday" on Monday, Thursday, Sunday
3. Day overflow: "January 31" → "next month"
4. Past date: "January 3" (spoken on January 5)
5. Month/day ambiguity: "01/03/2025", "13/03/2025"
6. Two-digit year: "03/15/25", "03/15/50"
7. Month formats: "Mar 15", "March 15", "3/15"
8. Ordinal dates: "March 3rd", "the 3rd of March"
9. ISO 8601: "2025-11-04"
10. Weekend: "this weekend" on Wednesday, Saturday
11. End of month: "end of the month" in February
12. Holidays (rejection): "Christmas", "tax day"
13. "This Friday" on a Friday
14. "In a couple days"
15. "Week" vs "workweek"
16. "Until Friday" (end condition)
17. Date range: "between Nov 4-6"
18. Implied year: "March 15" (current year vs next)
19. Leap year: "February 29, 2024" vs "February 29, 2025"
20. Quarter references: "Q1", "end of Q2"

#### Time Parsing (15 test cases)
1. 12-hour without meridiem: "5:00"
2. Midnight/noon: "12:00 AM", "12:00 PM", "noon", "midnight"
3. 24-hour format: "17:30", "1730"
4. Time of day: "morning", "afternoon", "evening"
5. Duration: "in 90 minutes", "1.5 hours", "hour and a half"
6. Colloquial: "half past 3", "quarter to 5"
7. Time already passed: "3 PM" at 4:15 PM
8. Edge of day: "tomorrow" at 11:58 PM
9. "Later today" at 11:30 PM
10. Meridiem ambiguity at boundary: "12:30 AM", "12:30 PM"
11. "5 o'clock" vs "5:00"
12. Military time: "1500 hours"
13. Seconds: "in 30 seconds" (not supported, graceful rejection)
14. Microseconds: rejection test
15. Time range: "between 2-4 PM"

#### Priority Inference (10 test cases)
1. Urgent keywords: "ASAP", "urgent", "emergency"
2. Important keywords: "important", "don't forget"
3. Chill keywords: "chill", "when you can", "sometime"
4. Default with time: "Buy milk tomorrow" → IMPORTANT
5. Default without time: "Buy milk" → CHILL
6. Contradictory: "urgent chill task"
7. Implicit urgency: "before deadline" → URGENT
8. Question format: "Should I call mom?" → CHILL
9. Multiple urgency levels: "important ASAP"
10. Case sensitivity: "URGENT" vs "urgent"

#### Timezone (8 test cases)
1. DST spring forward: March 10, 2025 at 2 AM
2. DST fall back: November 3, 2025 at 2 AM
3. Ambiguous time during DST: November 3 at 1:30 AM
4. UTC storage: verify all dates stored in UTC
5. Locale detection: verify user tz from browser
6. Timezone conversion: parse in user tz, store in UTC
7. Timezone abbreviations: reject "CST", accept "America/Chicago"
8. Future DST calculation: reminder set for 6 months ahead

#### Validation (10 test cases)
1. Empty text: "" → reject
2. Text too long: 501 characters → reject
3. Past date: "yesterday" → reject
4. Far future: "100 years from now" → reject
5. Invalid priority: "medium" → reject
6. Missing required field: no datetime → reject
7. Naive datetime (no tz): reject
8. Confidence out of range: -0.5, 1.5 → reject
9. SQL injection in text: "'; DROP TABLE reminders; --" → sanitize
10. Unicode/emoji in text: "🔥 urgent task" → accept

#### Graceful Degradation (8 test cases)
1. High confidence (0.95): proceed without confirmation
2. Medium confidence (0.75): show confirmation
3. Low confidence (0.55): offer multiple options
4. Failed parse (0.3): fall back to manual entry
5. Partial parse: text only, no date → date picker
6. Ambiguous priority: default to IMPORTANT
7. Ambiguous time: default to 9 AM
8. LLM timeout: fall back to dateparser

#### Integration (10 test cases)
1. Voice input → text → parse → store → retrieve
2. Multiple reminders: 3 reminders, different times
3. Edit reminder: change date/time
4. Complete reminder: mark as done
5. Delete reminder: soft delete
6. Timezone change: update user tz, verify reminders still correct
7. DST transition: verify reminders adjust correctly
8. Offline mode: create reminder offline, sync online
9. Conflict resolution: same reminder created on two devices
10. Bulk operations: import 50 reminders

### Test Data Generator

Create fixture for common test scenarios:

```python
import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

@pytest.fixture
def test_dates():
    """Common test date scenarios"""
    now = datetime.now(ZoneInfo('America/Los_Angeles'))
    return {
        'now': now,
        'today': now.replace(hour=9, minute=0, second=0),
        'tomorrow': now + timedelta(days=1),
        'next_week': now + timedelta(weeks=1),
        'past': now - timedelta(days=1),
        'far_future': now + timedelta(days=3650),  # 10 years
        'dst_spring': datetime(2025, 3, 10, 2, 0, tzinfo=ZoneInfo('America/Los_Angeles')),
        'dst_fall': datetime(2025, 11, 3, 2, 0, tzinfo=ZoneInfo('America/Los_Angeles')),
    }

@pytest.fixture
def test_inputs():
    """Common user input scenarios"""
    return {
        'simple': "Remind me to buy milk tomorrow",
        'urgent': "URGENT: Call dentist ASAP",
        'chill': "Chill reminder to clean garage sometime",
        'specific_time': "Remind me at 3 PM on Friday",
        'vague': "Remind me to call mom eventually",
        'contradictory': "Urgent task for someday",
        'past': "Remind me yesterday at 5 PM",
        'ambiguous': "Remind me next Tuesday",
        'no_time': "Buy groceries",
        'complex': "Important: Submit quarterly report by end of month before 5 PM",
    }
```

### Performance Test Targets

- **Parsing latency**: < 200ms per reminder
- **LLM inference**: < 2 seconds (acceptable for UX)
- **Database write**: < 50ms
- **End-to-end**: < 3 seconds (voice → stored)

### Continuous Testing Strategy

1. **Unit tests**: Run on every commit (pre-commit hook)
2. **Integration tests**: Run on every push
3. **Edge case tests**: Run nightly
4. **Performance tests**: Run weekly
5. **User acceptance tests**: Run before each release

---

## Implementation Checklist

Use this checklist to ensure all edge cases are addressed:

### Phase 8.1 Core Requirements
- [ ] Install `dateparser` library
- [ ] Configure dateparser settings (FUTURE context, user timezone, date order)
- [ ] Implement hybrid parsing (dateparser + python-dateutil fallback)
- [ ] Create LLM prompt for structured output (text, datetime, priority, confidence)
- [ ] Set up Pydantic validation models
- [ ] Implement timezone detection (browser → IP → UTC)
- [ ] Store all datetimes in UTC (ISO 8601 format)
- [ ] Convert UTC → user timezone for display

### Edge Case Handling
- [ ] Handle 27+ identified edge cases (see categories above)
- [ ] Implement relative date parsing ("tomorrow", "next week")
- [ ] Handle 12-hour time without meridiem (default to PM for 5:00)
- [ ] Resolve midnight/noon ambiguity
- [ ] Support multiple date formats (ISO 8601, MDY, DMY, month names)
- [ ] Handle past date references (reject or convert to next occurrence)
- [ ] Implement priority inference from keywords
- [ ] Detect and resolve contradictory inputs
- [ ] Handle DST transitions correctly
- [ ] Reject recurring patterns with helpful message

### Validation Layers
- [ ] Client-side validation (JavaScript)
- [ ] API validation (FastAPI/Pydantic)
- [ ] LLM output validation
- [ ] Database constraints (SQL)
- [ ] Input sanitization (SQL injection, XSS)

### Graceful Degradation
- [ ] Confidence scoring for LLM output (0.0-1.0)
- [ ] Level 1: High confidence (≥0.9) → proceed
- [ ] Level 2: Medium confidence (0.7-0.89) → confirm
- [ ] Level 3: Low confidence (0.5-0.69) → multiple options
- [ ] Level 4: Failed parse (<0.5) → manual entry
- [ ] Fallback chain: LLM → dateparser → python-dateutil → manual
- [ ] Helpful error messages (explain what failed, what succeeded)
- [ ] Log all degradations for model improvement

### Testing
- [ ] Write 20+ date parsing test cases
- [ ] Write 15+ time parsing test cases
- [ ] Write 10+ priority inference test cases
- [ ] Write 8+ timezone test cases
- [ ] Write 10+ validation test cases
- [ ] Write 8+ graceful degradation test cases
- [ ] Write 10+ integration test cases
- [ ] Achieve 85%+ code coverage
- [ ] Test DST transitions (spring forward, fall back)
- [ ] Test boundary conditions (midnight, end of month, leap year)
- [ ] Performance testing (< 200ms parsing, < 3s end-to-end)

### Documentation
- [ ] Document all edge cases in code comments
- [ ] Create user-facing docs for date/time input formats
- [ ] Document priority inference rules
- [ ] Document timezone behavior
- [ ] Create troubleshooting guide for common parsing failures
- [ ] Add inline examples for API endpoints

### Monitoring & Improvement
- [ ] Log all parsing attempts with confidence scores
- [ ] Track parsing failures by category
- [ ] Monitor degradation level distribution
- [ ] Collect user corrections to improve model
- [ ] Set up alerts for parsing success rate < 90%
- [ ] Quarterly review of edge case logs for new patterns

---

## Conclusion

This edge case analysis provides a comprehensive foundation for implementing robust NLP-based reminder parsing in Phase 8.1. Key takeaways:

1. **Use `dateparser` as primary library** for natural language date parsing
2. **Implement hybrid fallback strategy** (LLM → dateparser → python-dateutil → manual)
3. **Handle 27+ identified edge cases** across 5 major categories
4. **Resolve contradictions predictably** with priority hierarchy
5. **Always use timezone-aware datetimes** (store UTC, display local)
6. **Graceful degradation with confidence scoring** (4 levels)
7. **Multi-layer validation** (client, API, LLM, database)
8. **Extensive test coverage** (85%+ with edge case focus)
9. **Monitor and log all parsing attempts** for continuous improvement
10. **Provide helpful, specific error messages** when parsing fails

By addressing these edge cases proactively during the research phase, the development phase can proceed with clear requirements and minimal backtracking.

---

**Next Steps:**
1. Review this analysis with development team
2. Prioritize edge cases for MVP (Phase 8.1) vs future enhancements
3. Proceed to development phase with Architecture Subagent
4. Implement test cases before development (TDD approach)
5. Set up logging infrastructure for parsing analytics

---

*Research Complete: 2025-11-04*
*Subagent: Edge Case Analysis*
*Phase: Research*
*Model: Claude Sonnet 4.5*
