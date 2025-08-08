import httpx
import os
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from dotenv import load_dotenv

load_dotenv()

# Facebook OAuth configuration
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")

# Google OAuth configuration (iOS only needs Client ID)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
# Note: iOS Google Sign-In doesn't use Client Secret

async def verify_facebook_token(access_token: str) -> Optional[Dict[str, Any]]:
    """Verify Facebook access token and get user data."""
    if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Facebook OAuth not configured"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            # Verify the token with Facebook
            response = await client.get(
                "https://graph.facebook.com/debug_token",
                params={
                    "input_token": access_token,
                    "access_token": f"{FACEBOOK_APP_ID}|{FACEBOOK_APP_SECRET}"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Facebook token"
                )
            
            token_data = response.json()
            if not token_data.get("data", {}).get("is_valid", False):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Facebook token"
                )
            
            # Get user data
            user_response = await client.get(
                "https://graph.facebook.com/me",
                params={
                    "access_token": access_token,
                    "fields": "id,name,email,first_name,last_name"
                }
            )
            
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not fetch Facebook user data"
                )
            
            user_data = user_response.json()
            return {
                "social_id": user_data["id"],
                "email": user_data.get("email"),
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
                "username": user_data.get("name")
            }
            
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to Facebook"
        )

async def verify_google_token(id_token: str) -> Optional[Dict[str, Any]]:
    """Verify Google ID token and get user data (iOS compatible)."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            # Verify the ID token with Google
            response = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": id_token}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google token"
                )
            
            token_data = response.json()
            
            # Verify the token was issued for our app
            if token_data.get("aud") != GOOGLE_CLIENT_ID:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google token audience"
                )
            
            return {
                "social_id": token_data["sub"],
                "email": token_data.get("email"),
                "first_name": token_data.get("given_name"),
                "last_name": token_data.get("family_name"),
                "username": token_data.get("name")
            }
            
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to Google"
        )

async def send_sms_verification(phone_number: str) -> str:
    """Send SMS verification code to phone number."""
    # In a real implementation, you would integrate with an SMS service like:
    # - Twilio
    # - AWS SNS
    # - Firebase Phone Auth
    # - SendGrid
    
    # For demo purposes, we'll return a fixed code
    # In production, generate a random 6-digit code and store it temporarily
    verification_code = "123456"
    
    # TODO: Implement actual SMS sending
    # Example with Twilio:
    # from twilio.rest import Client
    # client = Client(account_sid, auth_token)
    # message = client.messages.create(
    #     body=f"Your verification code is: {verification_code}",
    #     from_=twilio_phone_number,
    #     to=phone_number
    # )
    
    return verification_code 