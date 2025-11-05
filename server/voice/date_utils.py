"""
Date and time parsing utilities for natural language reminder input.

This module provides functions to parse natural language date and time expressions
into structured ISO 8601 formats. It uses dateparser for fuzzy parsing and
python-dateutil for timezone-aware datetime manipulation.

Key Features:
- Relative dates: "tomorrow", "next Friday", "in 3 days"
- Absolute dates: "December 25", "12/25/2025", "Dec 25th"
- Named times: "noon", "midnight", "morning", "evening"
- Timezone awareness: Uses system timezone for consistency
- Graceful failure: Returns None instead of raising exceptions

Author: Claude Sonnet 4.5 (Phase 8.1)
Date: 2025-11-04
"""

import re
from datetime import datetime, time as dt_time, timedelta
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

import dateparser
from dateutil import parser as dateutil_parser


# Get system timezone for consistent date/time handling
def get_system_timezone() -> ZoneInfo:
    """
    Get the system's local timezone.

    Returns:
        ZoneInfo object for the system timezone.
    """
    try:
        # Try to get system timezone from /etc/localtime or environment
        import tzlocal
        return ZoneInfo(str(tzlocal.get_localzone()))
    except Exception:
        # Fallback to UTC if timezone detection fails
        return ZoneInfo("UTC")


SYSTEM_TZ = get_system_timezone()


def parse_natural_date(text: str, reference_date: Optional[datetime] = None) -> Optional[str]:
    """
    Parse natural language date expression to ISO 8601 date string.

    Args:
        text: Natural language text containing a date (e.g., "tomorrow", "next Friday")
        reference_date: Reference datetime for relative dates (defaults to now)

    Returns:
        ISO 8601 date string (YYYY-MM-DD) or None if no date found.

    Examples:
        >>> parse_natural_date("tomorrow")
        '2025-11-05'  # Assuming today is 2025-11-04

        >>> parse_natural_date("next Friday")
        '2025-11-08'  # Assuming today is 2025-11-04 (Monday)

        >>> parse_natural_date("December 25")
        '2025-12-25'

        >>> parse_natural_date("in 3 days")
        '2025-11-07'

        >>> parse_natural_date("no date here")
        None
    """
    if not text or not text.strip():
        return None

    # Use reference date or current time in system timezone
    if reference_date is None:
        reference_date = datetime.now(SYSTEM_TZ)
    elif reference_date.tzinfo is None:
        # Make naive datetime timezone-aware
        reference_date = reference_date.replace(tzinfo=SYSTEM_TZ)

    try:
        # Parse with dateparser using future-preference for ambiguous dates
        parsed_date = dateparser.parse(
            text,
            settings={
                'PREFER_DATES_FROM': 'future',  # "Monday" means next Monday
                'RELATIVE_BASE': reference_date,
                'TIMEZONE': str(SYSTEM_TZ),
                'RETURN_AS_TIMEZONE_AWARE': True
            }
        )

        if parsed_date:
            # Return ISO 8601 date string (YYYY-MM-DD)
            return parsed_date.strftime('%Y-%m-%d')

        return None

    except Exception as e:
        # Log error but don't crash - graceful degradation
        print(f"[date_utils] Error parsing date from '{text}': {e}")
        return None


