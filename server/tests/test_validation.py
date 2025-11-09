"""
Tests for input validation (dates, times, fields).

Verifies that Pydantic validators correctly reject invalid inputs
and accept valid inputs for reminder fields.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pydantic import ValidationError
from server.models import ReminderCreate, ReminderUpdate


class TestDateValidation:
    """Test due_date field validation."""

    def test_valid_date_accepted(self):
        """Valid ISO 8601 date should be accepted."""
        reminder = ReminderCreate(
            text="Test reminder",
            due_date="2025-12-25"
        )
        assert reminder.due_date == "2025-12-25"

    def test_none_date_accepted(self):
        """None (no date) should be accepted as optional."""
        reminder = ReminderCreate(
            text="Test reminder",
            due_date=None
        )
        assert reminder.due_date is None

    def test_omitted_date_accepted(self):
        """Omitting due_date should be accepted as optional."""
        reminder = ReminderCreate(text="Test reminder")
        assert reminder.due_date is None

    def test_invalid_month_rejected(self):
        """Date with invalid month (13) should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_date="2025-13-01"
            )
        assert "due_date" in str(exc_info.value)

    def test_invalid_day_rejected(self):
        """Date with invalid day (32) should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_date="2025-01-32"
            )
        assert "due_date" in str(exc_info.value)

    def test_february_invalid_day_rejected(self):
        """February 31 should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_date="2025-02-31"
            )
        assert "due_date" in str(exc_info.value)

    def test_february_30_rejected(self):
        """February 30 should be rejected in non-leap year."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_date="2025-02-30"
            )
        assert "due_date" in str(exc_info.value)

    def test_february_29_non_leap_rejected(self):
        """February 29 should be rejected in non-leap year."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_date="2025-02-29"
            )
        assert "due_date" in str(exc_info.value)

    def test_february_29_leap_year_accepted(self):
        """February 29 should be accepted in leap year."""
        reminder = ReminderCreate(
            text="Test reminder",
            due_date="2024-02-29"
        )
        assert reminder.due_date == "2024-02-29"

    def test_april_31_rejected(self):
        """April 31 should be rejected (April has 30 days)."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_date="2025-04-31"
            )
        assert "due_date" in str(exc_info.value)

    def test_non_iso_format_mm_dd_yyyy_rejected(self):
        """Non-ISO format MM/DD/YYYY should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_date="12/25/2025"
            )
        assert "due_date" in str(exc_info.value)

    def test_non_iso_format_dd_mm_yyyy_rejected(self):
        """Non-ISO format DD-MM-YYYY should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_date="25-12-2025"
            )
        assert "due_date" in str(exc_info.value)

    def test_invalid_string_rejected(self):
        """Invalid string like 'invalid-date' should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_date="invalid-date"
            )
        assert "due_date" in str(exc_info.value)

    def test_relative_date_next_tuesday_rejected(self):
        """Relative date like 'next Tuesday' should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_date="next Tuesday"
            )
        assert "due_date" in str(exc_info.value)

    def test_relative_date_tomorrow_rejected(self):
        """Relative date like 'tomorrow' should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_date="tomorrow"
            )
        assert "due_date" in str(exc_info.value)

    def test_english_date_format_rejected(self):
        """English date format should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_date="December 25, 2025"
            )
        assert "due_date" in str(exc_info.value)

    def test_valid_leap_year_dates(self):
        """Valid dates in leap years should be accepted."""
        # 2024 is a leap year
        reminder = ReminderCreate(
            text="Test reminder",
            due_date="2024-02-29"
        )
        assert reminder.due_date == "2024-02-29"

    def test_valid_century_leap_year(self):
        """Valid date in century leap year (2000) should be accepted."""
        reminder = ReminderCreate(
            text="Test reminder",
            due_date="2000-02-29"
        )
        assert reminder.due_date == "2000-02-29"

    def test_invalid_century_non_leap_year(self):
        """Date in century non-leap year (1900, 2100) should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_date="1900-02-29"
            )
        assert "due_date" in str(exc_info.value)


