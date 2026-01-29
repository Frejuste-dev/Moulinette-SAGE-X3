# 🐍 Moulinette Backend

> API REST FastAPI pour le traitement des inventaires Sage X3

---

## 📦 Technologies

| Technologie | Version | Usage |
|-------------|---------|-------|
| **Python** | 3.11+ | Runtime |
| **FastAPI** | 0.104+ | Framework API |
| **SQLAlchemy** | 2.0+ | ORM |
| **Pandas** | 2.1+ | Traitement données |
| **OpenPyXL** | 3.1+ | Génération Excel |
| **PyMySQL** | 1.1+ | Driver MySQL |
| **Uvicorn** | 0.24+ | Serveur ASGI |

---

## 🚀 Installation

### Prérequis

- Python 3.11+
- MySQL 8.0+ (ou Docker)

### Installation Locale

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Installer les dépendances
pip install -r requirements.txt

# Configurer la base de données
# Créer une base MySQL 'moulinette' et importer template.sql

# Lancer le serveur
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Variables d'Environnement

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/moulinette
```

---

## 📁 Structure

```
backend/
├── 📂 database/
│   ├── __init__.py
│   ├── models.py          # Modèles SQLAlchemy (Session, Inventory, File, Audit)
│   └── session.py         # Configuration connexion DB
│
├── 📂 schemas/
│   └── inventory.py       # Schémas Pydantic pour validation
│
├── engine.py              # 🧠 Logique métier (InventoryEngine)
├── router.py              # 🛣️ Routes API (/inventory/*)
├── main.py                # 🚀 Point d'entrée FastAPI
├── exceptions.py          # ⚠️ Exceptions personnalisées
├── requirements.txt       # 📋 Dépendances Python
└── Dockerfile             # 🐳 Image Docker
```

---

## 🧠 Logique Métier (engine.py)

### Classe `InventoryEngine`

```python
class InventoryEngine:
    def validate_mask(df, depot_type) -> List[str]
    def aggregate_for_template(df_mask) -> bytes
    def distribute_gaps(df_mask, df_reel) -> DataFrame
    def extract_lot_date(lot_number) -> datetime
```

| Méthode | Description |
|---------|-------------|
| `validate_mask()` | Vérifie la cohérence dépôt/statuts (A/AM vs R/RM) |
| `aggregate_for_template()` | Agrège les données par Article + Emplacement |
| `distribute_gaps()` | Redistribue les écarts sur les lots (FIFO/LIFO) |
| `extract_lot_date()` | Extrait la date d'un numéro de lot via RegEx |

### Règles de Redistribution

```
SI écart > 0 (surplus):
    → Ajouter au lot le PLUS RÉCENT (LIFO)
    
SI écart < 0 (manque):
    → Déduire du lot le PLUS ANCIEN d'abord (FIFO)
    → Si lot tombe à 0, passer au suivant
```

---

## 🛣️ API Endpoints

### Upload Masque CSV

```http
POST /inventory/upload-mask
Content-Type: multipart/form-data

name: string (required)
depot_type: "Conforme" | "Non-Conforme" (required)
file: File (required, .csv)
```

**Response 200:**
```json
{
  "status": "success",
  "sessionID": 3,
  "stats": {
    "total_lines": 1245,
    "total_products": 89,
    "total_lots": 312
  }
}
```

### Télécharger Template

```http
GET /inventory/download-template/{session_id}

Response: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
```

### Upload Template Rempli

```http
POST /inventory/upload-filled-template/{session_id}
Content-Type: multipart/form-data

file: File (required, .xlsx)
```

### Télécharger Fichier Final

```http
GET /inventory/download-file/{session_id}/final

Response: text/csv
```

### Autres Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/inventory/active-sessions` | Liste sessions actives |
| `GET` | `/inventory/session/{id}/resume` | Données pour reprise |
| `GET` | `/inventory/session/{id}/status` | Statut détaillé |
| `DELETE` | `/inventory/session/{id}` | Supprimer session |
| `GET` | `/inventory/session/{id}/audits` | Historique audit |

---

## 🗃️ Modèles de Données

### Session

```python
class Session(Base):
    sessionID: Integer (PK)
    sessionNUM: String       # Numéro Sage X3
    sessionNAME: String      # Nom descriptif
    currentStep: Integer     # Étape workflow (1-4)
    isCompleted: Boolean
    createdAt: DateTime
```

### Inventory

```python
class Inventory(Base):
    inventoryID: Integer (PK)
    inventoryNUM: String     # Numéro inventaire Sage
    sessionID: Integer (FK)
    depotType: String        # "Conforme" | "Non-Conforme"
    inventorySite: String    # Code site (ex: ABJ01)
    isCompleted: Boolean
```

### File

```python
class File(Base):
    fileID: Integer (PK)
    inventoryID: Integer (FK)
    fileName: String
    fileType: Enum           # mask | template | final
    content: LargeBinary     # Contenu binaire du fichier
```

### InventoryAudit

```python
class InventoryAudit(Base):
    id: Integer (PK)
    inventoryID: Integer (FK)
    actionType: String       # MASK_UPLOADED, TEMPLATE_GENERATED, etc.
    details: Text
    createdAt: DateTime
```

---

## 🧪 Tests

```bash
# Lancer les tests
pytest

# Avec couverture
pytest --cov=. --cov-report=html

# Ouvrir le rapport
start htmlcov/index.html
```

---

## 🐳 Docker

### Build

```bash
docker build -t moulinette-backend .
```

### Run

```bash
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=mysql+pymysql://user:pwd@db:3306/moulinette \
  moulinette-backend
```

---

## 📋 Dépendances (requirements.txt)

```
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0.0
pymysql>=1.1.0
pandas>=2.1.0
openpyxl>=3.1.0
python-multipart>=0.0.6
python-dotenv>=1.0.0
```

---

## ⚠️ Gestion des Erreurs

| Code | Exception | Cause |
|------|-----------|-------|
| 400 | `FileSizeError` | Fichier > 50 Mo |
| 400 | `FileExtensionError` | Extension non autorisée |
| 400 | `DataValidationError` | Données CSV invalides |
| 404 | `SessionNotFoundError` | Session inexistante |
| 400 | `QuarantineError` | Lots en Statut Q détectés |

---

**Moulinette Backend** © 2026 SIBM
