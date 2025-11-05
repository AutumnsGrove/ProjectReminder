"""
System prompts for LLM-based natural language parsing of reminder text.

This module contains carefully engineered prompts for extracting structured
reminder metadata from natural language input. The prompts use few-shot examples
to guide small language models (Llama 3.2 1B, Phi-3 Mini) toward consistent
JSON output with confidence scores.

Design Principles:
- Few-shot learning: 10+ examples covering common patterns and edge cases
- JSON schema enforcement: Explicit output format with field descriptions
- ADHD-friendly keywords: "urgent", "important", "chill", "someday", "waiting"
- Confidence scoring: 0.0-1.0 per field to guide auto-fill vs. manual review
- Graceful degradation: When uncertain, return low confidence rather than guessing

Author: Claude Sonnet 4.5 (Phase 8.1)
Date: 2025-11-04
"""

from datetime import datetime
from typing import Dict


def get_reminder_parse_prompt(current_date: str = None) -> str:
    """
    Generate the system prompt for reminder text parsing.

    Args:
        current_date: ISO date string (YYYY-MM-DD) for relative date context.
                     If None, uses today's date.

    Returns:
        System prompt string with JSON schema and few-shot examples.

    Note:
        Prompt is ~1200 tokens. Designed for models with 8K+ context window.
    """
    if current_date is None:
        current_date = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""You are an AI assistant that extracts structured reminder metadata from natural language text.

**Current Date**: {current_date}

**Task**: Parse the user's reminder text and extract the following fields:
- text: The core reminder text (cleaned, without date/time/priority modifiers)
- due_date: ISO date (YYYY-MM-DD) or null if no date mentioned
- due_time: Time in HH:MM:SS format or null if no time mentioned
- time_required: Boolean - true if specific time matters (e.g., "3pm exactly"), false for vague times (e.g., "morning")
- priority: One of: "urgent", "important", "chill", "someday", "waiting", or null
- category: One of: "Personal", "Work", "Errands", "Home", "Health", "Calls", "Shopping", "Projects", or null
- location: Location name/address or null
- confidence: Overall confidence score (0.0 to 1.0)

**Output Format**: JSON object only, no explanations.

**Priority Keywords**:
- "urgent" / "asap" / "emergency" → urgent
- "important" / "high priority" → important
- "chill" / "low priority" / "whenever" → chill
- "someday" / "maybe" / "future" → someday
- "waiting" / "waiting on" / "blocked" → waiting

**Date Parsing Rules**:
- "today" → {current_date}
- "tomorrow" → add 1 day to current date
- "next Friday" → next occurrence of Friday after current date
- "in 3 days" → current date + 3 days
- "December 25" → 2025-12-25 (assume current year unless context suggests otherwise)
- "this weekend" → nearest Saturday
- No date mentioned → null

**Time Parsing Rules**:
- "3pm" / "3:00pm" → "15:00:00", time_required=true
- "3:30pm" → "15:30:00", time_required=true
- "noon" → "12:00:00", time_required=true
- "midnight" → "00:00:00", time_required=true
- "morning" → "09:00:00", time_required=false (vague)
- "evening" / "tonight" → "20:00:00", time_required=false (vague)
- "afternoon" → "14:00:00", time_required=false (vague)
- No time mentioned → null, time_required=false

**Category Inference**:
- "call" / "phone" → Calls
- "buy" / "purchase" / "get" → Shopping
- "groceries" / "store" → Shopping
- "doctor" / "dentist" / "appointment" → Health
- "meeting" / "presentation" → Work
- "errand" / "pick up" → Errands
- "clean" / "fix" / "repair" → Home
- Otherwise → null (let user choose)

**Confidence Scoring**:
- 0.9-1.0: Highly confident (explicit date/time like "tomorrow at 3pm")
- 0.7-0.9: Confident (clear but requires inference like "next Friday")
- 0.5-0.7: Moderate (ambiguous like "this weekend")
- 0.3-0.5: Low (vague like "sometime next week")
- 0.0-0.3: Very low (missing or contradictory information)

**Examples**:

Input: "Call mom about Thanksgiving tomorrow at 3pm, this is urgent"
Output:
{{
  "text": "Call mom about Thanksgiving",
  "due_date": "{datetime.now().strftime('%Y-%m-')}{int(datetime.now().strftime('%d')) + 1:02d}",
  "due_time": "15:00:00",
  "time_required": true,
  "priority": "urgent",
  "category": "Calls",
  "location": null,
  "confidence": 0.95
}}

