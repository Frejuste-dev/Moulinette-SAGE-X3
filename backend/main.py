from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('moulinette.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from database.session import engine, Base
from database import models
from router import router as inventory_router

# 1. Initialisation de la base de données
logger.info("Initializing database tables...")
# Cette ligne crée automatiquement les tables dans MySQL au démarrage 
# si elles n'existent pas encore (InventorySession, InventoryFile, etc.)
models.Base.metadata.create_all(bind=engine)

# 2. Création de l'application FastAPI
app = FastAPI(
    title="Moulinette SIBM",
    description="Système automatisé de traitement d'écarts d'inventaire avec stockage binaire MySQL.",
    version="1.0.0"
)

# 3. Configuration du CORS (Cross-Origin Resource Sharing)
# Essentiel pour que ton Frontend React (Vite) puisse communiquer avec l'API
origins = [
    "http://localhost:5173",  # Port par défaut de Vite
    "http://127.0.0.1:5173",
    # Ajoute ici l'URL de production plus tard
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Autorise tous les verbes HTTP (GET, POST, etc.)
    allow_headers=["*"],  # Autorise tous les en-têtes
    expose_headers=["Content-Disposition"], # ESSENTIEL pour lire le nom du fichier en JS !
)

# 4. Inclusion des routes
app.include_router(inventory_router)

# 5. Route de santé (Healthcheck)
@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "message": "Moulinette SIBM is running",
        "database": "connected"
    }

# 6. Lancement du serveur (si exécuté directement)
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)