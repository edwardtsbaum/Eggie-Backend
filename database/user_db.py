from motor.motor_asyncio import AsyncIOMotorCollection
from models.user import UserInDB, UserCreate, AuthProvider
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
        
        if user.phone_number:
            existing_user = await self.get_user_by_phone(user.phone_number)
            if existing_user:
                raise ValueError("User with this phone number already exists")
        
        # Create user document
        user_dict = user.dict()
        if user.password:
            user_dict["hashed_password"] = get_password_hash(user.password)
            del user_dict["password"]
        
        user_dict["created_at"] = datetime.utcnow()
        user_dict["is_active"] = True
        user_dict["is_verified"] = False
        user_dict["phone_verified"] = False
        
        # Insert into database
        result = await self.collection.insert_one(user_dict)
        user_dict["_id"] = result.inserted_id
        
        return UserInDB(**user_dict)

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email - privacy focused query."""
        user_dict = await self.collection.find_one({"email": email})
        if user_dict:
            return UserInDB(**user_dict)
        return None

    async def get_user_by_phone(self, phone_number: str) -> Optional[UserInDB]:
        """Get user by phone number - privacy focused query."""
        user_dict = await self.collection.find_one({"phone_number": phone_number})
        if user_dict:
            return UserInDB(**user_dict)
        return None

    async def get_user_by_social_id(self, social_id: str, provider: AuthProvider) -> Optional[UserInDB]:
        """Get user by social ID - privacy focused query."""
        user_dict = await self.collection.find_one({
            "social_id": social_id,
            "auth_provider": provider
        })
        if user_dict:
            return UserInDB(**user_dict)
        return None

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID - privacy focused query."""
        try:
            user_dict = await self.collection.find_one({"_id": ObjectId(user_id)})
            if user_dict:
                return UserInDB(**user_dict)
        except Exception:
            pass
        return None

    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with email and password."""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not user.hashed_password or not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    async def authenticate_social_user(self, social_id: str, provider: AuthProvider, user_data: dict) -> UserInDB:
        """Authenticate or create social login user."""
        # Check if user exists
        existing_user = await self.get_user_by_social_id(social_id, provider)
        
        if existing_user:
            # Update user info from social provider
            await self.update_social_user_info(str(existing_user.id), user_data)
            return existing_user
        else:
            # Create new user from social data
            user_dict = {
                "social_id": social_id,
                "auth_provider": provider,
                "email": user_data.get("email"),
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
                "username": user_data.get("username"),
                "is_active": True,
                "is_verified": True,  # Social users are pre-verified
                "phone_verified": False,
                "created_at": datetime.utcnow()
            }
            
            result = await self.collection.insert_one(user_dict)
            user_dict["_id"] = result.inserted_id
            
            return UserInDB(**user_dict)

    async def authenticate_phone_user(self, phone_number: str, verification_code: str) -> Optional[UserInDB]:
        """Authenticate user with phone number and verification code."""
        # In a real implementation, you'd verify the code against what was sent
        # For now, we'll use a simple verification (you should implement proper SMS verification)
        user = await self.get_user_by_phone(phone_number)
        if not user:
            return None
        
        # Simple verification (replace with actual SMS verification)
        if verification_code == "123456":  # Demo code
            await self.verify_phone_number(str(user.id))
            return user
        return None

    async def create_or_get_phone_user(self, phone_number: str) -> UserInDB:
        """Create or get user by phone number."""
        existing_user = await self.get_user_by_phone(phone_number)
        
        if existing_user:
            return existing_user
        else:
            # Create new phone user
            user_dict = {
                "phone_number": phone_number,
                "auth_provider": AuthProvider.PHONE,
                "is_active": True,
                "is_verified": False,
                "phone_verified": False,
                "created_at": datetime.utcnow()
            }
            
            result = await self.collection.insert_one(user_dict)
            user_dict["_id"] = result.inserted_id
            
            return UserInDB(**user_dict)

    async def update_social_user_info(self, user_id: str, user_data: dict):
        """Update user information from social provider."""
        update_data = {}
        if "email" in user_data:
            update_data["email"] = user_data["email"]
        if "first_name" in user_data:
            update_data["first_name"] = user_data["first_name"]
        if "last_name" in user_data:
            update_data["last_name"] = user_data["last_name"]
        if "username" in user_data:
            update_data["username"] = user_data["username"]
        
        if update_data:
            await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )

    async def verify_phone_number(self, user_id: str):
        """Mark phone number as verified."""
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"phone_verified": True, "is_verified": True}}
        )

    async def update_last_login(self, user_id: str):
        """Update user's last login timestamp."""
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_login": datetime.utcnow()}}
        )

    async def deactivate_user(self, user_id: str):
        """Deactivate a user account."""
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": False}}
        )

    async def delete_user(self, user_id: str):
        """Delete a user account completely."""
        await self.collection.delete_one({"_id": ObjectId(user_id)})

    async def get_user_activity_count(self, user_id: str) -> int:
        """Get count of user's activities - privacy focused."""
        # This is a placeholder - you'll implement activity tracking separately
        # For now, return 0 to maintain privacy
        return 0 