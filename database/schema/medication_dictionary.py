from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId
from models.user import PyObjectId

class MedicationDictionary(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., description="Standard medication name")
    common_dosages: List[str] = Field(default_factory=list, description="Common dosage forms")
    category: str = Field(..., description="e.g., 'Estrogen', 'Progesterone', 'Antihistamine'")
    description: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}