class TestTimeValidation:
    """Test due_time field validation."""

    def test_valid_time_accepted(self):
        """Valid ISO 8601 time should be accepted."""
        reminder = ReminderCreate(
            text="Test reminder",
            due_time="14:30:00"
        )
        assert reminder.due_time == "14:30:00"

    def test_midnight_accepted(self):
        """Midnight (00:00:00) should be accepted."""
        reminder = ReminderCreate(
            text="Test reminder",
            due_time="00:00:00"
        )
        assert reminder.due_time == "00:00:00"

    def test_end_of_day_accepted(self):
        """End of day (23:59:59) should be accepted."""
        reminder = ReminderCreate(
            text="Test reminder",
            due_time="23:59:59"
        )
        assert reminder.due_time == "23:59:59"

    def test_none_time_accepted(self):
        """None (no time) should be accepted as optional."""
        reminder = ReminderCreate(
            text="Test reminder",
            due_time=None
        )
        assert reminder.due_time is None

    def test_omitted_time_accepted(self):
        """Omitting due_time should be accepted as optional."""
        reminder = ReminderCreate(text="Test reminder")
        assert reminder.due_time is None

    def test_invalid_hour_25_rejected(self):
        """Time with invalid hour (25) should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_time="25:00:00"
            )
        assert "due_time" in str(exc_info.value)

    def test_invalid_hour_99_rejected(self):
        """Time with invalid hour (99) should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_time="99:00:00"
            )
        assert "due_time" in str(exc_info.value)

    def test_invalid_minute_60_rejected(self):
        """Time with invalid minute (60) should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_time="14:60:00"
            )
        assert "due_time" in str(exc_info.value)

    def test_invalid_minute_99_rejected(self):
        """Time with invalid minute (99) should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_time="14:99:00"
            )
        assert "due_time" in str(exc_info.value)

    def test_invalid_second_60_rejected(self):
        """Time with invalid second (60) should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_time="14:30:60"
            )
        assert "due_time" in str(exc_info.value)

    def test_invalid_second_99_rejected(self):
        """Time with invalid second (99) should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_time="14:30:99"
            )
        assert "due_time" in str(exc_info.value)

    def test_12hour_format_with_am_rejected(self):
        """12-hour format like '2:30 AM' should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_time="2:30 AM"
            )
        assert "due_time" in str(exc_info.value)

    def test_12hour_format_with_pm_rejected(self):
        """12-hour format like '2:30 PM' should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_time="2:30 PM"
            )
        assert "due_time" in str(exc_info.value)

    def test_invalid_string_morning_rejected(self):
        """Invalid string like 'morning' should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_time="morning"
            )
        assert "due_time" in str(exc_info.value)

    def test_invalid_string_noon_rejected(self):
        """Invalid string like 'noon' should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_time="noon"
            )
        assert "due_time" in str(exc_info.value)

    def test_time_without_seconds_rejected(self):
        """Time format HH:MM (without seconds) should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_time="14:30"
            )
        assert "due_time" in str(exc_info.value)

    def test_time_with_milliseconds_rejected(self):
        """Time with milliseconds should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test reminder",
                due_time="14:30:00.123"
            )
        assert "due_time" in str(exc_info.value)

    def test_valid_times_range(self):
        """Various valid times throughout the day should be accepted."""
        valid_times = [
            "00:00:00",  # midnight
            "06:00:00",  # early morning
            "12:00:00",  # noon
            "15:30:45",  # afternoon
            "23:59:59"   # end of day
        ]
        for time_str in valid_times:
            reminder = ReminderCreate(
                text="Test reminder",
                due_time=time_str
            )
            assert reminder.due_time == time_str


