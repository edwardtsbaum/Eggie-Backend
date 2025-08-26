from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from database.protocol_db import ProtocolDatabase
from database.mongo import protocols
from database.schema.protocol import ProtocolCreate, ProtocolUpdate, ProtocolResponse
from dependencies.auth import get_current_user
from database.schema.user import UserInDB
from bson import ObjectId
from datetime import datetime
from pydantic import BaseModel, Field
from database.schema.protocol import Medication, DosageFrequency

router = APIRouter(prefix="/protocols", tags=["protocols"])

def get_protocol_db() -> ProtocolDatabase:
    """Dependency to get protocol database instance."""
    return ProtocolDatabase(protocols)

@router.post("/", response_model=ProtocolResponse)
async def create_protocol(
    protocol_data: ProtocolCreate,
    current_user: UserInDB = Depends(get_current_user),
    protocol_db: ProtocolDatabase = Depends(get_protocol_db)
):
    """Create a new protocol for the current user"""
    try:
        protocol = await protocol_db.create_protocol(str(current_user.id), protocol_data)
        return ProtocolResponse(
            id=str(protocol.id),
            protocol_name=protocol.protocol_name,
            protocol_number=protocol.protocol_number,
            cycle_day_start=protocol.cycle_day_start,
            protocol_start_date=protocol.protocol_start_date,
            protocol_duration_days=protocol.protocol_duration_days,
            medications=protocol.medications,
            created_at=protocol.created_at,
            updated_at=protocol.updated_at,
            is_active=protocol.is_active
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create protocol: {str(e)}"
        )

@router.get("/", response_model=List[ProtocolResponse])
async def get_user_protocols(
    current_user: UserInDB  = Depends(get_current_user),
    protocol_db: ProtocolDatabase = Depends(get_protocol_db)
):
    """Get all protocols for the current user"""
    try:
        protocols = await protocol_db.get_user_protocols(str(current_user.id))
        return [
            ProtocolResponse(
                id=str(protocol.id),
                protocol_name=protocol.protocol_name,
                protocol_number=protocol.protocol_number,
                cycle_day_start=protocol.cycle_day_start,
                protocol_start_date=protocol.protocol_start_date,
                protocol_duration_days=protocol.protocol_duration_days,
                medications=protocol.medications,
                created_at=protocol.created_at,
                updated_at=protocol.updated_at,
                is_active=protocol.is_active
            )
            for protocol in protocols
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve protocols: {str(e)}"
        )

@router.get("/{protocol_id}", response_model=ProtocolResponse)
async def get_protocol(
    protocol_id: str,
    current_user: UserInDB = Depends(get_current_user),
    protocol_db: ProtocolDatabase = Depends(get_protocol_db)
):
    """Get a specific protocol for the current user"""
    try:
        protocol = await protocol_db.get_protocol_by_id(protocol_id, str(current_user.id))
        if not protocol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Protocol not found or you don't have permission to view it"
            )
        
        return ProtocolResponse(
            id=str(protocol.id),
            protocol_name=protocol.protocol_name,
            protocol_number=protocol.protocol_number,
            cycle_day_start=protocol.cycle_day_start,
            protocol_start_date=protocol.protocol_start_date,
            protocol_duration_days=protocol.protocol_duration_days,
            medications=protocol.medications,
            created_at=protocol.created_at,
            updated_at=protocol.updated_at,
            is_active=protocol.is_active
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve protocol: {str(e)}"
        )

@router.put("/{protocol_id}")
async def update_protocol(
    protocol_id: str,
    protocol_update: ProtocolUpdate,
    current_user: UserInDB = Depends(get_current_user),
    protocol_db: ProtocolDatabase = Depends(get_protocol_db)
):
    """Update a protocol for the current user"""
    try:
        success = await protocol_db.update_protocol(
            protocol_id,
            str(current_user.id),
            protocol_update
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Protocol not found or you don't have permission to edit it"
            )
        
        return {"message": "Protocol updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update protocol: {str(e)}"
        )

@router.delete("/{protocol_id}")
async def delete_protocol(
    protocol_id: str,
    current_user: UserInDB = Depends(get_current_user),
    protocol_db: ProtocolDatabase = Depends(get_protocol_db)
):
    """Soft delete a protocol for the current user"""
    try:
        success = await protocol_db.delete_protocol(
            protocol_id,
            str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Protocol not found or you don't have permission to delete it"
            )
        
        return {"message": "Protocol deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete protocol: {str(e)}"
        )

class MedicationAdd(BaseModel):
    name: str = Field(..., description="Medication name")
    dosage_amount: str = Field(..., description="e.g., '2 mg', '4 ml'")
    frequency: DosageFrequency = Field(..., description="How often to take")
    specific_days: Optional[List[int]] = Field(default=None)
    times_per_day: int = Field(..., description="Number of times per day")
    notes: Optional[str] = Field(default=None)

