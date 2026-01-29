"""
API Router for Moulinette inventory management.
Uses new hierarchical structure: Session → Inventory → Files + Audits
"""
from fastapi import APIRouter, UploadFile, File as FastAPIFile, Depends, HTTPException, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession
import pandas as pd
import numpy as np
import io

from database.session import get_db
from database import models
from schemas import inventory as schemas
from engine import InventoryEngine
from exceptions import (
    FileSizeError, FileExtensionError, DataValidationError,
    SessionNotFoundError
)
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Security constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_CSV_EXTENSIONS = ['.csv']
ALLOWED_EXCEL_EXTENSIONS = ['.xlsx', '.xls']

router = APIRouter(prefix="/inventory", tags=["Inventory"])
engine = InventoryEngine()


# === Security Helpers ===

async def validate_file_size(file: UploadFile, max_size: int = MAX_FILE_SIZE) -> bytes:
    """Validate file size and return content"""
    content = await file.read()
    if len(content) > max_size:
        logger.warning(f"File too large: {len(content)} bytes (max: {max_size})")
        raise FileSizeError(len(content), max_size)
    return content


def validate_file_extension(filename: str, allowed_extensions: list) -> None:
    """Validate file extension"""
    import os
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_extensions:
        logger.warning(f"Invalid file extension: {ext}")
        raise FileExtensionError(ext, allowed_extensions)


def safe_float(value):
    """Convert string with comma decimal separator to float"""
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    str_value = str(value).replace(',', '.')
    try:
        return float(str_value)
    except ValueError:
        import re
        match = re.search(r'-?\d+\.?\d*', str_value)
        if match:
            return float(match.group())
        return 0.0


def create_audit(db: DBSession, inventory_id: int, action: str, details: str):
    """Helper to create audit entries"""
    audit = models.InventoryAudit(
        inventoryID=inventory_id,
        actionType=action,
        details=details
    )
    db.add(audit)


def extract_sage_metadata(df_mask: pd.DataFrame) -> dict:
    """
    Extract sessionNUM, inventoryNUM, site from mask file
    
    Returns:
        dict with sessionNUM, inventoryNUM, site
    """
    # Ligne E (header) - sessionNUM in column B (index 1)
    session_line = df_mask[df_mask[0] == 'E']
    sessionNUM = session_line.iloc[0, 1] if not session_line.empty else None
    
    # Ligne L (inventory) - inventoryNUM in column C (index 2)
    inv_line = df_mask[df_mask[0] == 'L']
    inventoryNUM = inv_line.iloc[0, 2] if not inv_line.empty else None
    
    # Ligne S (stock) - site in column E (index 4)
    stock_line = df_mask[df_mask[0] == 'S']
    site = stock_line.iloc[0, 4] if not stock_line.empty else 'UNKNOWN'
    
    return {
        'sessionNUM': sessionNUM or f"AUTO_SESS_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}",
        'inventoryNUM': inventoryNUM or f"AUTO_INV_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}",
        'site': site or 'UNKNOWN'
    }


# === ENDPOINTS ===

