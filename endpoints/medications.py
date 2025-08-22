from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from utils.user_medications import UserMedicationDB
from database.schema.user_medications import UserMedicationCreate, UserMedicationUpdate, UserMedication
from dependencies.auth import get_current_user
from database.schema.user import UserInDB

router = APIRouter(prefix="/medications", tags=["medications"])

@router.get("/")
async def get_user_medications(current_user: UserInDB = Depends(get_current_user)):
    """Get all medications available to the current user (global + custom)"""
    try:
        medications = await UserMedicationDB.get_all_medications_for_user(str(current_user.id))
        return medications
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve medications: {str(e)}"
        )

@router.get("/custom/")
async def get_custom_medications(current_user: UserInDB = Depends(get_current_user)):
    """Get only the current user's custom medications"""
    try:
        medications = await UserMedicationDB.get_user_medications(str(current_user.id))
        return {"medications": [med.dict() for med in medications]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve custom medications: {str(e)}"
        )

@router.post("/custom/")
async def create_custom_medication(
    medication: UserMedicationCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Add a custom medication for the current user only"""
    try:
        medication_id = await UserMedicationDB.create_user_medication(
            str(current_user.id), 
            medication
        )
        return {
            "id": medication_id,
            "message": "Custom medication created successfully"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create medication: {str(e)}"
        )

@router.put("/custom/{medication_id}")
async def update_custom_medication(
    medication_id: str,
    medication_update: UserMedicationUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Update a custom medication for the current user"""
    try:
        success = await UserMedicationDB.update_user_medication(
            medication_id,
            str(current_user.id),
            medication_update
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication not found or you don't have permission to edit it"
            )
        
        return {"message": "Medication updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update medication: {str(e)}"
        )

@router.delete("/custom/{medication_id}")
async def delete_custom_medication(
    medication_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Soft delete a custom medication (set is_active to False)"""
    try:
        success = await UserMedicationDB.delete_user_medication(
            medication_id,
            str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication not found or you don't have permission to delete it"
            )
        
        return {"message": "Medication deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete medication: {str(e)}"
        )

@router.get("/custom/count")
async def get_custom_medication_count(current_user: UserInDB = Depends(get_current_user)):
    """Get the current count of custom medications for the user"""
    try:
        count = await UserMedicationDB.count_user_medications(str(current_user.id))
        return {"custom_medication_count": count, "limit": 30}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get medication count: {str(e)}"
        )
    
