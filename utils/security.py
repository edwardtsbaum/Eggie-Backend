import bcrypt
from datetime import datetime, timedelta
import jwt
from typing import Optional, Dict, Tuple
import os
from fastapi import HTTPException, status
import secrets

# Get secret key from environment
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"

# Token expiration settings for IVF app
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))  # 24 hours for mobile
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))  # 30 days for mobile

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt (legacy function)."""
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash (legacy function)."""
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    
    return bcrypt.checkpw(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "token_type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "token_type": "refresh",
        "jti": secrets.token_urlsafe(32)  # Unique token ID for revocation
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_device_token_pair(device_id: str, user_id: str, first_name: str) -> Dict[str, str]:
    """Create both access and refresh tokens for device-based auth."""
    
    # Device-based token data
    token_data = {
        "sub": device_id,  # Subject is now device_id
        "user_id": user_id,
        "first_name": first_name,
        "type": "device"
    }
    
    # Create tokens
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_HOURS * 3600,  # seconds
        "refresh_expires_in": REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600  # seconds
    }

# Legacy function (keep for backward compatibility)
def create_token_pair(user_email: str, user_id: str) -> Dict[str, str]:
    """Create both access and refresh tokens for a user (legacy email-based)."""
    
    # Common token data
    token_data = {
        "sub": user_email,
        "user_id": user_id,
        "type": "email"
    }
    
    # Create tokens
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_HOURS * 3600,  # seconds
        "refresh_expires_in": REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600  # seconds
    }

def verify_token(token: str, expected_type: str = "access") -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("token_type") != expected_type:
            return None
            
        return payload
    
    except jwt.ExpiredSignatureError:
        return None
    
    except jwt.InvalidTokenError:
        return None
    
    except Exception as e:
        print(f"Token verification error: {e}")
        return None

def verify_refresh_token(refresh_token: str) -> Optional[dict]:
    """Verify a refresh token specifically."""
    return verify_token(refresh_token, expected_type="refresh")

def refresh_device_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
    """Create a new access token from a valid device refresh token."""
    
    # Verify refresh token
    payload = verify_refresh_token(refresh_token)
    if not payload:
        return None
    
    # Extract user data
    device_id = payload.get("sub")
    user_id = payload.get("user_id")
    first_name = payload.get("first_name")
    token_type = payload.get("type")
    
    if not device_id or not user_id or token_type != "device":
        return None
    
    # Create new access token (keep same refresh token)
    token_data = {
        "sub": device_id,
        "user_id": user_id,
        "first_name": first_name,
        "type": "device"
    }
    
    new_access_token = create_access_token(token_data)
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_HOURS * 3600
    }

# Legacy refresh function
def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
    """Create a new access token from a valid refresh token (legacy email-based)."""
    
    # Verify refresh token
    payload = verify_refresh_token(refresh_token)
    if not payload:
        return None
    
    # Extract user data
    user_email = payload.get("sub")
    user_id = payload.get("user_id")
    
    if not user_email or not user_id:
        return None
    
    # Create new access token (keep same refresh token)
    token_data = {
        "sub": user_email,
        "user_id": user_id,
        "type": "email"
    }
    
    new_access_token = create_access_token(token_data)
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_HOURS * 3600
    } 