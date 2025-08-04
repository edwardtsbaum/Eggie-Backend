from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database.user_db import UserDatabase
from database.mongo import database
from models.user import UserInDB
from utils.security import get_current_user_email
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
    """Get current authenticated user."""
    token = credentials.credentials
    email = get_current_user_email(token)
    
    user = await user_db.get_user_by_email(email)
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

async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_current_verified_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """Get current verified user."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return current_user 