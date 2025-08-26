from fastapi import APIRouter, Depends, HTTPException, status
from database.user_db import UserDatabase
from database.mongo import database
from datetime import datetime
from database.schema.user import (
    UserCreateDevice, UserCreate, UserLogin, UserResponse, 
    Token, TokenResponse, RefreshTokenRequest, BackupSettings, BackupResponse
)
from utils.security import (
    create_device_token_pair, create_token_pair, 
    refresh_device_access_token, refresh_access_token
)
from dependencies.auth import get_user_db, get_current_user, get_current_device_user

router = APIRouter(prefix="/auth", tags=["authentication"])

# NEW: Ultra-simple device-based registration
@router.post("/register/device", response_model=dict)
async def register_device(
    user: UserCreateDevice,
    user_db: UserDatabase = Depends(get_user_db)
):
    """Ultra-simple device registration - just first name and device ID."""
    try:
        created_user = await user_db.create_user_device(user)
        
        # Create device-based token pair immediately
        tokens = create_device_token_pair(
            device_id=created_user.device_id,
            user_id=str(created_user.id),
            first_name=created_user.first_name
        )
        
        return {
            "message": f"Welcome {created_user.first_name}! Your account is ready.",
            "user": UserResponse(
                id=str(created_user.id),
                first_name=created_user.first_name,
                username=created_user.username,
                device_id=created_user.device_id,
                phone_number=created_user.phone_number,
                email=created_user.email,
                backup_enabled=created_user.backup_enabled,
                is_active=created_user.is_active,
                created_at=created_user.created_at,
                last_active=created_user.last_active
            ),
            "tokens": tokens
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# NEW: Device-based authentication (auto-login)
@router.post("/authenticate/device", response_model=TokenResponse)
async def authenticate_device(
    device_data: dict,  # {"device_id": "xxx"}
    user_db: UserDatabase = Depends(get_user_db)
):
    """Authenticate user by device ID - for automatic login."""
    device_id = device_data.get("device_id")
    
    if not device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device ID is required"
        )
    
    user = await user_db.authenticate_device(device_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device not registered or inactive",
        )
    
    # Create device-based token pair
    tokens = create_device_token_pair(
        device_id=user.device_id,
        user_id=str(user.id),
        first_name=user.first_name
    )
    
    return TokenResponse(**tokens)

# NEW: Setup backup (add phone number to existing account)
@router.post("/backup/setup", response_model=BackupResponse)
async def setup_backup(
    backup_settings: BackupSettings,
    current_user = Depends(get_current_device_user),
    user_db: UserDatabase = Depends(get_user_db)
):
    """Set up phone number backup for existing device-based account."""
    try:
        updated_user = await user_db.setup_backup(str(current_user.id), backup_settings)
        
        return BackupResponse(
            backup_enabled=True,
            phone_number=updated_user.phone_number,
            message="Backup successfully enabled! Your data is now protected."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# NEW: Enhanced refresh token endpoint
@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_request: RefreshTokenRequest
):
    """Refresh access token using refresh token (supports both device and email tokens)."""
    
    # Try device-based refresh first
    new_tokens = refresh_device_access_token(refresh_request.refresh_token)
    
    # Fallback to legacy email-based refresh
    if not new_tokens:
        new_tokens = refresh_access_token(refresh_request.refresh_token)
    
    if not new_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return Token(**new_tokens)

# UPDATED: Enhanced user profile endpoint
@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user = Depends(get_current_user)
):
    """Get current user's profile (supports both device and email auth)."""
    return UserResponse(
        id=str(current_user.id),
        first_name=current_user.first_name,
        username=current_user.username,
        device_id=getattr(current_user, 'device_id', None),
        phone_number=current_user.phone_number,
        email=current_user.email,
        backup_enabled=getattr(current_user, 'backup_enabled', False),
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_active=getattr(current_user, 'last_active', None)
    )

