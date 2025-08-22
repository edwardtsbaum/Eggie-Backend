from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from database.protocol_db import ProtocolDatabase
from database.mongo import protocols
from database.schema.protocol import ProtocolCreate, ProtocolUpdate, ProtocolResponse
from dependencies.auth import get_current_user
from database.schema.user import UserInDB
from bson import ObjectId

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