@router.post("/{protocol_id}/medications/")
async def add_medication_to_protocol(
    protocol_id: str,
    medication: MedicationAdd,
    current_user: UserInDB = Depends(get_current_user),
    protocol_db: ProtocolDatabase = Depends(get_protocol_db)
):
    """Add a new medication to an existing protocol"""
    try:
        success = await protocol_db.add_medication_to_protocol(
            protocol_id,
            str(current_user.id),
            medication
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Protocol not found or you don't have permission to edit it"
            )
        
        return {
            "message": "Medication added successfully",
            "medication_name": medication.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add medication: {str(e)}"
        )

class MedicationUpdate(BaseModel):
    name: Optional[str] = Field(default=None)
    dosage_amount: Optional[str] = Field(default=None)
    frequency: Optional[DosageFrequency] = Field(default=None)
    specific_days: Optional[List[int]] = Field(default=None)
    times_per_day: Optional[int] = Field(default=None)
    notes: Optional[str] = Field(default=None)

@router.patch("/{protocol_id}/medications/{medication_index}")
async def update_medication(
    protocol_id: str,
    medication_index: int,
    medication_update: MedicationUpdate,
    current_user: UserInDB = Depends(get_current_user),
    protocol_db: ProtocolDatabase = Depends(get_protocol_db)
):
    """Update a specific medication in a protocol"""
    try:
        success = await protocol_db.update_medication_in_protocol(
            protocol_id,
            str(current_user.id),
            medication_index,
            medication_update
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Protocol or medication not found"
            )
        
        return {"message": "Medication updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update medication: {str(e)}"
        )

@router.delete("/{protocol_id}/medications/{medication_index}")
async def remove_medication_from_protocol(
    protocol_id: str,
    medication_index: int,
    current_user: UserInDB = Depends(get_current_user),
    protocol_db: ProtocolDatabase = Depends(get_protocol_db)
):
    """Remove a medication from a protocol"""
    try:
        success = await protocol_db.remove_medication_from_protocol(
            protocol_id,
            str(current_user.id),
            medication_index
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Protocol or medication not found"
            )
        
        return {"message": "Medication removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove medication: {str(e)}"
        )

class DosageAdd(BaseModel):
    dosage_amount: str = Field(..., description="e.g., '2 mg', '4 ml'")
    notes: Optional[str] = Field(default=None)

@router.post("/{protocol_id}/medications/{medication_index}/dosages/")
async def add_dosage_to_medication(
    protocol_id: str,
    medication_index: int,
    dosage: DosageAdd,
    current_user: UserInDB = Depends(get_current_user),
    protocol_db: ProtocolDatabase = Depends(get_protocol_db)
):
    """Add an additional dosage entry to a medication"""
    try:
        success = await protocol_db.add_dosage_to_medication(
            protocol_id,
            str(current_user.id),
            medication_index,
            dosage
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Protocol or medication not found"
            )
        
        return {"message": "Dosage added successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add dosage: {str(e)}"
        )

@router.post("/{protocol_id}/medications/{medication_index}/dosage/{dosage_number}/take")
async def mark_dosage_taken(
    protocol_id: str,
    medication_index: int,
    dosage_number: int,
    current_user: UserInDB = Depends(get_current_user),
    protocol_db: ProtocolDatabase = Depends(get_protocol_db)
):
    """Mark a specific medication dosage as taken"""
    try:
        success = await protocol_db.mark_medication_dosage_taken(
            protocol_id,
            str(current_user.id),
            medication_index,
            dosage_number
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Protocol or medication not found"
            )
        
        return {"message": "Dosage marked as taken"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark dosage: {str(e)}"
        )

@router.patch("/{protocol_id}/medications/{medication_index}/dosage/{dosage_number}/toggle")
async def toggle_dosage_status(
    protocol_id: str,
    medication_index: int,
    dosage_number: int,
    current_user: UserInDB = Depends(get_current_user),
    protocol_db: ProtocolDatabase = Depends(get_protocol_db)
):
    """Toggle a medication dosage between taken/not taken"""
    try:
        # Get current protocol to check current status
        protocol = await protocol_db.get_protocol_by_id(protocol_id, str(current_user.id))
        if not protocol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Protocol not found"
            )
        
        # Validate medication_index and dosage_number
        if medication_index >= len(protocol.medications):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid medication index"
            )
        
        medication = protocol.medications[medication_index]
        if dosage_number > len(medication.dosage_entries) or dosage_number < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid dosage number"
            )
        
        # Get current status
        current_entry = medication.dosage_entries[dosage_number - 1]
        new_status = not current_entry.is_taken
        
        # Update the dosage entry
        success = await protocol_db.toggle_medication_dosage(
            protocol_id,
            str(current_user.id),
            medication_index,
            dosage_number,
            new_status
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to update dosage status"
            )
        
        action = "marked" if new_status else "unmarked"
        return {
            "message": f"Dosage {action} successfully",
            "is_taken": new_status,
            "medication_name": medication.name,
            "dosage_number": dosage_number,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle dosage: {str(e)}"
        )

@router.get("/stats/summary")
async def get_protocol_stats(
    current_user: UserInDB = Depends(get_current_user),
    protocol_db: ProtocolDatabase = Depends(get_protocol_db)
):
    """Get protocol statistics for the current user"""
    try:
        stats = await protocol_db.get_protocol_stats(str(current_user.id))
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve protocol stats: {str(e)}"
        )