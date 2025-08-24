from motor.motor_asyncio import AsyncIOMotorCollection
from database.schema.activity import ActivityInDB, ActivityCreate, ActivityResponse
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import Request

class ActivityDatabase:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create_activity(
        self, 
        user_id: str, 
        activity: ActivityCreate, 
        request: Optional[Request] = None
    ) -> ActivityInDB:
        """Create a new activity for a user."""
        activity_dict = activity.dict()
        activity_dict["user_id"] = ObjectId(user_id)
        activity_dict["created_at"] = datetime.utcnow()
        
        # Add security information if available
        if request:
            activity_dict["ip_address"] = self._get_client_ip(request)
            activity_dict["user_agent"] = request.headers.get("user-agent")
        
        result = await self.collection.insert_one(activity_dict)
        activity_dict["_id"] = result.inserted_id
        
        return ActivityInDB(**activity_dict)

    async def get_user_activities(
        self, 
        user_id: str, 
        limit: int = 50, 
        skip: int = 0,
        days_back: Optional[int] = None
    ) -> List[ActivityResponse]:
        """Get activities for a specific user - privacy focused."""
        query = {"user_id": ObjectId(user_id)}
        
        # Add date filter if specified
        if days_back:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            query["created_at"] = {"$gte": cutoff_date}
        
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        
        activities = []
        async for doc in cursor:
            # Convert to response model (excludes sensitive fields)
            activity = ActivityResponse(
                id=str(doc["_id"]),
                activity_type=doc["activity_type"],
                description=doc["description"],
                created_at=doc["created_at"],
                metadata=doc.get("metadata")
            )
            activities.append(activity)
        
        return activities

    async def get_activity_count(self, user_id: str, days_back: Optional[int] = None) -> int:
        """Get count of user activities - privacy focused."""
        query = {"user_id": ObjectId(user_id)}
        
        if days_back:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            query["created_at"] = {"$gte": cutoff_date}
        
        return await self.collection.count_documents(query)

    async def delete_user_activities(self, user_id: str):
        """Delete all activities for a user (for account deletion)."""
        await self.collection.delete_many({"user_id": ObjectId(user_id)})

    async def delete_old_activities(self, days_old: int = 90):
        """Delete activities older than specified days (privacy maintenance)."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        await self.collection.delete_many({"created_at": {"$lt": cutoff_date}})

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers (for proxy/load balancer setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown" 