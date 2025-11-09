"""
models.py - Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime
from pydantic import ConfigDict


# =============================================================================
# Request Models
# =============================================================================

# =============================================================================
# Recurrence Pattern Models (Phase 7)
# =============================================================================

class RecurrencePatternCreate(BaseModel):
    """Model for creating a recurrence pattern"""
    frequency: Literal["daily", "weekly", "monthly", "yearly"] = Field(..., description="Recurrence frequency")
    interval: int = Field(1, ge=1, le=365, description="Repeat every N days/weeks/months/years")

    # Weekly constraints
    days_of_week: Optional[str] = Field(None, description="Comma-separated days (0=Mon, 6=Sun)")

    # Monthly constraints
    day_of_month: Optional[int] = Field(None, ge=1, le=31, description="Day of month (1-31)")

    # Yearly constraints
    month_of_year: Optional[int] = Field(None, ge=1, le=12, description="Month of year (1-12)")

    # End conditions
    end_date: Optional[str] = Field(None, description="End date in ISO 8601 format (YYYY-MM-DD)")
    end_count: Optional[int] = Field(None, ge=1, description="Number of occurrences before stopping")

    class Config:
        json_schema_extra = {
            "example": {
                "frequency": "weekly",
                "interval": 1,
                "days_of_week": "0,2,4",  # Monday, Wednesday, Friday
                "end_count": 10
            }
        }


# =============================================================================
# Voice Models (Phase 8)
# =============================================================================


class VoiceTranscriptionResponse(BaseModel):
    """Response from voice transcription endpoint."""
    text: str = Field(..., description="Transcribed text from audio")
    model: str = Field(default="base.en", description="Whisper model used")
    language: str = Field(default="en", description="Language detected/used")
    file_size_bytes: int = Field(..., description="Size of uploaded audio file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Call mom about Thanksgiving",
                "model": "base.en",
                "language": "en",
                "file_size_bytes": 87432
            }
        }
    )


class RecurrencePatternResponse(BaseModel):
    """Model for recurrence pattern response"""
    id: str
    frequency: str
    interval: int = 1
    days_of_week: Optional[str] = None
    day_of_month: Optional[int] = None
    month_of_year: Optional[int] = None
    end_date: Optional[str] = None
    end_count: Optional[int] = None
    created_at: str

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "frequency": "weekly",
                "interval": 1,
                "days_of_week": "0,2,4",
                "end_count": 10,
                "created_at": "2025-11-03T10:00:00Z"
            }
        }


# =============================================================================
# Voice Models (Phase 8)
# =============================================================================


class VoiceTranscriptionResponse(BaseModel):
    """Response from voice transcription endpoint."""
    text: str = Field(..., description="Transcribed text from audio")
    model: str = Field(default="base.en", description="Whisper model used")
    language: str = Field(default="en", description="Language detected/used")
    file_size_bytes: int = Field(..., description="Size of uploaded audio file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Call mom about Thanksgiving",
                "model": "base.en",
                "language": "en",
                "file_size_bytes": 87432
            }
        }
    )


class ReminderCreate(BaseModel):
    """Model for creating a new reminder"""
    text: str = Field(..., min_length=1, max_length=1000, description="Reminder text")

    # Timing
    due_date: Optional[str] = Field(None, description="Due date in ISO 8601 format (YYYY-MM-DD)")
    due_time: Optional[str] = Field(None, description="Due time in ISO 8601 format (HH:MM:SS)")
    time_required: Optional[bool] = Field(False, description="Must be done at specific time")

    # Location
    location_name: Optional[str] = Field(None, max_length=500, description="Human-readable location name")
    location_address: Optional[str] = Field(None, max_length=1000, description="Full address from geocoding")
    location_lat: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    location_lng: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    location_radius: Optional[int] = Field(100, ge=10, le=10000, description="Trigger radius in meters")

    # Organization
    priority: Literal["someday", "chill", "important", "urgent", "waiting"] = Field("chill", description="Priority level")
    category: Optional[str] = Field(None, max_length=100, description="Category tag")

    # Status
    status: Literal["pending", "completed", "snoozed"] = Field("pending", description="Reminder status")
    snoozed_until: Optional[str] = Field(None, description="Snoozed until ISO 8601 timestamp")

    # Recurrence
    recurrence_id: Optional[str] = Field(None, description="Recurrence pattern ID")
    recurrence_pattern: Optional[RecurrencePatternCreate] = Field(None, description="Embedded recurrence pattern (creates pattern + instances)")

    # Metadata
    source: Literal["manual", "voice", "api"] = Field("manual", description="Creation source")

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        """Validate due_date is valid ISO 8601 format and represents a real date."""
        if v is None:
            return v

        # Check format and parse to verify it's a real date
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError as e:
            raise ValueError(
                f"due_date must be in ISO 8601 format (YYYY-MM-DD) and represent a valid date. "
                f"Got: '{v}'"
            ) from e

    @field_validator('due_time')
    @classmethod
    def validate_due_time(cls, v):
        """Validate due_time is valid ISO 8601 time format (HH:MM:SS)."""
        if v is None:
            return v

        try:
            datetime.strptime(v, "%H:%M:%S")
            return v
        except ValueError as e:
            raise ValueError(
                f"due_time must be in ISO 8601 format (HH:MM:SS). Got: '{v}'"
            ) from e

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Call mom about Thanksgiving",
                "due_date": "2025-11-03",
                "priority": "important",
                "category": "Calls"
            }
        }


# =============================================================================
# Voice Models (Phase 8)
# =============================================================================


class VoiceTranscriptionResponse(BaseModel):
    """Response from voice transcription endpoint."""
    text: str = Field(..., description="Transcribed text from audio")
    model: str = Field(default="base.en", description="Whisper model used")
    language: str = Field(default="en", description="Language detected/used")
    file_size_bytes: int = Field(..., description="Size of uploaded audio file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Call mom about Thanksgiving",
                "model": "base.en",
                "language": "en",
                "file_size_bytes": 87432
            }
        }
    )


class ReminderUpdate(BaseModel):
    """Model for updating an existing reminder"""
    text: Optional[str] = Field(None, min_length=1, max_length=1000)

    # Timing
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    time_required: Optional[bool] = None

    # Location
    location_name: Optional[str] = Field(None, max_length=500)
    location_address: Optional[str] = Field(None, max_length=1000)
    location_lat: Optional[float] = Field(None, ge=-90, le=90)
    location_lng: Optional[float] = Field(None, ge=-180, le=180)
    location_radius: Optional[int] = Field(None, ge=10, le=10000)

    # Organization
    priority: Optional[Literal["someday", "chill", "important", "urgent", "waiting"]] = None
    category: Optional[str] = Field(None, max_length=100)

    # Status
    status: Optional[Literal["pending", "completed", "snoozed"]] = None
    completed_at: Optional[str] = None
    snoozed_until: Optional[str] = None

    # Recurrence
    recurrence_id: Optional[str] = None

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        """Validate due_date is valid ISO 8601 format and represents a real date."""
        if v is None:
            return v

        # Check format and parse to verify it's a real date
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError as e:
            raise ValueError(
                f"due_date must be in ISO 8601 format (YYYY-MM-DD) and represent a valid date. "
                f"Got: '{v}'"
            ) from e

    @field_validator('due_time')
    @classmethod
    def validate_due_time(cls, v):
        """Validate due_time is valid ISO 8601 time format (HH:MM:SS)."""
        if v is None:
            return v

        try:
            datetime.strptime(v, "%H:%M:%S")
            return v
        except ValueError as e:
            raise ValueError(
                f"due_time must be in ISO 8601 format (HH:MM:SS). Got: '{v}'"
            ) from e

    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "completed_at": "2025-11-02T15:30:00Z"
            }
        }


# =============================================================================
# Voice Models (Phase 8)
# =============================================================================


class VoiceTranscriptionResponse(BaseModel):
    """Response from voice transcription endpoint."""
    text: str = Field(..., description="Transcribed text from audio")
    model: str = Field(default="base.en", description="Whisper model used")
    language: str = Field(default="en", description="Language detected/used")
    file_size_bytes: int = Field(..., description="Size of uploaded audio file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Call mom about Thanksgiving",
                "model": "base.en",
                "language": "en",
                "file_size_bytes": 87432
            }
        }
    )


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
    location_name: Optional[str] = None
    location_address: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    location_radius: int = 100
    distance: Optional[float] = None  # Distance in meters (calculated for location queries)

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


# =============================================================================
# Voice Models (Phase 8)
# =============================================================================


class VoiceTranscriptionResponse(BaseModel):
    """Response from voice transcription endpoint."""
    text: str = Field(..., description="Transcribed text from audio")
    model: str = Field(default="base.en", description="Whisper model used")
    language: str = Field(default="en", description="Language detected/used")
    file_size_bytes: int = Field(..., description="Size of uploaded audio file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Call mom about Thanksgiving",
                "model": "base.en",
                "language": "en",
                "file_size_bytes": 87432
            }
        }
    )


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


# =============================================================================
# Voice Models (Phase 8)
# =============================================================================


class VoiceTranscriptionResponse(BaseModel):
    """Response from voice transcription endpoint."""
    text: str = Field(..., description="Transcribed text from audio")
    model: str = Field(default="base.en", description="Whisper model used")
    language: str = Field(default="en", description="Language detected/used")
    file_size_bytes: int = Field(..., description="Size of uploaded audio file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Call mom about Thanksgiving",
                "model": "base.en",
                "language": "en",
                "file_size_bytes": 87432
            }
        }
    )


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
# Voice Models (Phase 8)
# =============================================================================


class VoiceTranscriptionResponse(BaseModel):
    """Response from voice transcription endpoint."""
    text: str = Field(..., description="Transcribed text from audio")
    model: str = Field(default="base.en", description="Whisper model used")
    language: str = Field(default="en", description="Language detected/used")
    file_size_bytes: int = Field(..., description="Size of uploaded audio file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Call mom about Thanksgiving",
                "model": "base.en",
                "language": "en",
                "file_size_bytes": 87432
            }
        }
    )


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


# =============================================================================
# Voice Models (Phase 8)
# =============================================================================


class VoiceTranscriptionResponse(BaseModel):
    """Response from voice transcription endpoint."""
    text: str = Field(..., description="Transcribed text from audio")
    model: str = Field(default="base.en", description="Whisper model used")
    language: str = Field(default="en", description="Language detected/used")
    file_size_bytes: int = Field(..., description="Size of uploaded audio file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Call mom about Thanksgiving",
                "model": "base.en",
                "language": "en",
                "file_size_bytes": 87432
            }
        }
    )


# =============================================================================
# Sync Models (Phase 5)
# =============================================================================

class SyncChange(BaseModel):
    """Model for a single sync change"""
    id: str = Field(..., description="Reminder UUID")
    action: Literal["create", "update", "delete"] = Field(..., description="Type of change")
    data: Optional[dict] = Field(None, description="Reminder data (null for delete)")
    updated_at: str = Field(..., description="ISO 8601 timestamp of change")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "action": "update",
                "data": {
                    "text": "Updated reminder text",
                    "priority": "urgent"
                },
                "updated_at": "2025-11-03T10:30:00Z"
            }
        }


# =============================================================================
# Voice Models (Phase 8)
# =============================================================================


class VoiceTranscriptionResponse(BaseModel):
    """Response from voice transcription endpoint."""
    text: str = Field(..., description="Transcribed text from audio")
    model: str = Field(default="base.en", description="Whisper model used")
    language: str = Field(default="en", description="Language detected/used")
    file_size_bytes: int = Field(..., description="Size of uploaded audio file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Call mom about Thanksgiving",
                "model": "base.en",
                "language": "en",
                "file_size_bytes": 87432
            }
        }
    )


class SyncRequest(BaseModel):
    """Model for sync request from client"""
    client_id: str = Field(..., description="Unique device identifier (UUID)")
    last_sync: Optional[str] = Field(None, description="ISO 8601 timestamp of last successful sync")
    changes: List[SyncChange] = Field(default_factory=list, description="Local changes to push to server")

    class Config:
        json_schema_extra = {
            "example": {
                "client_id": "a1b2c3d4-e5f6-4789-a012-3456789abcde",
                "last_sync": "2025-11-03T10:00:00Z",
                "changes": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "action": "update",
                        "data": {
                            "status": "completed",
                            "completed_at": "2025-11-03T10:15:00Z"
                        },
                        "updated_at": "2025-11-03T10:15:00Z"
                    }
                ]
            }
        }


# =============================================================================
# Voice Models (Phase 8)
# =============================================================================


class VoiceTranscriptionResponse(BaseModel):
    """Response from voice transcription endpoint."""
    text: str = Field(..., description="Transcribed text from audio")
    model: str = Field(default="base.en", description="Whisper model used")
    language: str = Field(default="en", description="Language detected/used")
    file_size_bytes: int = Field(..., description="Size of uploaded audio file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Call mom about Thanksgiving",
                "model": "base.en",
                "language": "en",
                "file_size_bytes": 87432
            }
        }
    )


class ConflictInfo(BaseModel):
    """Model for sync conflict information"""
    id: str = Field(..., description="Reminder UUID with conflict")
    client_updated_at: str = Field(..., description="Client's update timestamp")
    server_updated_at: str = Field(..., description="Server's update timestamp")
    resolution: Literal["server_wins", "client_wins"] = Field(..., description="How conflict was resolved")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "client_updated_at": "2025-11-03T10:15:00Z",
                "server_updated_at": "2025-11-03T10:20:00Z",
                "resolution": "server_wins"
            }
        }


# =============================================================================
# Voice Models (Phase 8)
# =============================================================================


class VoiceTranscriptionResponse(BaseModel):
    """Response from voice transcription endpoint."""
    text: str = Field(..., description="Transcribed text from audio")
    model: str = Field(default="base.en", description="Whisper model used")
    language: str = Field(default="en", description="Language detected/used")
    file_size_bytes: int = Field(..., description="Size of uploaded audio file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Call mom about Thanksgiving",
                "model": "base.en",
                "language": "en",
                "file_size_bytes": 87432
            }
        }
    )


class SyncResponse(BaseModel):
    """Model for sync response from server"""
    server_changes: List[SyncChange] = Field(default_factory=list, description="Changes from server since last sync")
    conflicts: List[ConflictInfo] = Field(default_factory=list, description="Conflicts detected and resolved")
    last_sync: str = Field(..., description="ISO 8601 timestamp to use for next sync request")
    applied_count: int = Field(..., description="Number of client changes successfully applied")

    class Config:
        json_schema_extra = {
            "example": {
                "server_changes": [
                    {
                        "id": "660e8400-e29b-41d4-a716-446655440001",
                        "action": "create",
                        "data": {
                            "text": "New reminder from other device",
                            "priority": "chill",
                            "status": "pending",
                            "created_at": "2025-11-03T10:25:00Z",
                            "updated_at": "2025-11-03T10:25:00Z"
                        },
                        "updated_at": "2025-11-03T10:25:00Z"
                    }
                ],
                "conflicts": [],
                "last_sync": "2025-11-03T10:30:00Z",
                "applied_count": 1
            }
        }


# =============================================================================
# Voice Models (Phase 8)
# =============================================================================


class VoiceTranscriptionResponse(BaseModel):
    """Response from voice transcription endpoint."""
    text: str = Field(..., description="Transcribed text from audio")
    model: str = Field(default="base.en", description="Whisper model used")
    language: str = Field(default="en", description="Language detected/used")
    file_size_bytes: int = Field(..., description="Size of uploaded audio file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Call mom about Thanksgiving",
                "model": "base.en",
                "language": "en",
                "file_size_bytes": 87432
            }
        }
    )


# =============================================================================
# NLP Parsing Models (Phase 8.1)
# =============================================================================


class ReminderParseRequest(BaseModel):
    """Request for parsing natural language reminder text."""
    text: str = Field(..., min_length=1, max_length=1000, description="Reminder text to parse")
    mode: Literal["auto", "local", "cloud"] = Field("auto", description="Parsing mode selection")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Call mom tomorrow at 3pm, this is urgent",
                "mode": "auto"
            }
        }
    )


class ReminderParseResponse(BaseModel):
    """Response from reminder text parsing endpoint."""
    text: str = Field(..., description="Cleaned reminder text")
    due_date: Optional[str] = Field(None, description="Extracted due date (YYYY-MM-DD)")
    due_time: Optional[str] = Field(None, description="Extracted due time (HH:MM:SS)")
    time_required: bool = Field(False, description="Is specific time required?")
    priority: Optional[str] = Field(None, description="Extracted priority level")
    category: Optional[str] = Field(None, description="Inferred category")
    location: Optional[str] = Field(None, description="Extracted location")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score (0.0-1.0)")
    parse_mode: Literal["local", "cloud"] = Field(..., description="Mode used for parsing")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Call mom",
                "due_date": "2025-11-05",
                "due_time": "15:00:00",
                "time_required": True,
                "priority": "urgent",
                "category": "Calls",
                "location": None,
                "confidence": 0.95,
                "parse_mode": "local"
            }
        }
    )
