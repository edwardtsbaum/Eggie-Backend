from motor.motor_asyncio import AsyncIOMotorCollection
from database.schema.user import UserInDB, UserCreate
from utils.security import get_password_hash, verify_password
from typing import Optional
from datetime import datetime
from bson import ObjectId

class UserDatabase:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create_user(self, user: UserCreate) -> UserInDB:
        """Create a new user with hashed password."""
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
        """Get user by email - privacy focused query."""
        user_dict = await self.collection.find_one({"email": email})
        if user_dict:
            # Convert ObjectId to string for Pydantic model
            user_dict["_id"] = str(user_dict["_id"])
            return UserInDB(**user_dict)
        return None

    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with email and password."""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user

    async def update_last_login(self, user_id: str):
        """Update user's last login timestamp."""
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_login": datetime.utcnow()}}
        )

    async def delete_user(self, user_id: str, current_user_email: str = None):
        """Delete user completely from database with additional validation."""
        try:
            # Additional security: Verify the user exists and get their email
            user_to_delete = await self.collection.find_one({"_id": ObjectId(user_id)})
            
            if not user_to_delete:
                raise ValueError("User not found")
            
            # Additional validation: If current_user_email is provided, verify it matches
            if current_user_email and user_to_delete.get("email") != current_user_email:
                raise ValueError("Unauthorized: Cannot delete another user's account")
            
            # Delete the user
            result = await self.collection.delete_one({"_id": ObjectId(user_id)})
            
            if result.deleted_count == 0:
                raise ValueError("Failed to delete user")
            
            return True
        except Exception as e:
            raise e