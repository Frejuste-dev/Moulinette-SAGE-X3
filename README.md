<h1 align="center">
  <img src="frontend/public/logo.png" alt="Logo" width="40" style="vertical-align: middle;"/> Moulinette SAGE X3
</h1>

> Application de traitement automatisé des inventaires pour l'import dans Sage X3

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

---

## 📋 Table des Matières

- [Présentation](#-présentation)
- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [API Reference](#-api-reference)
- [Structure du Projet](#-structure-du-projet)
- [Licence](#-licence)

---

## 🎯 Présentation

**Moulinette SIBM** est une application web développée pour automatiser le traitement des fichiers d'inventaire exportés depuis Sage X3. Elle permet de :

1. **Importer** un masque CSV depuis Sage X3
2. **Générer** un template Excel pour la saisie des quantités réelles
3. **Calculer** automatiquement les écarts entre stock théorique et réel
4. **Redistribuer** les écarts sur les lots selon les règles FIFO/LIFO
5. **Exporter** un fichier CSV compatible Sage X3

### Contexte Métier

L'application gère deux types de dépôts :
- **Dépôt Conforme** : Produits avec statuts A (Actif) et AM (Actif Mature)
- **Dépôt Non Conforme** : Produits avec statuts R (Rejeté) et RM (Rejeté Mature)

---

## ✨ Fonctionnalités

### Workflow Principal

| Étape | Description |
|-------|-------------|
| 1️⃣ **Contexte** | Sélection du type de dépôt (Conforme/Non-Conforme) |
| 2️⃣ **Import** | Upload du masque CSV exporté de Sage X3 |
| 3️⃣ **Saisie** | Téléchargement du template Excel, saisie des quantités |
| 4️⃣ **Résultat** | Téléchargement du fichier final pour import Sage X3 |

### Fonctionnalités Avancées

- 📊 **Agrégation automatique** des données par article/emplacement
- 🔄 **Redistribution intelligente** des écarts sur les lots (FIFO/LIFO)
- 📅 **Extraction de dates** des numéros de lots
- 💾 **Persistance des sessions** avec reprise possible
- 📝 **Audit trail** complet de toutes les opérations
- 🚫 **Validation stricte** (détection des lots en Quarantaine)

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│              http://localhost:5173 (dev)                     │
│              http://localhost:80 (Docker)                    │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/REST
┌─────────────────────────▼───────────────────────────────────┐
│                     Backend (FastAPI)                        │
│                    http://localhost:8000                     │
│  ┌─────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │   Router    │→ │ InventoryEngine  │→ │   Database     │  │
│  │  (API)      │  │  (Business Logic)│  │  (SQLAlchemy)  │  │
│  └─────────────┘  └──────────────────┘  └────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ SQL
┌─────────────────────────▼───────────────────────────────────┐
│                      MySQL Database                          │
│                    http://localhost:3306                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Prérequis

### Développement Local

- **Python** 3.11+
- **Node.js** 18+
- **MySQL** 8.0+

### Déploiement Docker

- **Docker** 20.10+
- **Docker Compose** 2.0+

---

## 🚀 Installation

### Option 1 : Docker (Recommandé)

```bash
# 1. Cloner le repository
git clone https://github.com/sibm/moulinette.git
cd moulinette

# 2. Copier et configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos paramètres

# 3. Lancer les conteneurs
docker-compose up -d

# 4. Accéder à l'application
# Frontend : http://localhost:80
# API : http://localhost:8000
```

### Option 2 : Développement Local

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (nouveau terminal)
cd frontend
npm install
npm run dev
```

---

## 💻 Utilisation

### 1. Sélection du Dépôt

Choisissez le type de dépôt correspondant à votre inventaire :
- **Conforme** : Pour les produits A/AM
- **Non-Conforme** : Pour les produits R/RM

### 2. Import du Masque

Glissez-déposez le fichier CSV exporté depuis Sage X3. Le système :
- Valide la structure du fichier
- Vérifie la cohérence avec le type de dépôt
- Détecte les lots en Quarantaine (bloquant)

### 3. Saisie des Quantités

1. Téléchargez le **template Excel** généré
2. Remplissez la colonne `QUANTITE_REELLE`
3. Renvoyez le fichier complété

### 4. Téléchargement du Résultat

Le fichier final CSV est prêt pour import dans Sage X3.

---

## 📡 API Reference

### Endpoints Principaux

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/inventory/upload-mask` | Upload du masque CSV |
| `GET` | `/inventory/download-template/{id}` | Télécharger template Excel |
| `POST` | `/inventory/upload-filled-template/{id}` | Upload template rempli |
| `GET` | `/inventory/download-file/{id}/{type}` | Télécharger fichier (mask/template/final) |
| `GET` | `/inventory/active-sessions` | Liste des sessions actives |
| `GET` | `/inventory/session/{id}/resume` | Reprendre une session |
| `DELETE` | `/inventory/session/{id}` | Supprimer une session |

### Exemple : Upload Masque

```bash
curl -X POST "http://localhost:8000/inventory/upload-mask" \
  -F "name=INV_2026-01-29" \
  -F "depot_type=Conforme" \
  -F "file=@masque.csv"
```

**Réponse :**
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

---

## 📁 Structure du Projet

```
moulinette/
├── 📂 backend/
│   ├── 📂 database/
│   │   ├── models.py          # Modèles SQLAlchemy
│   │   └── session.py         # Configuration DB
│   ├── 📂 schemas/
│   │   └── inventory.py       # Schémas Pydantic
│   ├── engine.py              # Logique métier
│   ├── router.py              # Routes API
│   ├── main.py                # Point d'entrée FastAPI
│   ├── requirements.txt
│   └── Dockerfile
│
├── 📂 frontend/
│   ├── 📂 src/
│   │   ├── 📂 components/
│   │   │   ├── Layout.tsx
│   │   │   ├── StepUpload.tsx
│   │   │   ├── StepSummary.tsx
│   │   │   └── SessionHistory.tsx
│   │   ├── 📂 config/
│   │   │   └── api.ts         # Configuration API
│   │   └── App.tsx
│   ├── nginx.conf
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔧 Configuration

### Variables d'Environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `MYSQL_ROOT_PASSWORD` | Mot de passe root MySQL | `root` |
| `MYSQL_DATABASE` | Nom de la base de données | `moulinette` |
| `MYSQL_USER` | Utilisateur MySQL | `moulinette` |
| `MYSQL_PASSWORD` | Mot de passe utilisateur | `moulinette_pwd` |

### Fichier `.env.example`

```env
MYSQL_ROOT_PASSWORD=your_root_password
MYSQL_DATABASE=moulinette
MYSQL_USER=moulinette
MYSQL_PASSWORD=your_secure_password
```

---

## 🧪 Tests

```bash
# Backend
cd backend
pytest --cov=. --cov-report=html

# Frontend
cd frontend
npm test
```

---

## 📊 Modèle de Données

```
Session (1) ─────────┬───────── (*) Inventory
                     │
                     ├───────── (*) File
                     │              - mask
                     │              - template
                     │              - final
                     │
                     └───────── (*) InventoryAudit
                                    - MASK_UPLOADED
                                    - TEMPLATE_GENERATED
                                    - FINAL_FILE_CREATED
```

---

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push sur la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

---

## 📄 Licence

Ce projet est développé par **SIBM** (Société Ivoirienne de Brasseries et de Malteries).

**Moulinette SIBM** © 2026 - Tous droits réservés.

---

## 👨‍💻 Auteur

Développé dans le cadre d'un projet de **Licence Professionnelle en Génie Logiciel**.

---

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-❤️-red?style=for-the-badge" alt="Made with Love"/>
</p>

