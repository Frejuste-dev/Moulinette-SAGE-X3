CREATE DATABASE IF NOT EXISTS moulinette_db;
USE moulinette_db;

-- 1. Table des Sessions (Niveau global SESS)
CREATE TABLE sessions (
    sessionID INT AUTO_INCREMENT PRIMARY KEY,
    sessionNUM VARCHAR(100) NOT NULL COMMENT 'Numéro de session Sage dans la ligne E du fichier colone B (ex: ABJ012507SES00000003)',
    sessionNAME VARCHAR(100) NOT NULL COMMENT 'Nom descriptif de la session dans la ligne E du fichier colone C (ex: INVENTAIRE TEST)',
    currentStep INT DEFAULT 1 COMMENT 'Étape du workflow global',
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    isCompleted BOOLEAN DEFAULT FALSE
) ENGINE=InnoDB;

-- 2. Table des Inventaires (Niveau INV - plusieurs par session)
CREATE TABLE inventory (
    inventoryID INT AUTO_INCREMENT PRIMARY KEY,
    inventoryNUM VARCHAR(100) NOT NULL COMMENT 'Numéro d''inventaire Sage dans la ligne L du fichier colone C (ex: ABJ012507INV00000004)',
    sessionID INT NOT NULL COMMENT 'Session parente',
    depotType ENUM('Conforme', 'Non-Conforme') NOT NULL COMMENT 'Type de dépôt',
    inventorySite VARCHAR(100) NOT NULL COMMENT 'Site de l''inventaire colone E du fichier Sage',
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    isCompleted BOOLEAN DEFAULT FALSE COMMENT 'Statut de l''inventaire',
    CONSTRAINT fk_session_inventory 
        FOREIGN KEY (sessionID) 
        REFERENCES sessions(sessionID) 
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- 3. Table des Fichiers (Stockage binaire par inventaire)
CREATE TABLE files (
    fileID INT AUTO_INCREMENT PRIMARY KEY,
    inventoryID INT NOT NULL COMMENT 'Inventaire parent',
    fileName VARCHAR(255) NOT NULL COMMENT 'Nom du fichier',
    -- 'mask' = original, 'template' = excel agrégé, 'final' = csv corrigé
    fileType ENUM('mask', 'template', 'final') NOT NULL COMMENT 'Type de fichier',
    -- LONGBLOB : Indispensable pour les fichiers d'inventaire volumineux (jusqu'à 4Go)
    content LONGBLOB NOT NULL,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_inventory_files 
        FOREIGN KEY (inventoryID) 
        REFERENCES inventory(inventoryID) 
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- 4. Table d'Audit (Traçabilité par inventaire)
CREATE TABLE inventory_audits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inventoryID INT NOT NULL COMMENT 'Inventaire parent',
    actionType VARCHAR(50) NOT NULL COMMENT 'Type d''action effectuée', -- ex: 'STATUT_Q_DETECTED', 'LOT_IGNORED'
    details TEXT NOT NULL COMMENT 'Détails de l''action',
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_inventory_audit 
        FOREIGN KEY (inventoryID) 
        REFERENCES inventory(inventoryID) 
        ON DELETE CASCADE
) ENGINE=InnoDB;
