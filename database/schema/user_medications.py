from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from models.user import PyObjectId

class UserMedication(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="Private to this user only")
    name: str = Field(..., description="Custom medication name")
    common_dosages: List[str] = Field(default_factory=list, description="Common dosage forms")
    category: str = Field(..., description="User-defined category")
    description: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class UserMedicationCreate(BaseModel):
    name: str = Field(..., description="Custom medication name")
    common_dosages: List[str] = Field(default_factory=list)
    category: str = Field(..., description="User-defined category")
    description: Optional[str] = Field(default=None)

class UserMedicationUpdate(BaseModel):
    name: Optional[str] = Field(default=None)
    common_dosages: Optional[List[str]] = Field(default=None)
    category: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)