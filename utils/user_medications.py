from bson import ObjectId
from typing import List, Optional
from database.mongo import user_medications
from database.schema.user_medications import UserMedication, UserMedicationCreate, UserMedicationUpdate
from datetime import datetime
from bson import ObjectId
from utils.mongodb_helpers import convert_documents_list

class UserMedicationDB:
    
    @staticmethod
    async def get_user_medications(user_id: str) -> List[UserMedication]:
        """Get all custom medications for a specific user"""
        cursor = user_medications.find({"user_id": ObjectId(user_id), "is_active": True})
        medications_raw = await cursor.to_list(None)
        
        # Convert ObjectId to string before creating Pydantic models
        medications = []
        for med_data in medications_raw:
            # Create a clean dict with string IDs
            clean_data = {
                "id": str(med_data["_id"]),  # Convert _id to id as string
                "user_id": str(med_data["user_id"]),  # Convert user_id to string
                "name": med_data["name"],
                "common_dosages": med_data.get("common_dosages", []),
                "category": med_data["category"],
                "description": med_data.get("description"),
                "is_active": med_data.get("is_active", True),
                "created_at": med_data["created_at"],
                "updated_at": med_data["updated_at"]
            }
            medications.append(UserMedication(**clean_data))
        
        return medications
    
    @staticmethod
    async def get_user_medication_by_id(medication_id: str, user_id: str) -> Optional[UserMedication]:
        """Get a specific custom medication for a user"""
        medication = await user_medications.find_one({
            "_id": ObjectId(medication_id),
            "user_id": ObjectId(user_id)
        })
        
        if medication:
            # Convert ObjectId fields to strings
            medication["_id"] = str(medication["_id"])
            medication["user_id"] = str(medication["user_id"])
            return UserMedication(**medication)
        
        return None
    
    @staticmethod
    async def count_user_medications(user_id: str) -> int:
        """Count how many custom medications a user has"""
        return await user_medications.count_documents({
            "user_id": ObjectId(user_id),
            "is_active": True
        })
    
    @staticmethod
    async def create_user_medication(user_id: str, medication_data: UserMedicationCreate) -> str:
        """Create a new custom medication for a user"""
        # Check if user has reached the limit
        current_count = await UserMedicationDB.count_user_medications(user_id)
        if current_count >= 30:
            raise ValueError("User has reached the maximum limit of 30 custom medications")
        
        medication = UserMedication(
            user_id=ObjectId(user_id),
            **medication_data.dict()
        )
        
        result = await user_medications.insert_one(medication.dict(by_alias=True))
        return str(result.inserted_id)
    
    @staticmethod
    async def update_user_medication(
        medication_id: str, 
        user_id: str, 
        update_data: UserMedicationUpdate
    ) -> bool:
        """Update a custom medication for a user"""
        # Only allow updates to user's own medications
        update_data.updated_at = datetime.utcnow()
        
        result = await user_medications.update_one(
            {
                "_id": ObjectId(medication_id),
                "user_id": ObjectId(user_id)
            },
            {"$set": {k: v for k, v in update_data.dict().items() if v is not None}}
        )
        
        return result.modified_count > 0
    
    @staticmethod
    async def delete_user_medication(medication_id: str, user_id: str) -> bool:
        """Soft delete a custom medication (set is_active to False)"""
        result = await user_medications.update_one(
            {
                "_id": ObjectId(medication_id),
                "user_id": ObjectId(user_id)
            },
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        
        return result.modified_count > 0
    
    @staticmethod
    async def get_all_medications_for_user(user_id: str):
        """Get both global and user-specific medications for a user"""
        from database.mongo import medication_dictionary
        
        # Get global medications
        global_cursor = medication_dictionary.find({"is_active": True})
        global_meds_raw = await global_cursor.to_list(None)
        
        # Convert ObjectId to string for JSON serialization
        global_meds = convert_documents_list(global_meds_raw)
        
        # Get user's custom medications
        user_meds = await UserMedicationDB.get_user_medications(user_id)
        
        return {
            "global_medications": global_meds,
            "user_medications": [med.dict() for med in user_meds],
            "all_medications": global_meds + [med.dict() for med in user_meds],
            "total_count": len(global_meds) + len(user_meds)
        }