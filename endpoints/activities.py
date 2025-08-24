from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional
from database.activity_db import ActivityDatabase
from database.mongo import database
from database.schema.activity import ActivityCreate, ActivityResponse
from dependencies.auth import get_current_user
from database.schema.user import UserInDB

router = APIRouter(prefix="/activities", tags=["activities"])

def get_activity_db() -> ActivityDatabase:
    """Dependency to get activity database instance."""
    return ActivityDatabase(database.user_activities)

@router.get("/", response_model=List[ActivityResponse])
async def get_my_activities(
    limit: int = 50,
    skip: int = 0,
    days_back: Optional[int] = None,
    current_user: UserInDB = Depends(get_current_user),
    activity_db: ActivityDatabase = Depends(get_activity_db)
):
    """Get current user's activities - privacy focused."""
    if limit > 100:
        limit = 100  # Prevent excessive data retrieval
    
    activities = await activity_db.get_user_activities(
        user_id=str(current_user.id),
        limit=limit,
        skip=skip,
        days_back=days_back
    )
    
    return activities

@router.get("/count")
async def get_activity_count(
    days_back: Optional[int] = None,
    current_user: UserInDB = Depends(get_current_user),
    activity_db: ActivityDatabase = Depends(get_activity_db)
):
    """Get count of current user's activities."""
    count = await activity_db.get_activity_count(
        user_id=str(current_user.id),
        days_back=days_back
    )
    
    return {"count": count}

@router.post("/", response_model=ActivityResponse)
async def create_activity(
    activity: ActivityCreate,
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
    activity_db: ActivityDatabase = Depends(get_activity_db)
):
    """Create a new activity for current user."""
    created_activity = await activity_db.create_activity(
        user_id=str(current_user.id),
        activity=activity,
        request=request
    )
    
    return ActivityResponse(
        id=str(created_activity.id),
        activity_type=created_activity.activity_type,
        description=created_activity.description,
        created_at=created_activity.created_at,
        metadata=created_activity.metadata
    )

@router.delete("/")
async def delete_my_activities(
    current_user: UserInDB = Depends(get_current_user),
    activity_db: ActivityDatabase = Depends(get_activity_db)
):
    """Delete all activities for current user."""
    await activity_db.delete_user_activities(str(current_user.id))
    return {"message": "All activities deleted successfully"} 