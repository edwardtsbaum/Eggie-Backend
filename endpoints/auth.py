from fastapi import APIRouter, Depends, HTTPException, status
from database.user_db import UserDatabase
from database.schema.user import UserCreate, UserLogin, UserResponse, Token
from utils.security import create_access_token_for_user
from dependencies.auth import get_user_db, get_current_user
from typing import Optional

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
async def register_user(
    user: UserCreate,
    user_db: UserDatabase = Depends(get_user_db)
):
    """Register a new user with email/password."""
    try:
        created_user = await user_db.create_user(user)
        return UserResponse(
            id=str(created_user.id),
            email=created_user.email,
            username=created_user.username,
            phone_number=created_user.phone_number,
            first_name=created_user.first_name,
            last_name=created_user.last_name,
            is_active=created_user.is_active,
            is_verified=created_user.is_verified,
            created_at=created_user.created_at,
            last_login=created_user.last_login
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login_user(
    user_credentials: UserLogin,
    user_db: UserDatabase = Depends(get_user_db)
):
    """Login user with email/password and return access token."""
    user = await user_db.authenticate_user(
        user_credentials.email, 
        user_credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    await user_db.update_last_login(str(user.id))
    
    # Create access token
    access_token = create_access_token_for_user(user.email, "email")
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user = Depends(get_current_user)
):
    """Get current user's profile."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        phone_number=current_user.phone_number,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

@router.post("/logout")
async def logout_user():
    """Logout user (client should discard token)."""
    return {"message": "Successfully logged out"}

@router.delete("/account")
async def delete_account(
    current_user = Depends(get_current_user),
    user_db: UserDatabase = Depends(get_user_db)
):
    """Delete user account completely."""
    await user_db.delete_user(str(current_user.id))
    return {"message": "Account deleted successfully"}