class TestReminderUpdateValidation:
    """Test that ReminderUpdate also validates dates/times."""

    def test_update_invalid_date_rejected(self):
        """ReminderUpdate should also reject invalid dates."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderUpdate(due_date="2025-13-32")
        assert "due_date" in str(exc_info.value)

    def test_update_invalid_time_rejected(self):
        """ReminderUpdate should also reject invalid times."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderUpdate(due_time="25:99:99")
        assert "due_time" in str(exc_info.value)

    def test_update_valid_date_accepted(self):
        """ReminderUpdate should accept valid dates."""
        update = ReminderUpdate(due_date="2025-12-31")
        assert update.due_date == "2025-12-31"

    def test_update_valid_time_accepted(self):
        """ReminderUpdate should accept valid times."""
        update = ReminderUpdate(due_time="15:45:30")
        assert update.due_time == "15:45:30"

    def test_update_all_fields_optional(self):
        """ReminderUpdate should accept empty update."""
        update = ReminderUpdate()
        assert update.text is None
        assert update.due_date is None
        assert update.due_time is None

    def test_update_with_valid_text(self):
        """ReminderUpdate should accept valid text."""
        update = ReminderUpdate(text="Updated reminder text")
        assert update.text == "Updated reminder text"

    def test_update_with_empty_text_rejected(self):
        """ReminderUpdate should reject empty text."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderUpdate(text="")
        assert "text" in str(exc_info.value)


class TestTextFieldValidation:
    """Test text field validation (length limits, etc.)."""

    def test_text_required_in_create(self):
        """Text field should be required in ReminderCreate."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate()
        assert "text" in str(exc_info.value)

    def test_empty_text_rejected(self):
        """Empty text should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(text="")
        assert "text" in str(exc_info.value)

    def test_text_with_single_char_accepted(self):
        """Single character text should be accepted."""
        reminder = ReminderCreate(text="A")
        assert reminder.text == "A"

    def test_text_with_spaces_accepted(self):
        """Text with spaces should be accepted."""
        reminder = ReminderCreate(text="Call mom about Thanksgiving dinner")
        assert reminder.text == "Call mom about Thanksgiving dinner"

    def test_text_with_special_chars_accepted(self):
        """Text with special characters should be accepted."""
        reminder = ReminderCreate(text="Buy: milk, eggs & cheese @store!")
        assert reminder.text == "Buy: milk, eggs & cheese @store!"

    def test_text_with_unicode_accepted(self):
        """Text with unicode characters should be accepted."""
        reminder = ReminderCreate(text="Café meeting at 3pm")
        assert reminder.text == "Café meeting at 3pm"

    def test_text_with_newlines_accepted(self):
        """Text with newlines should be accepted."""
        reminder = ReminderCreate(text="Task 1\nTask 2\nTask 3")
        assert reminder.text == "Task 1\nTask 2\nTask 3"

    def test_long_text_rejected(self):
        """Text exceeding max length (1000) should be rejected."""
        long_text = "a" * 1001
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(text=long_text)
        assert "text" in str(exc_info.value)

    def test_max_length_text_accepted(self):
        """Text at max length (1000) should be accepted."""
        max_text = "a" * 1000
        reminder = ReminderCreate(text=max_text)
        assert len(reminder.text) == 1000

    def test_text_just_under_max_accepted(self):
        """Text just under max length should be accepted."""
        text = "a" * 999
        reminder = ReminderCreate(text=text)
        assert len(reminder.text) == 999


class TestLocationValidation:
    """Test location field validation."""

    def test_location_name_max_length_accepted(self):
        """Location name at max length (500) should be accepted."""
        location_name = "a" * 500
        reminder = ReminderCreate(
            text="Test",
            location_name=location_name
        )
        assert len(reminder.location_name) == 500

    def test_location_name_exceeds_max_rejected(self):
        """Location name exceeding max length (500) should be rejected."""
        location_name = "a" * 501
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test",
                location_name=location_name
            )
        assert "location_name" in str(exc_info.value)

    def test_location_address_max_length_accepted(self):
        """Location address at max length (1000) should be accepted."""
        location_address = "a" * 1000
        reminder = ReminderCreate(
            text="Test",
            location_address=location_address
        )
        assert len(reminder.location_address) == 1000

    def test_location_address_exceeds_max_rejected(self):
        """Location address exceeding max length (1000) should be rejected."""
        location_address = "a" * 1001
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test",
                location_address=location_address
            )
        assert "location_address" in str(exc_info.value)

    def test_latitude_valid_range(self):
        """Latitude within valid range (-90 to 90) should be accepted."""
        for lat in [-90, -45, 0, 45, 90]:
            reminder = ReminderCreate(
                text="Test",
                location_lat=lat
            )
            assert reminder.location_lat == lat

    def test_latitude_exceeds_max_rejected(self):
        """Latitude exceeding 90 should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test",
                location_lat=91
            )
        assert "location_lat" in str(exc_info.value)

    def test_latitude_below_min_rejected(self):
        """Latitude below -90 should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test",
                location_lat=-91
            )
        assert "location_lat" in str(exc_info.value)

    def test_longitude_valid_range(self):
        """Longitude within valid range (-180 to 180) should be accepted."""
        for lng in [-180, -90, 0, 90, 180]:
            reminder = ReminderCreate(
                text="Test",
                location_lng=lng
            )
            assert reminder.location_lng == lng

    def test_longitude_exceeds_max_rejected(self):
        """Longitude exceeding 180 should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test",
                location_lng=181
            )
        assert "location_lng" in str(exc_info.value)

    def test_longitude_below_min_rejected(self):
        """Longitude below -180 should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test",
                location_lng=-181
            )
        assert "location_lng" in str(exc_info.value)


class TestPriorityValidation:
    """Test priority field validation."""

    def test_valid_priorities_accepted(self):
        """All valid priority values should be accepted."""
        valid_priorities = ["someday", "chill", "important", "urgent", "waiting"]
        for priority in valid_priorities:
            reminder = ReminderCreate(
                text="Test",
                priority=priority
            )
            assert reminder.priority == priority

    def test_default_priority_chill(self):
        """Default priority should be 'chill'."""
        reminder = ReminderCreate(text="Test")
        assert reminder.priority == "chill"

    def test_invalid_priority_rejected(self):
        """Invalid priority should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test",
                priority="low"
            )
        assert "priority" in str(exc_info.value)


