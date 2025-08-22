from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from typing import List, Optional
from datetime import datetime, date
from database.schema.protocol import Protocol, ProtocolCreate, ProtocolUpdate
from schema.user import PyObjectId

class ProtocolDatabase:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
    
    async def create_protocol(self, user_id: str, protocol_data: ProtocolCreate) -> Protocol:
        """Create a new protocol with auto-generated naming"""
        # Get user's existing protocol count
        user_protocol_count = await self.collection.count_documents({
            "user_id": ObjectId(user_id),
            "is_active": True
        })
        protocol_number = user_protocol_count + 1
        
        # Generate protocol name
        current_date = datetime.now().strftime("%Y-%m-%d")
        protocol_name = f"Protocol: {current_date} - {protocol_number:02d}"
        
        # Create protocol
        protocol = Protocol(
            user_id=ObjectId(user_id),
            protocol_name=protocol_name,
            protocol_number=protocol_number,
            **protocol_data.dict()
        )
        
        result = await self.collection.insert_one(protocol.dict(by_alias=True))
        protocol.id = result.inserted_id
        return protocol
    
    async def get_user_protocols(self, user_id: str) -> List[Protocol]:
        """Get all protocols for a specific user"""
        cursor = self.collection.find({
            "user_id": ObjectId(user_id),
            "is_active": True
        }).sort("created_at", -1)  # Most recent first
        
        protocols = await cursor.to_list(None)
        return [Protocol(**protocol) for protocol in protocols]
    
    async def get_protocol_by_id(self, protocol_id: str, user_id: str) -> Optional[Protocol]:
        """Get a specific protocol for a user (ensures user isolation)"""
        protocol = await self.collection.find_one({
            "_id": ObjectId(protocol_id),
            "user_id": ObjectId(user_id),
            "is_active": True
        })
        return Protocol(**protocol) if protocol else None
    
    async def update_protocol(self, protocol_id: str, user_id: str, update_data: ProtocolUpdate) -> bool:
        """Update a protocol (ensures user can only update their own)"""
        update_data.updated_at = datetime.utcnow()
        
        result = await self.collection.update_one(
            {
                "_id": ObjectId(protocol_id),
                "user_id": ObjectId(user_id)
            },
            {"$set": {k: v for k, v in update_data.dict().items() if v is not None}}
        )
        
        return result.modified_count > 0
    
    async def delete_protocol(self, protocol_id: str, user_id: str) -> bool:
        """Soft delete a protocol (ensures user can only delete their own)"""
        result = await self.collection.update_one(
            {
                "_id": ObjectId(protocol_id),
                "user_id": ObjectId(user_id)
            },
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        
        return result.modified_count > 0
    
    async def mark_medication_dosage_taken(
        self, 
        protocol_id: str, 
        user_id: str,
        medication_index: int, 
        dosage_number: int
    ) -> bool:
        """Mark a specific dosage as taken (ensures user isolation)"""
        result = await self.collection.update_one(
            {
                "_id": ObjectId(protocol_id),
                "user_id": ObjectId(user_id)
            },
            {
                "$set": {
                    f"medications.{medication_index}.dosage_entries.{dosage_number-1}.is_taken": True,
                    f"medications.{medication_index}.dosage_entries.{dosage_number-1}.time_taken": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    async def add_medication_to_protocol(
        self, 
        protocol_id: str, 
        user_id: str, 
        medication: dict
    ) -> bool:
        """Add a medication to an existing protocol"""
        result = await self.collection.update_one(
            {
                "_id": ObjectId(protocol_id),
                "user_id": ObjectId(user_id)
            },
            {
                "$push": {"medications": medication},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0
    
    async def get_protocol_stats(self, user_id: str) -> dict:
        """Get protocol statistics for a user"""
        total_protocols = await self.collection.count_documents({
            "user_id": ObjectId(user_id),
            "is_active": True
        })
        
        active_protocols = await self.collection.count_documents({
            "user_id": ObjectId(user_id),
            "is_active": True,
            "protocol_start_date": {"$lte": date.today()},
            "$expr": {
                "$gte": [
                    {"$add": ["$protocol_start_date", {"$multiply": ["$protocol_duration_days", 24*60*60*1000]}]},
                    datetime.now()
                ]
            }
        })
        
        return {
            "total_protocols": total_protocols,
            "active_protocols": active_protocols,
            "completed_protocols": total_protocols - active_protocols
        }