@router.post("/upload-mask")
async def upload_mask(
    name: str = Form(...),
    depot_type: str = Form(...),
    file: UploadFile = FastAPIFile(...),
    db: DBSession = Depends(get_db)
):
    """
    Upload mask file, create session and inventory.
    Extracts sessionNUM, inventoryNUM, site from file.
    Generates template Excel for quantity input.
    """
    # Security validation
    validate_file_extension(file.filename, ALLOWED_CSV_EXTENSIONS)
    content = await validate_file_size(file)
    
    logger.info(f"Processing mask upload: {file.filename} ({len(content)} bytes)")
    
    # Parse CSV - Sage files have variable column counts per line type
    try:
        # First, find the max number of columns
        lines = content.decode('utf-8', errors='replace').split('\n')
        max_cols = max(len(line.split(';')) for line in lines if line.strip())
        
        # Read with fixed number of columns
        df_mask = pd.read_csv(
            io.BytesIO(content), 
            sep=';', 
            header=None, 
            dtype=str,
            names=range(max_cols),
            on_bad_lines='warn'
        )
    except Exception as e:
        logger.error(f"CSV parsing failed: {e}", exc_info=True)
        raise DataValidationError(f"Fichier CSV invalide : {str(e)}")
    
    # Validate structure
    if df_mask.shape[1] < 15:
        raise DataValidationError(f"Format invalide : {df_mask.shape[1]} colonnes détectées, 15 minimum requises.")
    
    # Extract Sage metadata
    metadata = extract_sage_metadata(df_mask)
    logger.info(f"Extracted metadata: {metadata}")
    
    # Validate business rules
    df_s = df_mask[df_mask[0] == 'S'].copy()
    if df_s.empty:
        raise DataValidationError("Aucune ligne de stock ('S') trouvée dans le fichier.")
    
    df_s.columns = [str(i) for i in range(len(df_s.columns))]
    errors = engine.validate_mask(df_s, depot_type)
    if errors:
        return schemas.APIResponse(status="error", message=" | ".join(errors))
    
    # Normalize depot_type to match MySQL ENUM values
    if depot_type in ["Conforme", "conforme"]:
        depot_type = "Conforme"
    elif depot_type in ["Non-Conforme", "NonConforme", "non-conforme", "Non Conforme"]:
        depot_type = "Non-Conforme"
    else:
        return schemas.APIResponse(status="error", message=f"Type de dépôt invalide : {depot_type}")
    
    # Create Session
    new_session = models.Session(
        sessionNUM=metadata['sessionNUM'],
        sessionNAME=name,
        currentStep=1,
        isCompleted=False
    )
    db.add(new_session)
    db.flush()
    
    # Create Inventory
    new_inventory = models.Inventory(
        inventoryNUM=metadata['inventoryNUM'],
        sessionID=new_session.sessionID,
        depotType=depot_type,  # Use string directly (Conforme or Non-Conforme)
        inventorySite=metadata['site'],
        isCompleted=False
    )
    db.add(new_inventory)
    db.flush()
    
    # Store mask file
    mask_filename = f"{new_session.sessionID}_{metadata['inventoryNUM']}_{metadata['site']}_MASK.csv"
    mask_file = models.File(
        inventoryID=new_inventory.inventoryID,
        fileName=mask_filename,
        fileType=models.FileType.mask,
        content=content
    )
    db.add(mask_file)
    
    # Generate template Excel
    template_bytes = engine.aggregate_for_template(df_s)
    template_filename = f"{new_session.sessionID}_{metadata['inventoryNUM']}_{metadata['site']}_TEMPLATE.xlsx"
    template_file = models.File(
        inventoryID=new_inventory.inventoryID,
        fileName=template_filename,
        fileType=models.FileType.template,
        content=template_bytes
    )
    db.add(template_file)
    
    # Create audit entries
    create_audit(db, new_inventory.inventoryID, models.AuditAction.MASK_UPLOADED, 
                 f"Mask uploaded: {file.filename}")
    create_audit(db, new_inventory.inventoryID, models.AuditAction.TEMPLATE_GENERATED,
                 f"Template generated: {template_filename}")
    
    # Update session step
    new_session.currentStep = 2
    
    db.commit()
    
    # Calculate stats
    stats = {
        "total_lines": len(df_s),
        "total_products": df_s['8'].nunique() if '8' in df_s.columns else 0,
        "total_lots": df_s['14'].nunique() if '14' in df_s.columns else 0
    }
    
    logger.info(f"Session {new_session.sessionID} created with inventory {new_inventory.inventoryID}")
    
    return schemas.MaskUploadResponse(
        status="success",
        message="Masque uploadé avec succès",
        sessionID=new_session.sessionID,
        inventoryID=new_inventory.inventoryID,
        sessionNUM=metadata['sessionNUM'],
        inventoryNUM=metadata['inventoryNUM'],
        site=metadata['site'],
        stats=stats
    )


