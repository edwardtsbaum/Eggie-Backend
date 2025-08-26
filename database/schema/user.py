from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Annotated, Union
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        """Pydantic V2 compatible schema generation."""
        from pydantic_core import core_schema
        
        return core_schema.union_schema([
            # Accept ObjectId instances directly
            core_schema.is_instance_schema(ObjectId),
            # Accept strings and convert them
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate)
            ])
        ])
    
    @classmethod
    def validate(cls, v):
        """Validate and convert value to ObjectId."""
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            if not ObjectId.is_valid(v):
                raise ValueError("Invalid ObjectId string")
            return ObjectId(v)
        raise ValueError(f"Invalid ObjectId format: expected string or ObjectId, got {type(v)}")

# New simplified device-based user models
class UserCreateDevice(BaseModel):
    """Ultra-simple device registration - just name and device ID."""
    first_name: str = Field(..., min_length=1, max_length=50, description="User's first name")
    device_id: str = Field(..., min_length=10, description="Unique device identifier")

class UserInDB(BaseModel):
    """User as stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    first_name: str
    username: str  # Auto-generated from first_name
    device_id: str
    
    # Optional backup fields (added later in settings)
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    backup_enabled: bool = False
    
    # System fields
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = None
    
    model_config = {
        "validate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class UserResponse(BaseModel):
    """User data returned to client."""
    id: str
    first_name: str
    username: str
    device_id: str
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    backup_enabled: bool
    is_active: bool
    created_at: datetime
    last_active: Optional[datetime] = None
    
    model_config = {
        "json_encoders": {ObjectId: str}
    }

# Backup settings models
class BackupSettings(BaseModel):
    """Settings for data backup."""
    phone_number: str = Field(..., min_length=10, max_length=15, description="Phone number for backup")

class BackupResponse(BaseModel):
    """Response after setting up backup."""
    backup_enabled: bool
    phone_number: str
    message: str

# Legacy models (keep for backward compatibility during transition)
class UserCreate(BaseModel):
    """Legacy email/password registration (deprecated)."""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    """Legacy email/password login (deprecated)."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

# Token models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenData(BaseModel):
    device_id: Optional[str] = None  # Changed from email to device_id
    user_id: Optional[str] = None