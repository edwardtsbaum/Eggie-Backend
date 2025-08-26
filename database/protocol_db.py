from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from typing import List, Optional
from datetime import datetime, date
from database.schema.protocol import Protocol, ProtocolCreate, ProtocolUpdate
from database.schema.user import PyObjectId
from database.schema.protocol import DosageEntry, Medication, DosageFrequency

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
    
    async def toggle_medication_dosage(
        self, 
        protocol_id: str, 
        user_id: str,
        medication_index: int, 
        dosage_number: int,
        new_status: bool
    ) -> bool:
        """Toggle a specific dosage status and update timestamp accordingly."""
        
        update_fields = {
            f"medications.{medication_index}.dosage_entries.{dosage_number-1}.is_taken": new_status,
            "updated_at": datetime.utcnow()
        }
        
        # If marking as taken, add timestamp. If unmarking, remove timestamp
        if new_status:
            update_fields[f"medications.{medication_index}.dosage_entries.{dosage_number-1}.time_taken"] = datetime.utcnow()
        else:
            # Remove the time_taken field when unmarking
            result = await self.collection.update_one(
                {
                    "_id": ObjectId(protocol_id),
                    "user_id": ObjectId(user_id)
                },
                {
                    "$set": update_fields,
                    "$unset": {f"medications.{medication_index}.dosage_entries.{dosage_number-1}.time_taken": ""}
                }
            )
            return result.modified_count > 0
        
        # For marking as taken, just set the fields
        result = await self.collection.update_one(
            {
                "_id": ObjectId(protocol_id),
                "user_id": ObjectId(user_id)
            },
            {"$set": update_fields}
        )
        
        return result.modified_count > 0

    async def update_medication_dosage_status(
        self, 
        protocol_id: str, 
        user_id: str,
        medication_index: int, 
        dosage_number: int,
        is_taken: bool,
        notes: Optional[str] = None
    ) -> bool:
        """Update a specific dosage status with optional notes."""
        
        update_fields = {
            f"medications.{medication_index}.dosage_entries.{dosage_number-1}.is_taken": is_taken,
            "updated_at": datetime.utcnow()
        }
        
        # Add or remove timestamp based on status
        if is_taken:
            update_fields[f"medications.{medication_index}.dosage_entries.{dosage_number-1}.time_taken"] = datetime.utcnow()
        
        # Add notes if provided
        if notes is not None:
            update_fields[f"medications.{medication_index}.dosage_entries.{dosage_number-1}.notes"] = notes
        
        # Handle unmarking (remove time_taken)
        if not is_taken:
            result = await self.collection.update_one(
                {
                    "_id": ObjectId(protocol_id),
                    "user_id": ObjectId(user_id)
                },
                {
                    "$set": update_fields,
                    "$unset": {f"medications.{medication_index}.dosage_entries.{dosage_number-1}.time_taken": ""}
                }
            )
        else:
            result = await self.collection.update_one(
                {
                    "_id": ObjectId(protocol_id),
                    "user_id": ObjectId(user_id)
                },
                {"$set": update_fields}
            )
        
        return result.modified_count > 0
    
    async def add_medication_to_protocol(
        self, 
        protocol_id: str, 
        user_id: str, 
        medication_data: dict
    ) -> bool:
        """Add a new medication to an existing protocol."""
        
        # Create dosage entries based on times_per_day
        dosage_entries = []
        for i in range(medication_data.times_per_day):
            dosage_entries.append({
                "dosage_number": i + 1,
                "dosage_amount": medication_data.dosage_amount,
                "is_taken": False,
                "time_taken": None,
                "notes": medication_data.notes or f"Dose {i + 1}"
            })
        
        # Create complete medication object
        new_medication = {
            "name": medication_data.name,
            "dosage_amount": medication_data.dosage_amount,
            "frequency": medication_data.frequency,
            "specific_days": medication_data.specific_days,
            "times_per_day": medication_data.times_per_day,
            "dosage_entries": dosage_entries,
            "notes": medication_data.notes,
            "is_active": True
        }
        
        result = await self.collection.update_one(
            {
                "_id": ObjectId(protocol_id),
                "user_id": ObjectId(user_id)
            },
            {
                "$push": {"medications": new_medication},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0

    async def update_medication_in_protocol(
        self, 
        protocol_id: str, 
        user_id: str, 
        medication_index: int,
        update_data: dict
    ) -> bool:
        """Update a specific medication in a protocol."""
        
        # Build update fields
        update_fields = {"updated_at": datetime.utcnow()}
        
        for field, value in update_data.dict(exclude_unset=True).items():
            if value is not None:
                update_fields[f"medications.{medication_index}.{field}"] = value
        
        # If times_per_day changed, regenerate dosage_entries
        if "times_per_day" in update_data.dict(exclude_unset=True):
            # Get current protocol to preserve existing dosage statuses
            protocol = await self.get_protocol_by_id(protocol_id, user_id)
            if protocol and medication_index < len(protocol.medications):
                current_medication = protocol.medications[medication_index]
                new_times_per_day = update_data.times_per_day or current_medication.times_per_day
                
                # Create new dosage entries, preserving existing ones where possible
                new_dosage_entries = []
                for i in range(new_times_per_day):
                    if i < len(current_medication.dosage_entries):
                        # Preserve existing dosage entry
                        existing_entry = current_medication.dosage_entries[i]
                        new_dosage_entries.append({
                            "dosage_number": i + 1,
                            "dosage_amount": existing_entry.dosage_amount,
                            "is_taken": existing_entry.is_taken,
                            "time_taken": existing_entry.time_taken,
                            "notes": existing_entry.notes
                        })
                    else:
                        # Create new dosage entry
                        new_dosage_entries.append({
                            "dosage_number": i + 1,
                            "dosage_amount": update_data.dosage_amount or current_medication.dosage_amount,
                            "is_taken": False,
                            "time_taken": None,
                            "notes": f"Dose {i + 1}"
                        })
                
                update_fields[f"medications.{medication_index}.dosage_entries"] = new_dosage_entries
        
        result = await self.collection.update_one(
            {
                "_id": ObjectId(protocol_id),
                "user_id": ObjectId(user_id)
            },
            {"$set": update_fields}
        )
        
        return result.modified_count > 0

    async def remove_medication_from_protocol(
        self, 
        protocol_id: str, 
        user_id: str, 
        medication_index: int
    ) -> bool:
        """Remove a medication from a protocol."""
        
        # First, get the protocol to validate the medication exists
        protocol = await self.get_protocol_by_id(protocol_id, user_id)
        if not protocol or medication_index >= len(protocol.medications):
            return False
        
        # Remove the medication at the specified index
        result = await self.collection.update_one(
            {
                "_id": ObjectId(protocol_id),
                "user_id": ObjectId(user_id)
            },
            {
                "$unset": {f"medications.{medication_index}": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        if result.modified_count > 0:
            # Clean up the array (remove null entries)
            await self.collection.update_one(
                {
                    "_id": ObjectId(protocol_id),
                    "user_id": ObjectId(user_id)
                },
                {"$pull": {"medications": None}}
            )
        
        return result.modified_count > 0

    async def add_dosage_to_medication(
        self, 
        protocol_id: str, 
        user_id: str, 
        medication_index: int,
        dosage_data: dict
    ) -> bool:
        """Add an additional dosage entry to a medication."""
        
        # Get current protocol to determine next dosage number
        protocol = await self.get_protocol_by_id(protocol_id, user_id)
        if not protocol or medication_index >= len(protocol.medications):
            return False
        
        current_medication = protocol.medications[medication_index]
        next_dosage_number = len(current_medication.dosage_entries) + 1
        
        new_dosage_entry = {
            "dosage_number": next_dosage_number,
            "dosage_amount": dosage_data.dosage_amount,
            "is_taken": False,
            "time_taken": None,
            "notes": dosage_data.notes or f"Dose {next_dosage_number}"
        }
        
        result = await self.collection.update_one(
            {
                "_id": ObjectId(protocol_id),
                "user_id": ObjectId(user_id)
            },
            {
                "$push": {f"medications.{medication_index}.dosage_entries": new_dosage_entry},
                "$inc": {f"medications.{medication_index}.times_per_day": 1},
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