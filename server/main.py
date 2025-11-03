"""
main.py - FastAPI application entry point

ADHD-Friendly Voice Reminders System
Phase 1: Core Backend REST API
"""

from fastapi import FastAPI, Depends, HTTPException, Header, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from typing import Optional, List
import uuid
import math
import os
import tempfile

from . import config
from . import database as db
from .models import (
    ReminderCreate,
    ReminderUpdate,
    ReminderResponse,
    ReminderListResponse,
    PaginationMetadata,
    HealthResponse,
    ErrorResponse,
    SyncRequest,
    SyncResponse,
    SyncChange,
    ConflictInfo,
    RecurrencePatternCreate,
    RecurrencePatternResponse,
    VoiceTranscriptionResponse
)


# =============================================================================
# FastAPI App Initialization
# =============================================================================

app = FastAPI(
    title="ADHD-Friendly Reminders API",
    description="Offline-first reminders system with voice input support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Authentication
# =============================================================================

async def verify_token(authorization: str = Header(None)) -> str:
    """
    Verify bearer token authentication.

    Args:
        authorization: Authorization header (Bearer TOKEN)

    Returns:
        Token if valid

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header. Use: Bearer YOUR_TOKEN"
        )

    token = authorization.replace("Bearer ", "")

    if not config.API_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="Server configuration error: API_TOKEN not set"
        )

    if token != config.API_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid API token"
        )

    return token


# =============================================================================
# Utility Functions
# =============================================================================

def get_current_timestamp() -> str:
    """Get current timestamp in ISO 8601 format"""
    return datetime.now(timezone.utc).isoformat()


def generate_uuid() -> str:
    """Generate a new UUID v4"""
    return str(uuid.uuid4())


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.

    Args:
        lat1: Latitude of first point (degrees)
        lng1: Longitude of first point (degrees)
        lat2: Latitude of second point (degrees)
        lng2: Longitude of second point (degrees)

    Returns:
        Distance in meters
    """
    # Earth's radius in meters
    R = 6371000

    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# =============================================================================
# Health Check Endpoint (No Authentication Required)
# =============================================================================

@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check endpoint"
)
async def health_check():
    """
    Check API health and database connectivity.

    Returns:
        Health status with version and database connectivity
    """
    try:
        # Test database connectivity
        db.count_reminders()
        database_status = "connected"
        status = "ok"
    except Exception as e:
        database_status = "disconnected"
        status = "error"

    return HealthResponse(
        status=status,
        version="1.0.0",
        database=database_status,
        timestamp=get_current_timestamp()
    )


# =============================================================================
# CRUD Endpoints (All Require Authentication)
# =============================================================================