@router.get("/download-template/{session_id}")
async def download_template(session_id: int, db: DBSession = Depends(get_db)):
    """Download Excel template for a session"""
    session = db.query(models.Session).filter(models.Session.sessionID == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    
    # Get inventory
    inventory = db.query(models.Inventory).filter(models.Inventory.sessionID == session_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventaire introuvable")
    
    # Get template file
    template_file = db.query(models.File).filter(
        models.File.inventoryID == inventory.inventoryID,
        models.File.fileType == models.FileType.template
    ).first()
    
    if not template_file:
        raise HTTPException(status_code=404, detail="Template introuvable")
    
    return StreamingResponse(
        io.BytesIO(template_file.content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={template_file.fileName}"}
    )


@router.post("/upload-filled-template/{session_id}")
async def upload_filled_template(
    session_id: int,
    file: UploadFile = FastAPIFile(...),
    db: DBSession = Depends(get_db)
):
    """
    Upload filled Excel template and generate final Sage X3 file.
    """
    # Security validation
    validate_file_extension(file.filename, ALLOWED_EXCEL_EXTENSIONS)
    content = await validate_file_size(file)
    
    logger.info(f"Processing filled template for session {session_id}: {file.filename}")
    
    # Get session and inventory
    session = db.query(models.Session).filter(models.Session.sessionID == session_id).first()
    if not session:
        raise SessionNotFoundError(session_id)
    
    inventory = db.query(models.Inventory).filter(models.Inventory.sessionID == session_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventaire introuvable")
    
    # Parse Excel
    try:
        df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
    except Exception as e:
        logger.error(f"Excel parsing failed: {e}", exc_info=True)
        raise DataValidationError(f"Erreur de lecture du fichier Excel : {str(e)}")
    
    # Validate columns (must match those generated in aggregate_for_template)
    required_cols = ['NUMERO_INVENTAIRE', 'CODE_ARTICLE', 'DEPOT', 'EMPLACEMENT', 'QUANTITE_THEORIQUE', 'QUANTITE_REELLE']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing required columns: {missing_cols}")
        raise DataValidationError(f"Colonnes manquantes : {', '.join(missing_cols)}")
    
    # Convert quantities
    df['REEL'] = df['QUANTITE_REELLE'].apply(lambda x: safe_float(x) if pd.notna(x) else 0.0)
    
    # Get mask file
    mask_file = db.query(models.File).filter(
        models.File.inventoryID == inventory.inventoryID,
        models.File.fileType == models.FileType.mask
    ).first()
    
    if not mask_file:
        raise HTTPException(status_code=404, detail="Masque original introuvable")
    
    # Read mask
    df_mask = pd.read_csv(io.BytesIO(mask_file.content), sep=';', header=None, dtype=str)
    
    # Process and distribute gaps
    df_final = engine.distribute_gaps(df_mask, df)
    
    # Generate final CSV
    final_csv = io.BytesIO()
    df_final.to_csv(final_csv, sep=';', index=False, header=False)
    final_content = final_csv.getvalue()
    
    # Store final file
    final_filename = f"{session.sessionID}_{inventory.inventoryNUM}_{inventory.inventorySite}_FINAL.csv"
    final_file = models.File(
        inventoryID=inventory.inventoryID,
        fileName=final_filename,
        fileType=models.FileType.final,
        content=final_content
    )
    db.add(final_file)
    
    # Create audit
    create_audit(db, inventory.inventoryID, models.AuditAction.FINAL_FILE_CREATED,
                 f"Final file generated: {final_filename}")
    
    # Update session and inventory
    session.currentStep = 4
    session.isCompleted = True
    inventory.isCompleted = True
    
    db.commit()
    
    logger.info(f"Final file generated for session {session_id}")
    
    return schemas.APIResponse(
        status="success",
        message="Fichier final généré avec succès",
        data={
            "fileName": final_filename,
            "sessionID": session.sessionID,
            "inventoryID": inventory.inventoryID
        }
    )


@router.get("/download-final/{session_id}")
async def download_final(session_id: int, db: DBSession = Depends(get_db)):
    """Download final Sage X3 file"""
    session = db.query(models.Session).filter(models.Session.sessionID == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    
    inventory = db.query(models.Inventory).filter(models.Inventory.sessionID == session_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventaire introuvable")
    
    final_file = db.query(models.File).filter(
        models.File.inventoryID == inventory.inventoryID,
        models.File.fileType == models.FileType.final
    ).first()
    
    if not final_file:
        raise HTTPException(status_code=404, detail="Fichier final introuvable")
    
    return StreamingResponse(
        io.BytesIO(final_file.content),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={final_file.fileName}"}
    )


@router.get("/download-file/{session_id}/{file_type}")
async def download_file(session_id: int, file_type: str, db: DBSession = Depends(get_db)):
    """
    Unified file download endpoint.
    file_type: 'mask', 'template', or 'final'
    """
    session = db.query(models.Session).filter(models.Session.sessionID == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    
    inventory = db.query(models.Inventory).filter(models.Inventory.sessionID == session_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventaire introuvable")
    
    # Map file_type string to FileType enum
    type_mapping = {
        'mask': models.FileType.mask,
        'template': models.FileType.template,
        'final': models.FileType.final
    }
    
    if file_type not in type_mapping:
        raise HTTPException(status_code=400, detail=f"Type de fichier invalide: {file_type}. Valeurs acceptées: mask, template, final")
    
    file_obj = db.query(models.File).filter(
        models.File.inventoryID == inventory.inventoryID,
        models.File.fileType == type_mapping[file_type]
    ).first()
    
    if not file_obj:
        raise HTTPException(status_code=404, detail=f"Fichier '{file_type}' introuvable")
    
    # Determine media type
    if file_type in ['mask', 'final']:
        media_type = "text/csv"
    else:  # template
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    return StreamingResponse(
        io.BytesIO(file_obj.content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={file_obj.fileName}"}
    )

@router.get("/active-sessions")
async def get_active_sessions(db: DBSession = Depends(get_db)):
    """Get all active (non-completed) sessions with their inventory info"""
    sessions = db.query(models.Session).filter(
        models.Session.isCompleted == False
    ).order_by(models.Session.createdAt.desc()).all()
    
    result = []
    for session in sessions:
        inventory = db.query(models.Inventory).filter(
            models.Inventory.sessionID == session.sessionID
        ).first()
        
        result.append({
            "id": session.sessionID,
            "name": session.sessionNAME,
            "session_num": session.sessionNUM,
            "depot_type": inventory.depotType if inventory else None,
            "status": "COMPLETE" if session.isCompleted else "IN_PROGRESS",
            "inventory_number": inventory.inventoryNUM if inventory else None,
            "site": inventory.inventorySite if inventory else None,
            "created_at": session.createdAt.isoformat() if session.createdAt else None,
            "computed_status": get_computed_status(db, session, inventory)
        })
    
    return result


def get_computed_status(db: DBSession, session: models.Session, inventory: models.Inventory) -> str:
    """Compute the current status based on available files"""
    if not inventory:
        return "NO_INVENTORY"
    
    files = db.query(models.File).filter(models.File.inventoryID == inventory.inventoryID).all()
    file_types = [f.fileType for f in files]
    
    if models.FileType.final in file_types:
        return "FINAL_READY"
    elif models.FileType.template in file_types:
        return "TEMPLATE_READY"
    elif models.FileType.mask in file_types:
        return "MASK_IMPORTED"
    
    return "CREATED"


@router.delete("/session/{session_id}")
async def delete_session(session_id: int, db: DBSession = Depends(get_db)):
    """Delete (archive) a session - cascade deletes inventory and files"""
    session = db.query(models.Session).filter(models.Session.sessionID == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    
    db.delete(session)
    db.commit()
    
    logger.info(f"Session {session_id} deleted")
    
    return schemas.APIResponse(status="success", message="Session supprimée")


@router.get("/session/{session_id}/resume")
async def resume_session(session_id: int, db: DBSession = Depends(get_db)):
    """Resume an existing session - returns data needed to continue workflow"""
    session = db.query(models.Session).filter(models.Session.sessionID == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    
    inventory = db.query(models.Inventory).filter(
        models.Inventory.sessionID == session_id
    ).first()
    
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventaire introuvable")
    
    # Get files to determine step
    files = db.query(models.File).filter(
        models.File.inventoryID == inventory.inventoryID
    ).all()
    file_types = [f.fileType for f in files]
    
    # Determine current step based on files present
    if models.FileType.final in file_types:
        step = 4  # Final file ready
    elif models.FileType.template in file_types:
        step = 3  # Template ready, waiting for filled template upload
    elif models.FileType.mask in file_types:
        step = 2  # Mask uploaded
    else:
        step = 1
    
    # Get stats from mask if available
    stats = None
    mask_file = next((f for f in files if f.fileType == models.FileType.mask), None)
    if mask_file:
        try:
            df_mask = pd.read_csv(io.BytesIO(mask_file.content), sep=';', header=None, dtype=str)
            df_s = df_mask[df_mask[0] == 'S']
            stats = {
                "total_lines": len(df_s),
                "total_products": df_s[8].nunique() if 8 in df_s.columns else 0,
                "total_lots": df_s[14].nunique() if 14 in df_s.columns else 0
            }
        except Exception as e:
            logger.error(f"Error reading mask stats: {e}")
            stats = {"total_lines": 0, "total_products": 0, "total_lots": 0}
    
    logger.info(f"Resuming session {session_id} at step {step}")
    
    return {
        "session_id": session.sessionID,
        "session_num": session.sessionNUM,
        "session_name": session.sessionNAME,
        "depot_type": inventory.depotType,
        "inventory_num": inventory.inventoryNUM,
        "site": inventory.inventorySite,
        "step": step,
        "stats": stats
    }

@router.get("/session/{session_id}/status")
async def get_session_status(session_id: int, db: DBSession = Depends(get_db)):
    """Get detailed status of a session"""
    session = db.query(models.Session).filter(models.Session.sessionID == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    
    inventory = db.query(models.Inventory).filter(
        models.Inventory.sessionID == session_id
    ).first()
    
    files = []
    stats = {}
    
    if inventory:
        db_files = db.query(models.File).filter(
            models.File.inventoryID == inventory.inventoryID
        ).all()
        files = [{"type": f.fileType.value, "name": f.fileName} for f in db_files]
        
        # Get stats from mask
        mask_file = next((f for f in db_files if f.fileType == models.FileType.mask), None)
        if mask_file:
            try:
                df_mask = pd.read_csv(io.BytesIO(mask_file.content), sep=';', header=None, dtype=str)
                df_s = df_mask[df_mask[0] == 'S']
                stats = {
                    "total_lines": len(df_s),
                    "total_products": df_s[8].nunique() if 8 in df_s.columns else 0,
                    "total_lots": df_s[14].nunique() if 14 in df_s.columns else 0
                }
            except Exception as e:
                logger.error(f"Error reading mask stats: {e}")
    
    return {
        "sessionID": session.sessionID,
        "sessionNUM": session.sessionNUM,
        "sessionNAME": session.sessionNAME,
        "currentStep": session.currentStep,
        "isCompleted": session.isCompleted,
        "inventory": {
            "inventoryID": inventory.inventoryID,
            "inventoryNUM": inventory.inventoryNUM,
            "depotType": inventory.depotType,
            "site": inventory.inventorySite,
            "isCompleted": inventory.isCompleted
        } if inventory else None,
        "files": files,
        "stats": stats,
        "computed_status": get_computed_status(db, session, inventory)
    }


@router.get("/session/{session_id}/audits")
async def get_session_audits(session_id: int, db: DBSession = Depends(get_db)):
    """Get audit trail for a session"""
    session = db.query(models.Session).filter(models.Session.sessionID == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    
    inventory = db.query(models.Inventory).filter(
        models.Inventory.sessionID == session_id
    ).first()
    
    if not inventory:
        return []
    
    audits = db.query(models.InventoryAudit).filter(
        models.InventoryAudit.inventoryID == inventory.inventoryID
    ).order_by(models.InventoryAudit.createdAt.desc()).all()
    
    return [
        {
            "id": a.id,
            "actionType": a.actionType,
            "details": a.details,
            "createdAt": a.createdAt.isoformat() if a.createdAt else None
        }
        for a in audits
    ]