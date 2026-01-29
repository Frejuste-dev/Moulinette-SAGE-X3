from pydantic import BaseModel
from typing import Any, Optional, List

class APIResponse(BaseModel):
    status: str # "success" ou "error"
    message: str
    data: Optional[Any] = None

class InventoryValidationError(BaseModel):
    error_type: str # "STATUT_Q", "DEPOT_INCOMPATIBLE", "FORMAT_INVALID"
    message: str
    invalid_rows: Optional[List[int]] = None # Indices des lignes en faute