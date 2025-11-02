"""
models.py - Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime


# =============================================================================
# Request Models
# =============================================================================

class ReminderCreate(BaseModel):
    """Model for creating a new reminder"""
    text: str = Field(..., min_length=1, max_length=1000, description="Reminder text")

    # Timing
    due_date: Optional[str] = Field(None, description="Due date in ISO 8601 format (YYYY-MM-DD)")
    due_time: Optional[str] = Field(None, description="Due time in ISO 8601 format (HH:MM:SS)")
    time_required: Optional[bool] = Field(False, description="Must be done at specific time")

    # Location
    location_text: Optional[str] = Field(None, max_length=500, description="Human-readable location")
    location_lat: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    location_lng: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    location_radius: Optional[int] = Field(100, ge=10, le=10000, description="Trigger radius in meters")

    # Organization
    priority: Literal["chill", "important", "urgent"] = Field("chill", description="Priority level")
    category: Optional[str] = Field(None, max_length=100, description="Category tag")

    # Status
    status: Literal["pending", "completed", "snoozed"] = Field("pending", description="Reminder status")
    snoozed_until: Optional[str] = Field(None, description="Snoozed until ISO 8601 timestamp")

    # Recurrence
    recurrence_id: Optional[str] = Field(None, description="Recurrence pattern ID")

    # Metadata
    source: Literal["manual", "voice", "api"] = Field("manual", description="Creation source")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Call mom about Thanksgiving",
                "due_date": "2025-11-03",
                "priority": "important",
                "category": "Calls"
            }
        }


class ReminderUpdate(BaseModel):
    """Model for updating an existing reminder"""
    text: Optional[str] = Field(None, min_length=1, max_length=1000)

    # Timing
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    time_required: Optional[bool] = None

    # Location
    location_text: Optional[str] = Field(None, max_length=500)
    location_lat: Optional[float] = Field(None, ge=-90, le=90)
    location_lng: Optional[float] = Field(None, ge=-180, le=180)
    location_radius: Optional[int] = Field(None, ge=10, le=10000)

    # Organization
    priority: Optional[Literal["chill", "important", "urgent"]] = None
    category: Optional[str] = Field(None, max_length=100)

    # Status
    status: Optional[Literal["pending", "completed", "snoozed"]] = None
    completed_at: Optional[str] = None
    snoozed_until: Optional[str] = None

    # Recurrence
    recurrence_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "completed_at": "2025-11-02T15:30:00Z"
            }
        }


# =============================================================================
# Response Models
# =============================================================================

class ReminderResponse(BaseModel):
    """Model for reminder response"""
    id: str
    text: str

    # Timing
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    time_required: bool = False

    # Location
    location_text: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    location_radius: int = 100

    # Organization
    priority: str = "chill"
    category: Optional[str] = None

    # Status
    status: str = "pending"
    completed_at: Optional[str] = None
    snoozed_until: Optional[str] = None

    # Recurrence
    recurrence_id: Optional[str] = None

    # Metadata
    source: str = "manual"
    created_at: str
    updated_at: str
    synced_at: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "text": "Call mom about Thanksgiving",
                "due_date": "2025-11-03",
                "priority": "important",
                "category": "Calls",
                "status": "pending",
                "source": "manual",
                "created_at": "2025-11-02T10:00:00Z",
                "updated_at": "2025-11-02T10:00:00Z"
            }
        }


class PaginationMetadata(BaseModel):
    """Pagination metadata"""
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Number of items skipped")
    returned: int = Field(..., description="Number of items in current page")


class ReminderListResponse(BaseModel):
    """Model for list of reminders with pagination"""
    data: List[ReminderResponse]
    pagination: PaginationMetadata

    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "text": "Call mom",
                        "priority": "important",
                        "category": "Calls",
                        "status": "pending",
                        "created_at": "2025-11-02T10:00:00Z",
                        "updated_at": "2025-11-02T10:00:00Z"
                    }
                ],
                "pagination": {
                    "total": 1,
                    "limit": 100,
                    "offset": 0,
                    "returned": 1
                }
            }
        }


class HealthResponse(BaseModel):
    """Model for health check response"""
    status: Literal["ok", "error"] = "ok"
    version: str = "1.0.0"
    database: Literal["connected", "disconnected"] = "connected"
    timestamp: str

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "version": "1.0.0",
                "database": "connected",
                "timestamp": "2025-11-02T10:00:00Z"
            }
        }


# =============================================================================
# Error Models
# =============================================================================

class ErrorResponse(BaseModel):
    """Model for error responses"""
    detail: str = Field(..., description="Error message")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Reminder not found"
            }
        }
