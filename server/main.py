"""
main.py - FastAPI application entry point

ADHD-Friendly Voice Reminders System
Phase 1: Core Backend REST API
"""

from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from typing import Optional, List
import uuid

from . import config
from . import database as db
from .models import (
    ReminderCreate,
    ReminderUpdate,
    ReminderResponse,
    ReminderListResponse,
    PaginationMetadata,
    HealthResponse,
    ErrorResponse
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

    Args:
        reminder: Reminder data

    Returns:
        Created reminder with generated ID and timestamps
    """
    try:
        # Generate ID and timestamps
        reminder_id = generate_uuid()
        current_time = get_current_timestamp()

        # Build reminder data dictionary
        reminder_data = {
            "id": reminder_id,
            "text": reminder.text,
            "due_date": reminder.due_date,
            "due_time": reminder.due_time,
            "time_required": 1 if reminder.time_required else 0,
            "location_text": reminder.location_text,
            "location_lat": reminder.location_lat,
            "location_lng": reminder.location_lng,
            "location_radius": reminder.location_radius,
            "priority": reminder.priority,
            "category": reminder.category,
            "status": reminder.status,
            "completed_at": None,
            "snoozed_until": reminder.snoozed_until,
            "recurrence_id": reminder.recurrence_id,
            "source": reminder.source,
            "created_at": current_time,
            "updated_at": current_time,
            "synced_at": None
        }

        # Create in database
        db.create_reminder(reminder_data)

        # Return created reminder
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
