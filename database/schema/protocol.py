from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, date
from bson import ObjectId
from user import PyObjectId
from enum import Enum

class DosageFrequency(str, Enum):
    DAILY = "daily"
    EVERY_OTHER_DAY = "every_other_day"
    EVERY_TWO_DAYS = "every_two_days"
    SPECIFIC_DAYS = "specific_days"

class DosageEntry(BaseModel):
    dosage_number: int = Field(..., description="Which dosage this is (1st, 2nd, 3rd)")
    dosage_amount: str = Field(..., description="e.g., '2 mg', '4 ml'")
    is_taken: bool = Field(default=False)
    time_taken: Optional[datetime] = Field(default=None)
    notes: Optional[str] = Field(default=None)

class Medication(BaseModel):
    name: str = Field(..., description="Medication name")
    dosage_amount: str = Field(..., description="e.g., '2 mg', '4 ml'")
    frequency: DosageFrequency = Field(..., description="How often to take")
    specific_days: Optional[List[int]] = Field(default=None, description="Specific cycle days if applicable")
    times_per_day: int = Field(..., description="Number of times per day")
    dosage_entries: List[DosageEntry] = Field(default_factory=list)
    notes: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)

class Protocol(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="User who owns this protocol")
    protocol_name: str = Field(..., description="Auto-generated name like 'Protocol: 2024-01-15 - 01'")
    protocol_number: int = Field(..., description="Sequential number for this user")
    cycle_day_start: int = Field(..., description="What cycle day they're starting on")
    protocol_start_date: date = Field(..., description="First day of protocol")
    protocol_duration_days: int = Field(..., description="How long the protocol lasts")
    medications: List[Medication] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# New models for API operations
class ProtocolCreate(BaseModel):
    cycle_day_start: int = Field(..., description="What cycle day they're starting on")
    protocol_start_date: date = Field(..., description="First day of protocol")
    protocol_duration_days: int = Field(..., description="How long the protocol lasts")
    medications: List[Medication] = Field(default_factory=list)

class ProtocolUpdate(BaseModel):
    cycle_day_start: Optional[int] = Field(default=None)
    protocol_start_date: Optional[date] = Field(default=None)
    protocol_duration_days: Optional[int] = Field(default=None)
    medications: Optional[List[Medication]] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)

class ProtocolResponse(BaseModel):
    id: str
    protocol_name: str
    protocol_number: int
    cycle_day_start: int
    protocol_start_date: date
    protocol_duration_days: int
    medications: List[Medication]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        json_encoders = {ObjectId: str}