# UPDATED: Enhanced account deletion
@router.delete("/account")
async def delete_account(
    current_user = Depends(get_current_user),
    user_db: UserDatabase = Depends(get_user_db)
):
    """Delete user account completely."""
    try:
        # Use device_id if available, otherwise fall back to email
        identifier = getattr(current_user, 'device_id', current_user.email)
        await user_db.delete_user(str(current_user.id), identifier)
        return {"message": "Account deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )

# Keep logout endpoint as-is
@router.post("/logout")
async def logout_user():
    """Logout user (client should discard tokens)."""
    return {"message": "Successfully logged out"}

# LEGACY ENDPOINTS (keep for backward compatibility)
@router.post("/register", response_model=UserResponse)
async def register_user(
    user: UserCreate,
    user_db: UserDatabase = Depends(get_user_db)
):
    """Legacy email/password registration (deprecated - use /register/device instead)."""
    try:
        created_user = await user_db.create_user(user)
        return UserResponse(
            id=str(created_user.id),
            first_name=created_user.first_name,
            username=getattr(created_user, 'username', created_user.first_name),
            device_id=getattr(created_user, 'device_id', None),
            phone_number=created_user.phone_number,
            email=created_user.email,
            backup_enabled=getattr(created_user, 'backup_enabled', False),
            is_active=created_user.is_active,
            created_at=created_user.created_at,
            last_active=getattr(created_user, 'last_active', None)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=TokenResponse)
async def login_user(
    user_credentials: UserLogin,
    user_db: UserDatabase = Depends(get_user_db)
):
    """Legacy email/password login (deprecated - use device auth instead)."""
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
    
    # Update last active (using legacy method name for compatibility)
    if hasattr(user_db, 'update_last_login'):
        await user_db.update_last_login(str(user.id))
    else:
        await user_db.update_last_active(str(user.id))
    
    # Create legacy token pair
    tokens = create_token_pair(user.credentials.email, str(user.id))
    
    return TokenResponse(**tokens)

# NEW: Recovery endpoints for backup system
@router.post("/recover/request")
async def request_account_recovery(
    recovery_data: dict,  # {"phone_number": "+1234567890"}
    user_db: UserDatabase = Depends(get_user_db)
):
    """Request account recovery using phone number."""
    phone_number = recovery_data.get("phone_number")
    
    if not phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is required"
        )
    
    user = await user_db.get_user_by_phone(phone_number)
    
    if not user or not user.backup_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with backup enabled for this phone number"
        )
    
    # TODO: In production, send SMS verification code here
    # For now, return a simple success message
    return {
        "message": "Recovery code sent to your phone number",
        "phone_number": phone_number[-4:].rjust(len(phone_number), '*'),  # Masked phone
        "next_step": "Enter the verification code to complete recovery"
    }

@router.post("/recover/verify")
async def verify_account_recovery(
    recovery_data: dict,  # {"phone_number": "+123...", "code": "123456", "new_device_id": "xxx"}
):
    """Verify recovery code and create new device token (simplified for demo)."""
    phone_number = recovery_data.get("phone_number")
    code = recovery_data.get("code") 
    new_device_id = recovery_data.get("new_device_id")
    
    if not all([phone_number, code, new_device_id]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number, verification code, and new device ID are required"
        )
    
    # TODO: In production, verify the SMS code here
    # For demo purposes, accept any 6-digit code
    if len(code) != 6 or not code.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code format"
        )
    
    user_db = UserDatabase(database.users)  # You'll need to import database
    user = await user_db.get_user_by_phone(phone_number)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Update user's device_id to the new device
    await user_db.collection.update_one(
        {"_id": user.id},
        {"$set": {"device_id": new_device_id, "last_active": datetime.utcnow()}}
    )
    
    # Create new device token for the new device
    tokens = create_device_token_pair(
        device_id=new_device_id,
        user_id=str(user.id),
        first_name=user.first_name
    )
    
    return {
        "message": f"Welcome back, {user.first_name}! Your account has been recovered.",
        "tokens": tokens
    }