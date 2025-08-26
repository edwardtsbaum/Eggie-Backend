from motor.motor_asyncio import AsyncIOMotorCollection
from database.schema.user import UserInDB, UserCreateDevice, UserCreate, BackupSettings
from utils.security import get_password_hash, verify_password
from typing import Optional
from datetime import datetime
from bson import ObjectId

class UserDatabase:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create_user_device(self, user: UserCreateDevice) -> UserInDB:
        """Create a new user with device-based authentication."""
        # Check if device already exists
        existing_user = await self.get_user_by_device_id(user.device_id)
        if existing_user:
            raise ValueError("Device already registered")
        
        # Create user document
        user_dict = {
            "first_name": user.first_name.strip(),
            "username": user.first_name.strip(),  # Username = first name
            "device_id": user.device_id,
            "phone_number": None,
            "email": None,
            "backup_enabled": False,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_active": datetime.utcnow()
        }
        
        # Insert into database
        result = await self.collection.insert_one(user_dict)
        
        # Convert ObjectId to string for Pydantic model
        user_dict["_id"] = str(result.inserted_id)
        
        return UserInDB(**user_dict)

    async def get_user_by_device_id(self, device_id: str) -> Optional[UserInDB]:
        """Get user by device ID."""
        user_dict = await self.collection.find_one({"device_id": device_id})
        if user_dict:
            user_dict["_id"] = str(user_dict["_id"])
            return UserInDB(**user_dict)
        return None

    async def authenticate_device(self, device_id: str) -> Optional[UserInDB]:
        """Authenticate user by device ID."""
        user = await self.get_user_by_device_id(device_id)
        if not user or not user.is_active:
            return None
        
        # Update last active
        await self.update_last_active(str(user.id))
        return user

    async def update_last_active(self, user_id: str):
        """Update user's last active timestamp."""
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_active": datetime.utcnow()}}
        )

    async def setup_backup(self, user_id: str, backup_settings: BackupSettings) -> UserInDB:
        """Set up phone backup for existing user."""
        # Check if phone number is already used by another user
        existing_phone_user = await self.collection.find_one({
            "phone_number": backup_settings.phone_number,
            "_id": {"$ne": ObjectId(user_id)}
        })
        
        if existing_phone_user:
            raise ValueError("Phone number already registered to another account")
        
        # Update user with backup settings
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "phone_number": backup_settings.phone_number,
                "backup_enabled": True
            }}
        )
        
        # Return updated user
        user_dict = await self.collection.find_one({"_id": ObjectId(user_id)})
        user_dict["_id"] = str(user_dict["_id"])
        return UserInDB(**user_dict)

    async def get_user_by_phone(self, phone_number: str) -> Optional[UserInDB]:
        """Get user by phone number (for backup recovery)."""
        user_dict = await self.collection.find_one({"phone_number": phone_number})
        if user_dict:
            user_dict["_id"] = str(user_dict["_id"])
            return UserInDB(**user_dict)
        return None

    # Legacy methods (keep for backward compatibility)
    async def create_user(self, user: UserCreate) -> UserInDB:
        """Legacy email/password user creation (deprecated)."""
        # Check if user already exists
        if user.email:
            existing_user = await self.get_user_by_email(user.email)
            if existing_user:
                raise ValueError("User with this email already exists")
        
        # Create user document
        user_dict = user.dict()
        user_dict["hashed_password"] = get_password_hash(user.password)
        del user_dict["password"]
        
        user_dict["created_at"] = datetime.utcnow()
        user_dict["is_active"] = True
        user_dict["is_verified"] = False
        
        # Insert into database
        result = await self.collection.insert_one(user_dict)
        
        # Convert ObjectId to string for Pydantic model
        user_dict["_id"] = str(result.inserted_id)
        
        return UserInDB(**user_dict)

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email - legacy method."""
        user_dict = await self.collection.find_one({"email": email})
        if user_dict:
            user_dict["_id"] = str(user_dict["_id"])
            return UserInDB(**user_dict)
        return None

    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Legacy email/password authentication."""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not hasattr(user, 'hashed_password') or not verify_password(password, user.hashed_password):
            return None
        
        return user

    async def delete_user(self, user_id: str, current_user_device_id: str = None):
        """Delete user completely from database."""
        try:
            user_to_delete = await self.collection.find_one({"_id": ObjectId(user_id)})
            
            if not user_to_delete:
                raise ValueError("User not found")
            
            # Additional validation: If device_id is provided, verify it matches
            if current_user_device_id and user_to_delete.get("device_id") != current_user_device_id:
                raise ValueError("Unauthorized: Cannot delete another user's account")
            
            # Delete the user
            result = await self.collection.delete_one({"_id": ObjectId(user_id)})
            
            if result.deleted_count == 0:
                raise ValueError("Failed to delete user")
            
            return True
        except Exception as e:
            raise e