@app.post(
    "/api/reminders",
    response_model=ReminderResponse,
    status_code=201,
    tags=["Reminders"],
    summary="Create a new reminder",
    dependencies=[Depends(verify_token)]
)
async def create_reminder(reminder: ReminderCreate):
    """
    Create a new reminder.

    Requires authentication via Bearer token.

    If recurrence_pattern is provided, creates the pattern and generates
    recurring instances for the next 90 days.

    Args:
        reminder: Reminder data

    Returns:
        Created reminder with generated ID and timestamps
        (Note: For recurring reminders, returns the first instance)
    """
    try:
        # Generate ID and timestamps
        reminder_id = generate_uuid()
        current_time = get_current_timestamp()

        # Handle recurrence pattern if provided
        pattern_id = reminder.recurrence_id
        if reminder.recurrence_pattern:
            # Create recurrence pattern
            pattern_id = generate_uuid()
            db.create_recurrence_pattern(
                pattern_id=pattern_id,
                frequency=reminder.recurrence_pattern.frequency,
                interval=reminder.recurrence_pattern.interval,
                days_of_week=reminder.recurrence_pattern.days_of_week,
                day_of_month=reminder.recurrence_pattern.day_of_month,
                month_of_year=reminder.recurrence_pattern.month_of_year,
                end_date=reminder.recurrence_pattern.end_date,
                end_count=reminder.recurrence_pattern.end_count
            )

        # Build reminder data dictionary
        reminder_data = {
            "id": reminder_id,
            "text": reminder.text,
            "due_date": reminder.due_date,
            "due_time": reminder.due_time,
            "time_required": 1 if reminder.time_required else 0,
            "location_name": reminder.location_name,
            "location_address": reminder.location_address,
            "location_lat": reminder.location_lat,
            "location_lng": reminder.location_lng,
            "location_radius": reminder.location_radius,
            "priority": reminder.priority,
            "category": reminder.category,
            "status": reminder.status,
            "completed_at": None,
            "snoozed_until": reminder.snoozed_until,
            "recurrence_id": pattern_id,
            "source": reminder.source,
            "created_at": current_time,
            "updated_at": current_time,
            "synced_at": None
        }

        # If recurrence pattern exists, generate instances instead of single reminder
        if reminder.recurrence_pattern and pattern_id:
            pattern_dict = db.get_recurrence_pattern(pattern_id)
            if pattern_dict:
                # Generate recurring instances (90 days ahead)
                generated_ids = db.generate_recurrence_instances(
                    base_reminder=reminder_data,
                    pattern=pattern_dict,
                    horizon_days=90
                )

                # Return the first generated instance
                if generated_ids:
                    first_instance = db.get_reminder(generated_ids[0])
                    if first_instance:
                        return ReminderResponse(**first_instance)

        # No recurrence - create single reminder
        db.create_reminder(reminder_data)
        return ReminderResponse(**reminder_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create reminder: {str(e)}")


@app.get(
    "/api/reminders",
    response_model=ReminderListResponse,
    tags=["Reminders"],
    summary="List reminders with filters",
    dependencies=[Depends(verify_token)]
)
async def list_reminders(
    status: Optional[str] = Query(None, description="Filter by status (pending, completed, snoozed)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority (chill, important, urgent)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    List reminders with optional filters and pagination.

    Requires authentication via Bearer token.

    Args:
        status: Filter by status
        category: Filter by category
        priority: Filter by priority
        limit: Maximum results per page
        offset: Number of results to skip

    Returns:
        List of reminders with pagination metadata
    """
    try:
        # Get reminders from database
        reminders = db.get_all_reminders(
            status=status,
            category=category,
            priority=priority,
            limit=limit,
            offset=offset
        )

        # Get total count
        total_count = db.count_reminders(
            status=status,
            category=category,
            priority=priority
        )

        # Convert to response models
        reminder_responses = [ReminderResponse(**reminder) for reminder in reminders]

        # Build pagination metadata
        pagination = PaginationMetadata(
            total=total_count,
            limit=limit,
            offset=offset,
            returned=len(reminder_responses)
        )

        return ReminderListResponse(
            data=reminder_responses,
            pagination=pagination
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list reminders: {str(e)}")


# =============================================================================
# Location Endpoints (Phase 6)
# =============================================================================

@app.get(
    "/api/reminders/near-location",
    response_model=ReminderListResponse,
    tags=["Location"],
    summary="Find reminders near a location",
    dependencies=[Depends(verify_token)]
)
async def get_reminders_near_location(
    lat: float = Query(..., ge=-90, le=90, description="Latitude of search location"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude of search location"),
    radius: int = Query(1000, ge=10, le=50000, description="Search radius in meters (default: 1000m)")
):
    """
    Find reminders near a specific location.

    Uses Haversine formula to calculate distances between search location
    and reminder locations. Returns all reminders within the specified radius,
    sorted by distance (nearest first).

    Requires authentication via Bearer token.

    Args:
        lat: Latitude of search location
        lng: Longitude of search location
        radius: Search radius in meters (10m - 50km)

    Returns:
        List of reminders within radius, sorted by distance
    """
    try:
        # Get all reminders with location data
        all_reminders = db.get_all_reminders(limit=10000)

        # Filter reminders with valid location coordinates
        reminders_with_location = [
            r for r in all_reminders
            if r.get('location_lat') is not None and r.get('location_lng') is not None
        ]

        # Calculate distances and filter by radius
        nearby_reminders = []
        for reminder in reminders_with_location:
            distance = haversine_distance(
                lat, lng,
                reminder['location_lat'], reminder['location_lng']
            )

            # Check if within reminder's configured radius (or search radius, whichever is larger)
            reminder_radius = reminder.get('location_radius', 100)
            effective_radius = max(radius, reminder_radius)

            if distance <= effective_radius:
                # Add distance metadata for sorting
                reminder['distance'] = round(distance, 2)
                nearby_reminders.append(reminder)

        # Sort by distance (nearest first)
        nearby_reminders.sort(key=lambda r: r['distance'])

        # Convert to response models
        reminder_responses = [ReminderResponse(**r) for r in nearby_reminders]

        # Build pagination metadata
        pagination = PaginationMetadata(
            total=len(reminder_responses),
            limit=len(reminder_responses),
            offset=0,
            returned=len(reminder_responses)
        )

        return ReminderListResponse(
            data=reminder_responses,
            pagination=pagination
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find nearby reminders: {str(e)}")


@app.post(
    "/api/voice/transcribe",
    response_model=VoiceTranscriptionResponse,
    tags=["Voice"],
    summary="Transcribe audio to text",
    description="Upload audio file (WebM/MP4/WAV) and receive transcribed text using Whisper.cpp"
)
async def transcribe_voice(
    audio: UploadFile = File(..., description="Audio file (WebM/MP4/WAV, max 10MB)"),
    token: str = Depends(verify_token)
):
    """
    Transcribe audio file to text using local Whisper.cpp.

    Requires bearer token authentication.
    Accepts audio files up to 10MB.
    Processing time: typically 2-8 seconds for 5-30 second audio.
    """
    temp_path = None

    try:
        # Validate content type
        if not audio.content_type or not audio.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content type: {audio.content_type}. Expected audio/*"
            )

        # Determine file extension from content type
        ext_map = {
            'audio/webm': '.webm',
            'audio/mp4': '.mp4',
            'audio/x-m4a': '.m4a',
            'audio/wav': '.wav',
            'audio/x-wav': '.wav',
            'audio/mpeg': '.mp3'
        }
        ext = ext_map.get(audio.content_type, '.webm')

        # Save uploaded file to temp directory
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            temp_path = tmp.name
            content = await audio.read()
            tmp.write(content)

        # Validate file size
        file_size = os.path.getsize(temp_path)
        if file_size > 10 * 1024 * 1024:  # 10MB max
            raise HTTPException(
                status_code=413,
                detail="Audio file too large (max 10MB)"
            )

        if file_size < 1024:  # 1KB min
            raise HTTPException(
                status_code=400,
                detail="Audio file too small (min 1KB)"
            )

        # Transcribe using Whisper.cpp
        from server.voice.whisper import transcribe_audio
        text = transcribe_audio(temp_path)

        return VoiceTranscriptionResponse(
            text=text,
            model="base.en",
            language="en",
            file_size_bytes=file_size
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except RuntimeError as e:
        # Whisper-specific errors
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Voice transcription service not configured. Contact administrator."
            )
        elif "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=504,
                detail="Transcription timeout. Try a shorter recording."
            )
        elif "No speech detected" in error_msg or "No transcription found" in error_msg:
            raise HTTPException(
                status_code=422,
                detail="No speech detected in audio. Please speak louder and try again."
            )
        else:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {error_msg}")

    except Exception as e:
        # Unexpected errors
        print(f"Unexpected transcription error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during transcription"
        )

    finally:
        # Cleanup temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"Warning: Failed to cleanup temp file {temp_path}: {e}")


@app.get(
    "/api/reminders/{reminder_id}",
    response_model=ReminderResponse,
    tags=["Reminders"],
    summary="Get a single reminder by ID",
    dependencies=[Depends(verify_token)],
    responses={404: {"model": ErrorResponse, "description": "Reminder not found"}}
)
async def get_reminder(reminder_id: str):
    """
    Get a single reminder by ID.

    Requires authentication via Bearer token.

    Args:
        reminder_id: Reminder UUID

    Returns:
        Reminder data

    Raises:
        404: If reminder not found
    """
    try:
        reminder = db.get_reminder_by_id(reminder_id)

        if not reminder:
            raise HTTPException(status_code=404, detail="Reminder not found")

        return ReminderResponse(**reminder)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get reminder: {str(e)}")


@app.patch(
    "/api/reminders/{reminder_id}",
    response_model=ReminderResponse,
    tags=["Reminders"],
    summary="Update a reminder",
    dependencies=[Depends(verify_token)],
    responses={404: {"model": ErrorResponse, "description": "Reminder not found"}}
)
async def update_reminder(reminder_id: str, update: ReminderUpdate):
    """
    Update a reminder.

    Requires authentication via Bearer token.

    Args:
        reminder_id: Reminder UUID
        update: Fields to update

    Returns:
        Updated reminder data

    Raises:
        404: If reminder not found
    """
    try:
        # Check if reminder exists
        existing = db.get_reminder_by_id(reminder_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Reminder not found")

        # Build update dictionary (only include non-None fields)
        update_data = update.model_dump(exclude_unset=True)

        # Always update the updated_at timestamp
        update_data["updated_at"] = get_current_timestamp()

        # Special handling: if status is being set to 'completed', set completed_at
        if update_data.get("status") == "completed" and not update_data.get("completed_at"):
            update_data["completed_at"] = get_current_timestamp()

        # Handle boolean conversion for time_required
        if "time_required" in update_data:
            update_data["time_required"] = 1 if update_data["time_required"] else 0

        # Update in database
        success = db.update_reminder(reminder_id, update_data)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update reminder")

        # Fetch and return updated reminder
        updated_reminder = db.get_reminder_by_id(reminder_id)
        return ReminderResponse(**updated_reminder)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update reminder: {str(e)}")


@app.delete(
    "/api/reminders/{reminder_id}",
    status_code=204,
    tags=["Reminders"],
    summary="Delete a reminder",
    dependencies=[Depends(verify_token)],
    responses={404: {"model": ErrorResponse, "description": "Reminder not found"}}
)
async def delete_reminder(reminder_id: str):
    """
    Delete a reminder.

    Requires authentication via Bearer token.

    Args:
        reminder_id: Reminder UUID

    Returns:
        204 No Content on success

    Raises:
        404: If reminder not found
    """
    try:
        # Check if reminder exists
        existing = db.get_reminder_by_id(reminder_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Reminder not found")

        # Delete from database
        success = db.delete_reminder(reminder_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete reminder")

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete reminder: {str(e)}")


# =============================================================================
# Sync Endpoint (Phase 5)
# =============================================================================

@app.post(
    "/api/sync",
    response_model=SyncResponse,
    tags=["Sync"],
    summary="Synchronize reminders between client and server",
    dependencies=[Depends(verify_token)]
)
async def sync_reminders(sync_request: SyncRequest):
    """
    Bidirectional sync endpoint for offline-first synchronization.

    This endpoint:
    1. Accepts client changes (creates, updates, deletes)
    2. Applies client changes to server database
    3. Detects and resolves conflicts (last-write-wins)
    4. Returns server changes since client's last sync

    Requires authentication via Bearer token.

    Args:
        sync_request: Sync request with client_id, last_sync, and changes

    Returns:
        Server changes, conflicts, and new last_sync timestamp
    """
    try:
        current_time = get_current_timestamp()
        conflicts: List[ConflictInfo] = []
        applied_count = 0

        # Step 1: Apply client changes to server
        for change in sync_request.changes:
            try:
                # Check if reminder exists on server
                existing = db.get_reminder_by_id(change.id)

                # Detect conflicts (both client and server modified same reminder)
                if change.action == "update" and existing:
                    client_updated_at = change.updated_at
                    server_updated_at = existing.get("updated_at")

                    # Conflict: both updated since last sync
                    if server_updated_at and client_updated_at:
                        # Last-write-wins: Compare timestamps
                        if server_updated_at > client_updated_at:
                            # Server wins - skip client change
                            conflicts.append(ConflictInfo(
                                id=change.id,
                                client_updated_at=client_updated_at,
                                server_updated_at=server_updated_at,
                                resolution="server_wins"
                            ))
                            continue
                        else:
                            # Client wins - apply change and log conflict
                            conflicts.append(ConflictInfo(
                                id=change.id,
                                client_updated_at=client_updated_at,
                                server_updated_at=server_updated_at,
                                resolution="client_wins"
                            ))

                # Apply the change
                success = db.apply_sync_change(change.id, change.action, change.data)
                if success:
                    applied_count += 1

                    # Update synced_at for this reminder
                    if change.action != "delete":
                        db.update_synced_at(change.id, current_time)

            except Exception as e:
                # Log error but continue processing other changes
                print(f"ERROR: Failed to apply change {change.id}: {e}")
                continue

        # Step 2: Get server changes since client's last sync
        server_reminders = db.get_changes_since(sync_request.last_sync)

        # Convert server reminders to SyncChange objects
        server_changes: List[SyncChange] = []
        for reminder in server_reminders:
            # Skip reminders that were just updated by this sync request
            if any(c.id == reminder["id"] for c in sync_request.changes):
                continue

            server_changes.append(SyncChange(
                id=reminder["id"],
                action="update",  # Existing reminders are always updates
                data=reminder,
                updated_at=reminder["updated_at"]
            ))

        # Step 3: Update synced_at for all reminders sent to client
        reminder_ids = [change.id for change in server_changes]
        if reminder_ids:
            db.batch_update_synced_at(reminder_ids, current_time)

        # Step 4: Return sync response
        return SyncResponse(
            server_changes=server_changes,
            conflicts=conflicts,
            last_sync=current_time,
            applied_count=applied_count
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# =============================================================================
# Config Endpoint (Phase 6)
# =============================================================================

@app.get(
    "/api/config/mapbox",
    tags=["Config"],
    summary="Get MapBox configuration"
)
async def get_mapbox_config():
    """
    Get MapBox access token for frontend.

    Does NOT require authentication (frontend needs this to initialize MapBox).

    Returns:
        MapBox access token
    """
    return {
        "mapbox_access_token": config.MAPBOX_ACCESS_TOKEN
    }


# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "ADHD-Friendly Reminders API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health"
    }
