from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from bson import ObjectId
from enum import Enum

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")

class AuthProvider(str, Enum):
    EMAIL = "email"
    FACEBOOK = "facebook"
    GOOGLE = "google"
    PHONE = "phone"

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    phone_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    password: Optional[str] = Field(None, min_length=8)
    auth_provider: AuthProvider = AuthProvider.EMAIL

class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    phone_number: Optional[str] = None
    auth_provider: AuthProvider = AuthProvider.EMAIL

# Social Login Models
class FacebookLogin(BaseModel):
    access_token: str

class GoogleLogin(BaseModel):
    id_token: str

class PhoneVerification(BaseModel):
    phone_number: str
    verification_code: str

class PhoneVerificationRequest(BaseModel):
    phone_number: str

class UserInDB(UserBase):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: Optional[str] = None
    auth_provider: AuthProvider = AuthProvider.EMAIL
    social_id: Optional[str] = None  # Facebook/Google user ID
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    phone_verified: bool = False

class UserResponse(UserBase):
    model_config = ConfigDict(
        json_encoders={ObjectId: str}
    )
    
    id: str
    auth_provider: AuthProvider
    is_active: bool
    is_verified: bool
    phone_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
    phone_number: Optional[str] = None 