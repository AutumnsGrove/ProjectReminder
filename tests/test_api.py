"""
API endpoint tests for the reminders system
Tests all CRUD operations and authentication
"""

import pytest
from fastapi.testclient import TestClient


# =============================================================================
# Authentication Tests
# =============================================================================

@pytest.mark.api
def test_create_reminder_without_auth_returns_401(client, sample_reminder_data):
    """Test that creating a reminder without auth returns 401"""
    response = client.post("/api/reminders", json=sample_reminder_data)
    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.api
def test_create_reminder_with_invalid_token_returns_401(client, invalid_auth_headers, sample_reminder_data):
    """Test that creating a reminder with invalid token returns 401"""
    response = client.post(
        "/api/reminders",
        headers=invalid_auth_headers,
        json=sample_reminder_data
    )
    assert response.status_code == 401


@pytest.mark.api
def test_health_check_no_auth_required(client):
    """Test that health check endpoint doesn't require authentication"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "error"]
    assert "version" in data
    assert "database" in data


# =============================================================================
# Create Operation Tests
# =============================================================================

@pytest.mark.api
def test_create_reminder_minimal_data(client, auth_headers, sample_reminder_minimal):
    """Test creating a reminder with only required fields"""
    response = client.post(
        "/api/reminders",
        headers=auth_headers,
        json=sample_reminder_minimal
    )

    assert response.status_code == 201
    data = response.json()

    # Verify required fields
    assert "id" in data
    assert data["text"] == sample_reminder_minimal["text"]
    assert data["priority"] == sample_reminder_minimal["priority"]
    assert data["status"] == "pending"

    # Verify auto-generated fields
    assert "created_at" in data
    assert "updated_at" in data

    # Verify UUID format (basic check)
    assert len(data["id"]) == 36
    assert data["id"].count("-") == 4


@pytest.mark.api
def test_create_reminder_full_data(client, auth_headers, sample_reminder_data):
    """Test creating a reminder with all fields populated"""
    response = client.post(
        "/api/reminders",
        headers=auth_headers,
        json=sample_reminder_data
    )

    assert response.status_code == 201
    data = response.json()

    # Verify all provided fields are saved
    assert data["text"] == sample_reminder_data["text"]
    assert data["priority"] == sample_reminder_data["priority"]
    assert data["category"] == sample_reminder_data["category"]
    assert data["due_date"] == sample_reminder_data["due_date"]
    assert data["due_time"] == sample_reminder_data["due_time"]
    assert data["time_required"] == sample_reminder_data["time_required"]
    assert data["location_text"] == sample_reminder_data["location_text"]


@pytest.mark.api
def test_create_reminder_generates_uuid(client, auth_headers, sample_reminder_minimal):
    """Test that creating multiple reminders generates unique UUIDs"""
    response1 = client.post("/api/reminders", headers=auth_headers, json=sample_reminder_minimal)
    response2 = client.post("/api/reminders", headers=auth_headers, json=sample_reminder_minimal)

    assert response1.status_code == 201
    assert response2.status_code == 201

    id1 = response1.json()["id"]
    id2 = response2.json()["id"]

    assert id1 != id2


@pytest.mark.api
def test_create_reminder_sets_timestamps(client, auth_headers, sample_reminder_minimal):
    """Test that created_at and updated_at are set automatically"""
    response = client.post("/api/reminders", headers=auth_headers, json=sample_reminder_minimal)

    assert response.status_code == 201
    data = response.json()

    assert data["created_at"] is not None
    assert data["updated_at"] is not None
    # Both should be approximately equal for new reminder
    assert data["created_at"] == data["updated_at"]


# =============================================================================
# Read Operation Tests
# =============================================================================

@pytest.mark.api
def test_get_reminder_by_id(client, auth_headers, created_reminder):
    """Test retrieving a single reminder by ID"""
    reminder_id = created_reminder["id"]

    response = client.get(
        f"/api/reminders/{reminder_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == reminder_id
    assert data["text"] == created_reminder["text"]


@pytest.mark.api
def test_get_reminder_not_found_returns_404(client, auth_headers):
    """Test that getting a non-existent reminder returns 404"""
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(
        f"/api/reminders/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.api
def test_list_reminders(client, auth_headers, multiple_reminders):
    """Test listing all reminders"""
    response = client.get("/api/reminders", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "pagination" in data
    assert len(data["data"]) >= 5  # At least the 5 we created
    assert data["pagination"]["total"] >= 5


@pytest.mark.api
def test_list_reminders_filter_by_status(client, auth_headers, multiple_reminders):
    """Test filtering reminders by status"""
    # Get pending reminders
    response = client.get(
        "/api/reminders?status=pending",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # All returned reminders should be pending
    for reminder in data["data"]:
        assert reminder["status"] == "pending"


@pytest.mark.api
def test_list_reminders_filter_by_priority(client, auth_headers, multiple_reminders):
    """Test filtering reminders by priority"""
    response = client.get(
        "/api/reminders?priority=urgent",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # All returned reminders should be urgent
    for reminder in data["data"]:
        assert reminder["priority"] == "urgent"


@pytest.mark.api
def test_list_reminders_pagination(client, auth_headers, multiple_reminders):
    """Test pagination parameters"""
    response = client.get(
        "/api/reminders?limit=2&offset=1",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["data"]) <= 2
    assert data["pagination"]["limit"] == 2
    assert data["pagination"]["offset"] == 1


# =============================================================================
# Update Operation Tests
# =============================================================================

@pytest.mark.api
def test_update_reminder(client, auth_headers, created_reminder):
    """Test updating a reminder"""
    reminder_id = created_reminder["id"]

    update_data = {
        "text": "Updated reminder text",
        "priority": "urgent"
    }

    response = client.patch(
        f"/api/reminders/{reminder_id}",
        headers=auth_headers,
        json=update_data
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == reminder_id
    assert data["text"] == update_data["text"]
    assert data["priority"] == update_data["priority"]
    # updated_at should change
    assert data["updated_at"] != created_reminder["updated_at"]


@pytest.mark.api
def test_update_reminder_marks_completed(client, auth_headers, created_reminder):
    """Test that updating status to completed sets completed_at timestamp"""
    reminder_id = created_reminder["id"]

    response = client.patch(
        f"/api/reminders/{reminder_id}",
        headers=auth_headers,
        json={"status": "completed"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "completed"
    assert data["completed_at"] is not None


@pytest.mark.api
def test_update_nonexistent_reminder_returns_404(client, auth_headers):
    """Test that updating a non-existent reminder returns 404"""
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = client.patch(
        f"/api/reminders/{fake_id}",
        headers=auth_headers,
        json={"text": "Updated"}
    )

    assert response.status_code == 404


# =============================================================================
# Delete Operation Tests
# =============================================================================

@pytest.mark.api
def test_delete_reminder(client, auth_headers, created_reminder):
    """Test deleting a reminder"""
    reminder_id = created_reminder["id"]

    response = client.delete(
        f"/api/reminders/{reminder_id}",
        headers=auth_headers
    )

    assert response.status_code == 204

    # Verify it's actually deleted
    get_response = client.get(
        f"/api/reminders/{reminder_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404


@pytest.mark.api
def test_delete_nonexistent_reminder_returns_404(client, auth_headers):
    """Test that deleting a non-existent reminder returns 404"""
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = client.delete(
        f"/api/reminders/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404