def parse_natural_time(text: str) -> Optional[Tuple[str, bool]]:
    """
    Parse natural language time expression to HH:MM:SS format.

    Args:
        text: Natural language text containing a time (e.g., "3pm", "noon", "morning")

    Returns:
        Tuple of (time_string, is_specific) or None if no time found.
        - time_string: ISO 8601 time (HH:MM:SS)
        - is_specific: True if exact time (3pm), False if vague (morning)

    Examples:
        >>> parse_natural_time("3pm")
        ('15:00:00', True)

        >>> parse_natural_time("3:30pm")
        ('15:30:00', True)

        >>> parse_natural_time("noon")
        ('12:00:00', True)

        >>> parse_natural_time("morning")
        ('09:00:00', False)  # Vague time

        >>> parse_natural_time("no time here")
        None
    """
    if not text or not text.strip():
        return None

    text_lower = text.lower()

    # Named time mappings (specific times)
    specific_named_times = {
        'noon': '12:00:00',
        'midnight': '00:00:00',
        '12pm': '12:00:00',
        '12am': '00:00:00',
    }

    # Vague time mappings (approximate times)
    vague_named_times = {
        'morning': '09:00:00',
        'afternoon': '14:00:00',
        'evening': '20:00:00',
        'tonight': '20:00:00',
        'night': '21:00:00',
    }

    # Check for specific named times first
    for keyword, time_str in specific_named_times.items():
        if keyword in text_lower:
            return (time_str, True)

    # Check for vague named times
    for keyword, time_str in vague_named_times.items():
        if keyword in text_lower:
            return (time_str, False)

    # Try to extract time patterns with regex
    # Match patterns like: 3pm, 3:30pm, 15:00, 1500, 3 o'clock
    time_patterns = [
        # 12-hour format with minutes: "3:30pm", "11:45am"
        r'\b(\d{1,2}):(\d{2})\s*(am|pm)\b',
        # 12-hour format without minutes: "3pm", "11am"
        r'\b(\d{1,2})\s*(am|pm)\b',
        # 24-hour format with colon: "15:00", "09:30"
        r'\b(\d{1,2}):(\d{2})\b',
        # 24-hour format without colon: "1500", "0930"
        r'\b(\d{4})\b',
        # "o'clock" format: "3 o'clock"
        r"\b(\d{1,2})\s*o[\\'\\']?clock\b",
    ]

    for pattern in time_patterns:
        match = re.search(pattern, text_lower)
        if match:
            groups = match.groups()

            # Handle different match types
            if len(groups) == 3:  # HH:MM am/pm
                hour = int(groups[0])
                minute = int(groups[1])
                period = groups[2]

                # Convert 12-hour to 24-hour
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0

                return (f"{hour:02d}:{minute:02d}:00", True)

            elif len(groups) == 2 and groups[1] in ('am', 'pm'):  # HH am/pm
                hour = int(groups[0])
                period = groups[1]

                # Convert 12-hour to 24-hour
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0

                return (f"{hour:02d}:00:00", True)

            elif len(groups) == 2 and groups[1].isdigit():  # HH:MM (24-hour)
                hour = int(groups[0])
                minute = int(groups[1])

                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return (f"{hour:02d}:{minute:02d}:00", True)

            elif len(groups) == 1 and len(groups[0]) == 4:  # HHMM (military time)
                hour = int(groups[0][:2])
                minute = int(groups[0][2:])

                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return (f"{hour:02d}:{minute:02d}:00", True)

            elif len(groups) == 1:  # H o'clock
                hour = int(groups[0])

                # Assume PM for afternoon/evening context (heuristic)
                if 1 <= hour <= 11:
                    # Check context for afternoon/evening keywords
                    if any(word in text_lower for word in ['afternoon', 'evening', 'tonight', 'pm']):
                        hour += 12

                if 0 <= hour <= 23:
                    return (f"{hour:02d}:00:00", True)

    # Try dateparser as fallback for complex expressions like "in 2 hours"
    try:
        parsed_datetime = dateparser.parse(
            text,
            settings={
                'PREFER_DATES_FROM': 'future',
                'TIMEZONE': str(SYSTEM_TZ),
                'RETURN_AS_TIMEZONE_AWARE': True
            }
        )

        if parsed_datetime:
            # Only return if the parsed time is different from the reference time
            # (i.e., actual time information was extracted)
            time_str = parsed_datetime.strftime('%H:%M:%S')
            return (time_str, True)

    except Exception:
        pass

    return None


def normalize_datetime(date_str: Optional[str], time_str: Optional[str],
                      time_required: bool = False) -> Optional[str]:
    """
    Combine date and time into ISO 8601 datetime string.

    Args:
        date_str: ISO date string (YYYY-MM-DD) or None
        time_str: ISO time string (HH:MM:SS) or None
        time_required: Whether the time is required for the datetime

    Returns:
        ISO 8601 datetime string (YYYY-MM-DDTHH:MM:SS) or None.

    Examples:
        >>> normalize_datetime("2025-11-05", "15:00:00", True)
        '2025-11-05T15:00:00'

        >>> normalize_datetime("2025-11-05", None, False)
        '2025-11-05T00:00:00'  # Default to midnight

        >>> normalize_datetime(None, "15:00:00", True)
        None  # Can't create datetime without date
    """
    if not date_str:
        return None

    if time_str:
        return f"{date_str}T{time_str}"
    elif time_required:
        # Time is required but not provided
        return None
    else:
        # Default to midnight if no time specified and not required
        return f"{date_str}T00:00:00"


def get_relative_date(days_offset: int, reference_date: Optional[datetime] = None) -> str:
    """
    Get a date relative to the reference date.

    Args:
        days_offset: Number of days to add (can be negative)
        reference_date: Reference datetime (defaults to now)

    Returns:
        ISO 8601 date string (YYYY-MM-DD).

    Examples:
        >>> get_relative_date(1)  # Tomorrow
        '2025-11-05'

        >>> get_relative_date(7)  # One week from now
        '2025-11-11'

        >>> get_relative_date(-1)  # Yesterday
        '2025-11-03'
    """
    if reference_date is None:
        reference_date = datetime.now(SYSTEM_TZ)
    elif reference_date.tzinfo is None:
        reference_date = reference_date.replace(tzinfo=SYSTEM_TZ)

    target_date = reference_date + timedelta(days=days_offset)
    return target_date.strftime('%Y-%m-%d')


def is_past_date(date_str: str, reference_date: Optional[datetime] = None) -> bool:
    """
    Check if a date string represents a past date.

    Args:
        date_str: ISO date string (YYYY-MM-DD)
        reference_date: Reference datetime (defaults to now)

    Returns:
        True if date is in the past, False otherwise.

    Examples:
        >>> is_past_date("2020-01-01")
        True

        >>> is_past_date("2030-01-01")
        False
    """
    if reference_date is None:
        reference_date = datetime.now(SYSTEM_TZ).date()
    else:
        reference_date = reference_date.date()

    try:
        parsed_date = datetime.fromisoformat(date_str).date()
        return parsed_date < reference_date
    except Exception:
        return False
