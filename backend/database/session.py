from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# En production, on utilise des variables d'environnement. 
# Pour le développement, on définit une URL par défaut.
# Format : mysql+pymysql://user:password@host:port/dbname
MYSQL_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://root:sibmlab%401014@localhost:3306/moulinette_db"
)

# 1. L'Engine : Il gère la connexion réelle à la base de données.
# pool_pre_ping=True permet de vérifier si la connexion est toujours active 
# (évite les erreurs "MySQL server has gone away").
engine = create_engine(
    MYSQL_URL, 
    pool_pre_ping=True,
    pool_recycle=3600
)

# 2. SessionLocal : Une factory pour créer des sessions de base de données.
# autocommit=False : On valide les changements manuellement avec db.commit().
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Base : La classe parente de tous nos modèles SQLAlchemy.
Base = declarative_base()

# 4. Dépendance FastAPI : Permet d'injecter la session DB dans les routes.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        # On ferme toujours la session après l'exécution de la route, 
        # même s'il y a eu une erreur.
        db.close()