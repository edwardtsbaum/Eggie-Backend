from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from database.user_db import UserDatabase
from database.mongo import database
from models.user import (
    UserCreate, UserLogin, UserResponse, Token, 
    FacebookLogin, GoogleLogin, PhoneVerification, PhoneVerificationRequest,
    AuthProvider
)
from utils.security import create_access_token, create_access_token_for_user
from utils.social_auth import verify_facebook_token, verify_google_token, send_sms_verification
from dependencies.auth import get_user_db, get_current_user
from datetime import timedelta
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
            auth_provider=created_user.auth_provider,
            is_active=created_user.is_active,
            is_verified=created_user.is_verified,
            phone_verified=created_user.phone_verified,
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
    if user_credentials.auth_provider != AuthProvider.EMAIL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use appropriate endpoint for this auth provider"
        )
    
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

@router.post("/facebook", response_model=Token)
async def facebook_login(
    facebook_data: FacebookLogin,
    user_db: UserDatabase = Depends(get_user_db)
):
    """Login with Facebook access token."""
    # Verify Facebook token and get user data
    user_data = await verify_facebook_token(facebook_data.access_token)
    
    # Authenticate or create user
    user = await user_db.authenticate_social_user(
        user_data["social_id"], 
        AuthProvider.FACEBOOK, 
        user_data
    )
    
    # Update last login
    await user_db.update_last_login(str(user.id))
    
    # Create access token
    access_token = create_access_token_for_user(user.email or user.phone_number, "email")
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/google", response_model=Token)
async def google_login(
    google_data: GoogleLogin,
    user_db: UserDatabase = Depends(get_user_db)
):
    """Login with Google ID token."""
    # Verify Google token and get user data
    user_data = await verify_google_token(google_data.id_token)
    
    # Authenticate or create user
    user = await user_db.authenticate_social_user(
        user_data["social_id"], 
        AuthProvider.GOOGLE, 
        user_data
    )
    
    # Update last login
    await user_db.update_last_login(str(user.id))
    
    # Create access token
    access_token = create_access_token_for_user(user.email or user.phone_number, "email")
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/phone/request", response_model=dict)
async def request_phone_verification(
    phone_request: PhoneVerificationRequest,
    user_db: UserDatabase = Depends(get_user_db)
):
    """Request SMS verification code for phone number."""
    # Create or get user by phone number
    user = await user_db.create_or_get_phone_user(phone_request.phone_number)
    
    # Send verification code
    verification_code = await send_sms_verification(phone_request.phone_number)
    
    # In production, store the verification code securely with expiration
    # For demo, we're using a fixed code "123456"
    
    return {
        "message": "Verification code sent",
        "phone_number": phone_request.phone_number,
        "demo_code": "123456"  # Remove this in production
    }

@router.post("/phone/verify", response_model=Token)
async def verify_phone_code(
    phone_verification: PhoneVerification,
    user_db: UserDatabase = Depends(get_user_db)
):
    """Verify phone number with SMS code and return access token."""
    user = await user_db.authenticate_phone_user(
        phone_verification.phone_number,
        phone_verification.verification_code
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification code",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    await user_db.update_last_login(str(user.id))
    
    # Create access token
    access_token = create_access_token_for_user(user.phone_number, "phone")
    
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
        auth_provider=current_user.auth_provider,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        phone_verified=current_user.phone_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

@router.post("/logout")
async def logout_user():
    """Logout user (client should discard token)."""
    # In a stateless JWT system, logout is handled client-side
    # by discarding the token. This endpoint can be used for
    # logging purposes or future token blacklisting.
    return {"message": "Successfully logged out"}

@router.delete("/account")
async def delete_account(
    current_user = Depends(get_current_user),
    user_db: UserDatabase = Depends(get_user_db)
):
    """Delete user account completely."""
    await user_db.delete_user(str(current_user.id))
    return {"message": "Account deleted successfully"} 