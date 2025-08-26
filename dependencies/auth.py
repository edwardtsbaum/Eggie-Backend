from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database.user_db import UserDatabase
from database.mongo import database
from database.schema.user import UserInDB
from utils.security import verify_token
from typing import Optional

# Security scheme for JWT tokens
security = HTTPBearer()

def get_user_db() -> UserDatabase:
    """Dependency to get user database instance."""
    return UserDatabase(database.users)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_db: UserDatabase = Depends(get_user_db)
) -> UserInDB:
    """Get current authenticated user (supports both device and email auth)."""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get subject (device_id or email) and auth type
    subject = payload.get("sub")
    auth_type = payload.get("type", "email")  # Default to email for backward compatibility
    user_id = payload.get("user_id")
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Authenticate based on type
    user = None
    if auth_type == "device":
        user = await user_db.get_user_by_device_id(subject)
    elif auth_type == "email":
        user = await user_db.get_user_by_email(subject)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

# Optional: Specific device auth dependency
async def get_current_device_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_db: UserDatabase = Depends(get_user_db)
) -> UserInDB:
    """Get current authenticated user specifically for device-based auth."""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None or payload.get("type") != "device":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    device_id = payload.get("sub")
    
    if not device_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await user_db.get_user_by_device_id(device_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive device",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user