"""
Custom exceptions for the Moulinette application.
Provides specific error types for better error handling and logging.
"""
from fastapi import HTTPException, status


class MoulinetteException(HTTPException):
    """Base exception for all Moulinette errors"""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class FileValidationError(MoulinetteException):
    """Raised when file validation fails (size, extension, format)"""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class FileSizeError(FileValidationError):
    """Raised when file exceeds maximum size"""
    def __init__(self, size: int, max_size: int):
        detail = f"Fichier trop volumineux ({size // (1024*1024)}MB). Taille maximale: {max_size // (1024*1024)}MB"
        super().__init__(detail=detail)


class FileExtensionError(FileValidationError):
    """Raised when file has invalid extension"""
    def __init__(self, extension: str, allowed: list):
        detail = f"Extension '{extension}' invalide. Extensions autorisées: {', '.join(allowed)}"
        super().__init__(detail=detail)


class DataValidationError(MoulinetteException):
    """Raised when data validation fails (missing columns, invalid values)"""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class SessionNotFoundError(MoulinetteException):
    """Raised when session is not found in database"""
    def __init__(self, session_id: int):
        super().__init__(
            detail=f"Session {session_id} introuvable",
            status_code=status.HTTP_404_NOT_FOUND
        )


class FileNotFoundError(MoulinetteException):
    """Raised when file is not found in database"""
    def __init__(self, file_type: str, session_id: int):
        super().__init__(
            detail=f"Fichier {file_type} introuvable pour la session {session_id}",
            status_code=status.HTTP_404_NOT_FOUND
        )


class BusinessRuleError(MoulinetteException):
    """Raised when business rule validation fails"""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class DepotTypeError(BusinessRuleError):
    """Raised when depot type is incompatible with data"""
    def __init__(self, depot_type: str, incompatible_status: str):
        detail = f"Incompatibilité : Dépôt {depot_type} choisi mais lots {incompatible_status} détectés"
        super().__init__(detail=detail)