class TestStatusValidation:
    """Test status field validation."""

    def test_valid_statuses_accepted(self):
        """All valid status values should be accepted."""
        valid_statuses = ["pending", "completed", "snoozed"]
        for status in valid_statuses:
            reminder = ReminderCreate(
                text="Test",
                status=status
            )
            assert reminder.status == status

    def test_default_status_pending(self):
        """Default status should be 'pending'."""
        reminder = ReminderCreate(text="Test")
        assert reminder.status == "pending"

    def test_invalid_status_rejected(self):
        """Invalid status should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test",
                status="in_progress"
            )
        assert "status" in str(exc_info.value)


class TestCategoryValidation:
    """Test category field validation."""

    def test_category_max_length_accepted(self):
        """Category at max length (100) should be accepted."""
        category = "a" * 100
        reminder = ReminderCreate(
            text="Test",
            category=category
        )
        assert len(reminder.category) == 100

    def test_category_exceeds_max_rejected(self):
        """Category exceeding max length (100) should be rejected."""
        category = "a" * 101
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test",
                category=category
            )
        assert "category" in str(exc_info.value)

    def test_category_optional(self):
        """Category should be optional."""
        reminder = ReminderCreate(text="Test")
        assert reminder.category is None


class TestLocationRadiusValidation:
    """Test location_radius field validation."""

    def test_location_radius_default_100(self):
        """Default location_radius should be 100."""
        reminder = ReminderCreate(text="Test")
        assert reminder.location_radius == 100

    def test_location_radius_min_accepted(self):
        """Minimum location_radius (10) should be accepted."""
        reminder = ReminderCreate(
            text="Test",
            location_radius=10
        )
        assert reminder.location_radius == 10

    def test_location_radius_max_accepted(self):
        """Maximum location_radius (10000) should be accepted."""
        reminder = ReminderCreate(
            text="Test",
            location_radius=10000
        )
        assert reminder.location_radius == 10000

    def test_location_radius_below_min_rejected(self):
        """Location_radius below 10 should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test",
                location_radius=9
            )
        assert "location_radius" in str(exc_info.value)

    def test_location_radius_exceeds_max_rejected(self):
        """Location_radius exceeding 10000 should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test",
                location_radius=10001
            )
        assert "location_radius" in str(exc_info.value)


class TestCombinedValidation:
    """Test combinations of valid fields."""

    def test_full_reminder_valid(self):
        """Full reminder with all valid fields should be accepted."""
        reminder = ReminderCreate(
            text="Call mom about Thanksgiving",
            due_date="2025-11-27",
            due_time="15:00:00",
            time_required=True,
            location_name="Mom's House",
            location_lat=40.7128,
            location_lng=-74.0060,
            location_radius=500,
            priority="important",
            category="Family",
            status="pending"
        )
        assert reminder.text == "Call mom about Thanksgiving"
        assert reminder.due_date == "2025-11-27"
        assert reminder.due_time == "15:00:00"

    def test_date_and_invalid_time_rejected(self):
        """Valid date with invalid time should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test",
                due_date="2025-12-25",
                due_time="25:00:00"
            )
        assert "due_time" in str(exc_info.value)

    def test_invalid_date_and_valid_time_rejected(self):
        """Invalid date with valid time should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test",
                due_date="2025-13-32",
                due_time="15:00:00"
            )
        assert "due_date" in str(exc_info.value)

    def test_minimal_valid_reminder(self):
        """Minimal reminder with only required field should be valid."""
        reminder = ReminderCreate(text="Test")
        assert reminder.text == "Test"
        assert reminder.due_date is None
        assert reminder.due_time is None
        assert reminder.location_name is None
        assert reminder.priority == "chill"
        assert reminder.status == "pending"
