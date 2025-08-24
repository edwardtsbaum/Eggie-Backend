from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class UserMedication(BaseModel):
    id: str = Field(..., description="Medication ID as string")
    user_id: str = Field(..., description="User ID as string")
    name: str = Field(..., description="Custom medication name")
    common_dosages: List[str] = Field(default_factory=list)
    category: str = Field(..., description="User-defined category")
    description: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

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