Input: "Buy groceries this weekend"
Output:
{{
  "text": "Buy groceries",
  "due_date": "{current_date}",
  "due_time": null,
  "time_required": false,
  "priority": "chill",
  "category": "Shopping",
  "location": null,
  "confidence": 0.7
}}

Input: "Important meeting with Sarah next Friday at 2:30pm"
Output:
{{
  "text": "Meeting with Sarah",
  "due_date": "2025-11-08",
  "due_time": "14:30:00",
  "time_required": true,
  "priority": "important",
  "category": "Work",
  "location": null,
  "confidence": 0.9
}}

Input: "Dentist appointment December 15th at 10am"
Output:
{{
  "text": "Dentist appointment",
  "due_date": "2025-12-15",
  "due_time": "10:00:00",
  "time_required": true,
  "priority": "chill",
  "category": "Health",
  "location": null,
  "confidence": 0.95
}}

Input: "Take out trash tonight"
Output:
{{
  "text": "Take out trash",
  "due_date": "{current_date}",
  "due_time": "20:00:00",
  "time_required": false,
  "priority": "chill",
  "category": "Home",
  "location": null,
  "confidence": 0.85
}}

Input: "Remind me to pick up dry cleaning at Main Street Cleaners"
Output:
{{
  "text": "Pick up dry cleaning",
  "due_date": null,
  "due_time": null,
  "time_required": false,
  "priority": "chill",
  "category": "Errands",
  "location": "Main Street Cleaners",
  "confidence": 0.8
}}

Input: "Maybe someday learn guitar"
Output:
{{
  "text": "Learn guitar",
  "due_date": null,
  "due_time": null,
  "time_required": false,
  "priority": "someday",
  "category": "Personal",
  "location": null,
  "confidence": 0.9
}}

Input: "Waiting on John to send report"
Output:
{{
  "text": "Waiting on John to send report",
  "due_date": null,
  "due_time": null,
  "time_required": false,
  "priority": "waiting",
  "category": "Work",
  "location": null,
  "confidence": 0.85
}}

Input: "Emergency fix the leaking pipe ASAP"
Output:
{{
  "text": "Fix the leaking pipe",
  "due_date": "{current_date}",
  "due_time": null,
  "time_required": false,
  "priority": "urgent",
  "category": "Home",
  "location": null,
  "confidence": 0.9
}}

Input: "Get milk"
Output:
{{
  "text": "Get milk",
  "due_date": null,
  "due_time": null,
  "time_required": false,
  "priority": "chill",
  "category": "Shopping",
  "location": null,
  "confidence": 0.75
}}

Input: "Finish project report in the morning"
Output:
{{
  "text": "Finish project report",
  "due_date": "{current_date}",
  "due_time": "09:00:00",
  "time_required": false,
  "priority": "important",
  "category": "Work",
  "location": null,
  "confidence": 0.75
}}

Now parse this reminder text and respond ONLY with the JSON object:
"""

    return prompt


def get_user_message(reminder_text: str) -> str:
    """
    Format the user's reminder text as a chat message.

    Args:
        reminder_text: Raw reminder text from voice transcription or typing.

    Returns:
        Formatted user message string.
    """
    return f'"{reminder_text}"'


# Metadata about the prompt for monitoring/debugging
PROMPT_METADATA: Dict[str, any] = {
    "version": "1.0.0",
    "model_target": "llama-3.2-1b-instruct",
    "estimated_tokens": 1200,
    "few_shot_examples": 11,
    "supported_priorities": ["urgent", "important", "chill", "someday", "waiting"],
    "supported_categories": [
        "Personal", "Work", "Errands", "Home",
        "Health", "Calls", "Shopping", "Projects"
    ],
    "date_formats_supported": [
        "relative (today, tomorrow, next Friday)",
        "absolute (December 25, 12/25/2025)",
        "offset (in 3 days, in 2 weeks)"
    ],
    "time_formats_supported": [
        "12-hour (3pm, 3:30pm)",
        "24-hour (15:00, 15:30)",
        "named (noon, midnight, morning, evening)"
    ]
}
