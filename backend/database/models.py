"""
Database models for Moulinette application.
Hierarchical structure: Session → Inventory → Files + Audits
"""
from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, LargeBinary, Text, TIMESTAMP, func
from sqlalchemy.orm import relationship
from database.session import Base
import enum


class Session(Base):
    """
    Table des Sessions (Niveau global SESS)
    Une session contient un inventaire (workflow simple)
    """
    __tablename__ = 'sessions'
    
    sessionID = Column(Integer, primary_key=True, autoincrement=True)
    sessionNUM = Column(String(100), nullable=False, comment='Numéro de session Sage (ex: ABJ012507SES00000003)')
    sessionNAME = Column(String(100), nullable=False, comment='Nom descriptif de la session')
    currentStep = Column(Integer, default=1, comment='Étape du workflow global')
    createdAt = Column(TIMESTAMP, server_default=func.current_timestamp())
    isCompleted = Column(Boolean, default=False)
    
    # Relations
    inventories = relationship("Inventory", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Session(id={self.sessionID}, num={self.sessionNUM}, name={self.sessionNAME})>"


class DepotType(enum.Enum):
    """Type de dépôt pour l'inventaire"""
    Conforme = "Conforme"
    NonConforme = "Non-Conforme"  # Must match MySQL ENUM exactly


class Inventory(Base):
    """
    Table des Inventaires (Niveau INV)
    Un inventaire appartient à une session
    """
    __tablename__ = 'inventory'
    
    inventoryID = Column(Integer, primary_key=True, autoincrement=True)
    inventoryNUM = Column(String(100), nullable=False, comment='Numéro inventaire Sage (ex: ABJ012507INV00000004)')
    sessionID = Column(Integer, ForeignKey('sessions.sessionID', ondelete='CASCADE'), nullable=False)
    # Use String type to store enum value directly (matches MySQL ENUM)
    depotType = Column(String(20), nullable=False, comment='Type de dépôt')
    inventorySite = Column(String(100), nullable=False, comment='Site de l\'inventaire')
    createdAt = Column(TIMESTAMP, server_default=func.current_timestamp())
    isCompleted = Column(Boolean, default=False, comment='Statut de l\'inventaire')
    
    # Relations
    session = relationship("Session", back_populates="inventories")
    files = relationship("File", back_populates="inventory", cascade="all, delete-orphan")
    audits = relationship("InventoryAudit", back_populates="inventory", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Inventory(id={self.inventoryID}, num={self.inventoryNUM}, site={self.inventorySite})>"


class FileType(enum.Enum):
    """Type de fichier stocké"""
    mask = "mask"
    template = "template"
    final = "final"


class File(Base):
    """
    Table des Fichiers (Stockage binaire par inventaire)
    """
    __tablename__ = 'files'
    
    fileID = Column(Integer, primary_key=True, autoincrement=True)
    inventoryID = Column(Integer, ForeignKey('inventory.inventoryID', ondelete='CASCADE'), nullable=False)
    fileName = Column(String(255), nullable=False, comment='Nom du fichier')
    fileType = Column(Enum(FileType), nullable=False, comment='Type de fichier')
    content = Column(LargeBinary(length=(2**32)-1), nullable=False)
    createdAt = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    # Relations
    inventory = relationship("Inventory", back_populates="files")
    
    def __repr__(self):
        return f"<File(id={self.fileID}, name={self.fileName}, type={self.fileType})>"


class InventoryAudit(Base):
    """
    Table d'Audit (Traçabilité par inventaire)
    """
    __tablename__ = 'inventory_audits'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    inventoryID = Column(Integer, ForeignKey('inventory.inventoryID', ondelete='CASCADE'), nullable=False)
    actionType = Column(String(50), nullable=False, comment='Type d\'action effectuée')
    details = Column(Text, nullable=False, comment='Détails de l\'action')
    createdAt = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    # Relations
    inventory = relationship("Inventory", back_populates="audits")
    
    def __repr__(self):
        return f"<InventoryAudit(id={self.id}, type={self.actionType})>"


# Constantes pour les types d'audit
class AuditAction:
    """Constants for audit action types"""
    MASK_UPLOADED = "MASK_UPLOADED"
    TEMPLATE_GENERATED = "TEMPLATE_GENERATED"
    FINAL_FILE_CREATED = "FINAL_FILE_CREATED"
    STATUT_Q_DETECTED = "STATUT_Q_DETECTED"
    LOECART_CREATED = "LOECART_CREATED"
    GAP_DISTRIBUTED = "GAP_DISTRIBUTED"
    LOT_REDUCED_TO_ZERO = "LOT_REDUCED_TO_ZERO"