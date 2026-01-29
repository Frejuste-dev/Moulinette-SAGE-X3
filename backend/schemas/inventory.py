"""
Pydantic schemas for Moulinette API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ===== Enums =====

class DepotType(str, Enum):
    """Type de dépôt"""
    Conforme = "Conforme"
    NonConforme = "Non-Conforme"


class FileType(str, Enum):
    """Type de fichier"""
    mask = "mask"
    template = "template"
    final = "final"


# ===== Session Schemas =====

class SessionCreate(BaseModel):
    """Schema for creating a new session"""
    sessionNAME: str = Field(..., description="Nom descriptif de la session")
    depotType: DepotType = Field(..., description="Type de dépôt")


class SessionResponse(BaseModel):
    """Schema for session response"""
    sessionID: int
    sessionNUM: str
    sessionNAME: str
    currentStep: int
    createdAt: datetime
    isCompleted: bool
    
    class Config:
        from_attributes = True


class SessionListItem(BaseModel):
    """Session item for list display"""
    sessionID: int
    sessionNUM: str
    sessionNAME: str
    currentStep: int
    isCompleted: bool
    depotType: Optional[str] = None
    inventorySite: Optional[str] = None
    inventoryNUM: Optional[str] = None
    createdAt: datetime
    
    class Config:
        from_attributes = True


# ===== Inventory Schemas =====

class InventoryResponse(BaseModel):
    """Schema for inventory response"""
    inventoryID: int
    inventoryNUM: str
    sessionID: int
    depotType: DepotType
    inventorySite: str
    createdAt: datetime
    isCompleted: bool
    
    class Config:
        from_attributes = True


# ===== File Schemas =====

class FileResponse(BaseModel):
    """Schema for file response (without content)"""
    fileID: int
    inventoryID: int
    fileName: str
    fileType: FileType
    createdAt: datetime
    
    class Config:
        from_attributes = True


# ===== Audit Schemas =====

class AuditResponse(BaseModel):
    """Schema for audit response"""
    id: int
    inventoryID: int
    actionType: str
    details: str
    createdAt: datetime
    
    class Config:
        from_attributes = True


# ===== Workflow Response Schemas =====

class MaskUploadResponse(BaseModel):
    """Response after mask upload"""
    status: str
    message: str
    sessionID: int
    inventoryID: int
    sessionNUM: str
    inventoryNUM: str
    site: str
    stats: dict


class APIResponse(BaseModel):
    """Generic API response"""
    status: str
    message: Optional[str] = None
    data: Optional[dict] = None