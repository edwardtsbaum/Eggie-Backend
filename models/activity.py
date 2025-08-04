from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from models.user import PyObjectId

class ActivityBase(BaseModel):
    activity_type: str = Field(..., description="Type of activity")
    description: str = Field(..., description="Activity description")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional activity data")

class ActivityCreate(ActivityBase):
    pass

class ActivityInDB(ActivityBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="User ID (for privacy, not exposed in responses)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = Field(default=None, description="IP address for security")
    user_agent: Optional[str] = Field(default=None, description="User agent for security")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ActivityResponse(BaseModel):
    id: str
    activity_type: str
    description: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {ObjectId: str} 