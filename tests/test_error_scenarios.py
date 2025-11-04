"""
Error handling and edge case tests for the reminders API.

Tests cover:
- API validation errors (422)
- Not found errors (404)
- Authentication failures (401)
- Invalid input edge cases (400)
- Location validation errors
- Sync error scenarios
- Recurrence validation errors
"""

import pytest
import json


# =============================================================================
# API Validation Errors (422)
# =============================================================================

@pytest.mark.api
def test_create_reminder_missing_text_returns_422(client, auth_headers):
    """Test that creating a reminder without text returns 422 validation error."""
    response = client.post(
        "/api/reminders",
        json={"priority": "important"},  # Missing required 'text' field
        headers=auth_headers
    )
    assert response.status_code == 422
    # Verify error message mentions 'text' field
    error_detail = str(response.json().get("detail", "")).lower()
    assert "text" in error_detail


@pytest.mark.api
def test_create_reminder_invalid_priority_returns_422(client, auth_headers):
    """Test that creating a reminder with invalid priority returns 422."""
    response = client.post(
        "/api/reminders",
        json={
            "text": "Test reminder",
            "priority": "INVALID_PRIORITY"  # Not in allowed list
        },
        headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.api
def test_create_reminder_invalid_date_format_accepted_as_string(client, auth_headers):
    """Test that creating a reminder with invalid date format is accepted (stored as-is)."""
    response = client.post(
        "/api/reminders",
        json={
            "text": "Test reminder",
            "due_date": "not-a-date"  # Invalid format but accepted as string
        },
        headers=auth_headers
    )
    # API currently accepts any string for dates (no strict validation)
    assert response.status_code == 201
    data = response.json()
    assert data["due_date"] == "not-a-date"


@pytest.mark.api
def test_create_reminder_empty_text_returns_422(client, auth_headers):
    """Test that creating a reminder with empty text returns 422."""
    response = client.post(
        "/api/reminders",
        json={
            "text": "",  # Empty string should fail min_length validation
            "priority": "chill"
        },
        headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.api
def test_update_reminder_invalid_status_returns_422(client, auth_headers, created_reminder):
    """Test that updating a reminder with invalid status returns 422."""
    reminder_id = created_reminder["id"]

    response = client.patch(
        f"/api/reminders/{reminder_id}",
        json={"status": "INVALID_STATUS"},  # Not in allowed list
        headers=auth_headers
    )
    assert response.status_code == 422


# =============================================================================
# Not Found Errors (404)
# =============================================================================

@pytest.mark.api
def test_get_nonexistent_reminder_returns_404(client, auth_headers):
    """Test that GET /api/reminders/{invalid-id} returns 404."""
    fake_id = "550e8400-e29b-41d4-a716-446655440999"

    response = client.get(
        f"/api/reminders/{fake_id}",
        headers=auth_headers
    )
    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.api
def test_update_nonexistent_reminder_returns_404(client, auth_headers):
    """Test that PUT /api/reminders/{invalid-id} returns 404."""
    fake_id = "550e8400-e29b-41d4-a716-446655440999"

    response = client.patch(
        f"/api/reminders/{fake_id}",
        json={"text": "Updated text"},
        headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.api
def test_delete_nonexistent_reminder_returns_404(client, auth_headers):
    """Test that DELETE /api/reminders/{invalid-id} returns 404."""
    fake_id = "550e8400-e29b-41d4-a716-446655440999"

    response = client.delete(
        f"/api/reminders/{fake_id}",
        headers=auth_headers
    )
    assert response.status_code == 404


# =============================================================================
# Authentication Failures (401)
# =============================================================================

@pytest.mark.api
def test_create_reminder_no_auth_returns_401(client):
    """Test that creating a reminder without Authorization header returns 401."""
    response = client.post(
        "/api/reminders",
        json={"text": "Test reminder", "priority": "chill"}
        # No headers - missing auth
    )
    assert response.status_code == 401
    error_data = response.json()
    assert "detail" in error_data
    assert "authorization" in error_data["detail"].lower()


@pytest.mark.api
def test_create_reminder_invalid_token_returns_401(client):
    """Test that creating a reminder with invalid Bearer token returns 401."""
    response = client.post(
        "/api/reminders",
        json={"text": "Test reminder", "priority": "chill"},
        headers={"Authorization": "Bearer INVALID_TOKEN_12345"}
    )
    assert response.status_code == 401


@pytest.mark.api
def test_list_reminders_without_auth_returns_401(client):
    """Test that listing reminders requires authentication."""
    response = client.get("/api/reminders")
    assert response.status_code == 401


# =============================================================================
# Invalid Input Edge Cases
# =============================================================================

@pytest.mark.api
def test_invalid_uuid_format_returns_400_or_422(client, auth_headers):
    """Test that malformed UUID in path returns error."""
    invalid_uuid = "not-a-uuid"

    response = client.get(
        f"/api/reminders/{invalid_uuid}",
        headers=auth_headers
    )
    # Could be 404 (not found) if UUID validation happens in DB layer
    # or 400/422 if validated in path parameter
    assert response.status_code in [400, 404, 422]


@pytest.mark.api
def test_text_exceeds_max_length_handled(client, auth_headers):
    """Test that very long text (1000+ chars) is handled appropriately."""
    long_text = "a" * 1500  # Exceeds max_length=1000

    response = client.post(
        "/api/reminders",
        json={
            "text": long_text,
            "priority": "chill"
        },
        headers=auth_headers
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.api
def test_past_date_accepted_for_overdue(client, auth_headers):
    """Test that past dates are allowed (become overdue reminders)."""
    response = client.post(
        "/api/reminders",
        json={
            "text": "Overdue reminder",
            "due_date": "2020-01-01",  # Past date
            "priority": "chill"
        },
        headers=auth_headers
    )
    # Past dates should be accepted - they're just overdue
    assert response.status_code == 201


@pytest.mark.api
def test_malformed_json_returns_422(client, auth_headers):
    """Test that invalid JSON payload returns 422."""
    response = client.post(
        "/api/reminders",
        data="{invalid json syntax}",  # Malformed JSON
        headers={
            "Authorization": auth_headers["Authorization"],
            "Content-Type": "application/json"
        }
    )
    assert response.status_code == 422


@pytest.mark.api
def test_text_field_null_returns_422(client, auth_headers):
    """Test that null text field returns validation error."""
    response = client.post(
        "/api/reminders",
        json={
            "text": None,  # Null instead of string
            "priority": "chill"
        },
        headers=auth_headers
    )
    assert response.status_code == 422


# =============================================================================
# Location Validation Errors
# =============================================================================

@pytest.mark.api
def test_invalid_latitude_returns_422(client, auth_headers):
    """Test that latitude outside -90 to 90 range returns 422."""
    response = client.post(
        "/api/reminders",
        json={
            "text": "Test reminder",
            "location_name": "North Pole",
            "location_lat": 95.0,  # Invalid: > 90
            "location_lng": 0.0
        },
        headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.api
def test_invalid_longitude_returns_422(client, auth_headers):
    """Test that longitude outside -180 to 180 range returns 422."""
    response = client.post(
        "/api/reminders",
        json={
            "text": "Test reminder",
            "location_name": "International Date Line",
            "location_lat": 0.0,
            "location_lng": 190.0  # Invalid: > 180
        },
        headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.api
def test_radius_exceeds_max_returns_422(client, auth_headers):
    """Test that radius > 10km (10000m) returns 422."""
    response = client.post(
        "/api/reminders",
        json={
            "text": "Test reminder",
            "location_name": "Wide area",
            "location_lat": 40.7128,
            "location_lng": -74.0060,
            "location_radius": 60000  # 60km - exceeds max
        },
        headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.api
def test_radius_below_min_returns_422(client, auth_headers):
    """Test that radius < 10m returns 422."""
    response = client.post(
        "/api/reminders",
        json={
            "text": "Test reminder",
            "location_name": "Tiny area",
            "location_lat": 40.7128,
            "location_lng": -74.0060,
            "location_radius": 5  # 5m - below min
        },
        headers=auth_headers
    )
    assert response.status_code == 422


# =============================================================================
# Sync Error Scenarios
# =============================================================================

@pytest.mark.api
def test_sync_with_invalid_changes_format_returns_422(client, auth_headers):
    """Test that sync with malformed changes array returns 422."""
    response = client.post(
        "/api/sync",
        json={
            "client_id": "550e8400-e29b-41d4-a716-446655440000",
            "last_sync": None,
            "changes": "not-an-array"  # Should be list
        },
        headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.api
def test_sync_with_missing_client_id_returns_422(client, auth_headers):
    """Test that sync without client_id returns 422."""
    response = client.post(
        "/api/sync",
        json={
            # Missing client_id
            "last_sync": None,
            "changes": []
        },
        headers=auth_headers
    )
    assert response.status_code == 422


# =============================================================================
# Recurrence Validation Errors
# =============================================================================

@pytest.mark.api
def test_invalid_recurrence_frequency_returns_422(client, auth_headers):
    """Test that invalid recurrence frequency returns 422."""
    response = client.post(
        "/api/reminders",
        json={
            "text": "Recurring reminder",
            "recurrence_pattern": {
                "frequency": "INVALID_FREQUENCY",  # Not in allowed list
                "interval": 1
            }
        },
        headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.api
def test_recurrence_end_count_negative_returns_422(client, auth_headers):
    """Test that negative end_count returns 422."""
    response = client.post(
        "/api/reminders",
        json={
            "text": "Recurring reminder",
            "recurrence_pattern": {
                "frequency": "daily",
                "interval": 1,
                "end_count": -5  # Negative count invalid
            }
        },
        headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.api
def test_recurrence_interval_zero_returns_422(client, auth_headers):
    """Test that interval of 0 returns 422."""
    response = client.post(
        "/api/reminders",
        json={
            "text": "Recurring reminder",
            "recurrence_pattern": {
                "frequency": "weekly",
                "interval": 0  # Zero interval invalid
            }
        },
        headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.api
def test_recurrence_interval_exceeds_max_returns_422(client, auth_headers):
    """Test that interval > 365 returns 422."""
    response = client.post(
        "/api/reminders",
        json={
            "text": "Recurring reminder",
            "recurrence_pattern": {
                "frequency": "yearly",
                "interval": 500  # Exceeds max of 365
            }
        },
        headers=auth_headers
    )
    assert response.status_code == 422


# =============================================================================
# Additional Edge Cases
# =============================================================================

@pytest.mark.api
def test_update_reminder_with_invalid_priority_returns_422(client, auth_headers, created_reminder):
    """Test that updating with numeric priority (instead of string) returns 422."""
    reminder_id = created_reminder["id"]

    response = client.patch(
        f"/api/reminders/{reminder_id}",
        json={"priority": 123},  # Number instead of string
        headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.api
def test_create_reminder_with_invalid_status_returns_422(client, auth_headers):
    """Test that creating a reminder with invalid status returns 422."""
    response = client.post(
        "/api/reminders",
        json={
            "text": "Test reminder",
            "status": "in_progress"  # Not in allowed list
        },
        headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.api
def test_malformed_bearer_token_format_returns_401(client):
    """Test that malformed Authorization header (missing 'Bearer ') returns 401."""
    response = client.post(
        "/api/reminders",
        json={"text": "Test reminder"},
        headers={"Authorization": "INVALID_FORMAT"}  # Missing 'Bearer ' prefix
    )
    assert response.status_code == 401


@pytest.mark.api
def test_category_exceeds_max_length_returns_422(client, auth_headers):
    """Test that category exceeding max_length=100 returns 422."""
    long_category = "a" * 150  # Exceeds max

    response = client.post(
        "/api/reminders",
        json={
            "text": "Test reminder",
            "category": long_category
        },
        headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.api
def test_location_name_exceeds_max_length_returns_422(client, auth_headers):
    """Test that location_name exceeding max_length=500 returns 422."""
    long_location = "a" * 600  # Exceeds max

    response = client.post(
        "/api/reminders",
        json={
            "text": "Test reminder",
            "location_name": long_location
        },
        headers=auth_headers
    )
    assert response.status_code == 422
