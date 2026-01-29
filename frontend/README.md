# ⚛️ Moulinette Frontend

> Interface utilisateur React pour le traitement des inventaires Sage X3

---

## 📦 Technologies

| Technologie | Version | Usage |
|-------------|---------|-------|
| **React** | 18+ | Framework UI |
| **TypeScript** | 5.0+ | Typage statique |
| **Vite** | 5.0+ | Build tool |
| **Tailwind CSS** | 3.4+ | Styling |
| **Axios** | 1.6+ | Client HTTP |
| **Lucide React** | 0.300+ | Icônes |

---

## 🚀 Installation

### Prérequis

- Node.js 18+
- npm 9+ ou yarn

### Installation Locale

```bash
# Installer les dépendances
npm install

# Lancer en mode développement
npm run dev

# L'application est accessible sur http://localhost:5173
```

### Build Production

```bash
# Créer le bundle de production
npm run build

# Prévisualiser le build
npm run preview
```

---

## 📁 Structure

```
frontend/
├── 📂 public/
│   └── logo.png               # Logo Moulinette
│
├── 📂 src/
│   ├── 📂 assets/
│   │   └── logo.png
│   │
│   ├── 📂 components/
│   │   ├── Layout.tsx         # 🖼️ Layout principal + Stepper
│   │   ├── StepUpload.tsx     # 📤 Upload masque CSV
│   │   ├── StepSummary.tsx    # 📊 Résumé + Template
│   │   ├── StepEdit.tsx       # ✏️ Édition (optionnel)
│   │   ├── SessionHistory.tsx # 📜 Historique sessions
│   │   └── ErrorBoundary.tsx  # ⚠️ Gestion erreurs React
│   │
│   ├── 📂 config/
│   │   └── api.ts             # 🔧 Configuration API endpoints
│   │
│   ├── App.tsx                # 🎯 Composant principal
│   ├── App.css
│   ├── index.css              # 🎨 Styles Tailwind
│   └── main.tsx               # 🚀 Point d'entrée
│
├── nginx.conf                 # 🌐 Config Nginx (production)
├── package.json
├── tailwind.config.js
├── tsconfig.json
├── vite.config.ts
└── Dockerfile                 # 🐳 Image Docker multi-stage
```

---

## 🎯 Composants

### App.tsx

Composant racine gérant le workflow en 4 étapes.

```typescript
// États principaux
const [step, setStep] = useState(1);        // Étape actuelle
const [depot, setDepot] = useState('');      // Type dépôt
const [sessionId, setSessionId] = useState(null);
const [stats, setStats] = useState(null);

// Étapes du workflow
1. Sélection du dépôt (Conforme/Non-Conforme)
2. Upload du masque CSV
3. Résumé + Template Excel
4. Téléchargement fichier final
```

### Layout.tsx

Layout avec stepper visuel et bouton historique.

```tsx
<Layout currentStep={step} headerContent={...}>
  {children}
</Layout>
```

### StepUpload.tsx

Zone drag & drop pour l'upload du masque CSV.

| Prop | Type | Description |
|------|------|-------------|
| `depotType` | string | "Conforme" ou "Non-Conforme" |
| `onSuccess` | function | Callback après upload réussi |

### StepSummary.tsx

Affiche les statistiques et gère le template Excel.

| Prop | Type | Description |
|------|------|-------------|
| `sessionId` | number | ID de la session |
| `stats` | object | Statistiques d'analyse |
| `onSuccess` | function | Callback après génération finale |

### SessionHistory.tsx

Panel latéral pour consulter/reprendre les sessions.

| Prop | Type | Description |
|------|------|-------------|
| `onResume` | function | Callback pour reprendre une session |

---

## 🔧 Configuration API (config/api.ts)

```typescript
// Détection automatique de l'environnement
const API_BASE_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:8000'  // Développement
  : '';                       // Production (proxy Nginx)

export const API_ENDPOINTS = {
  UPLOAD_MASK: `${API_BASE_URL}/inventory/upload-mask`,
  DOWNLOAD_TEMPLATE: (id: number) => 
    `${API_BASE_URL}/inventory/download-template/${id}`,
  UPLOAD_TEMPLATE: (id: number) => 
    `${API_BASE_URL}/inventory/upload-filled-template/${id}`,
  DOWNLOAD_FILE: (id: number, type: string) => 
    `${API_BASE_URL}/inventory/download-file/${id}/${type}`,
  ACTIVE_SESSIONS: `${API_BASE_URL}/inventory/active-sessions`,
  RESUME_SESSION: (id: number) => 
    `${API_BASE_URL}/inventory/session/${id}/resume`,
  DELETE_SESSION: (id: number) => 
    `${API_BASE_URL}/inventory/session/${id}`,
};
```

---

## 🎨 Styles

### Tailwind CSS

Configuration personnalisée dans `tailwind.config.js` :

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#EFF6FF',
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8',
        }
      }
    }
  }
}
```

### Classes Principales

| Classe | Usage |
|--------|-------|
| `.card` | Conteneur avec ombre et bordure |
| `.btn-primary` | Bouton principal bleu |
| `.btn-secondary` | Bouton secondaire gris |
| `.dropzone` | Zone de drag & drop |
| `.stat-card` | Carte de statistique |

---

## 🌐 Nginx (Production)

Le fichier `nginx.conf` configure :

1. **Serving statique** des fichiers build
2. **Proxy API** vers le backend (`/inventory/*`)
3. **SPA routing** (fallback vers index.html)

```nginx
location /inventory/ {
    proxy_pass http://backend:8000;
}

location / {
    try_files $uri $uri/ /index.html;
}
```

---

## 🐳 Docker

### Dockerfile Multi-Stage

```dockerfile
# Stage 1: Build
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Production
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### Build & Run

```bash
# Build
docker build -t moulinette-frontend .

# Run
docker run -d -p 80:80 moulinette-frontend
```

---

## 📜 Scripts NPM

| Script | Commande | Description |
|--------|----------|-------------|
| `dev` | `vite` | Serveur développement |
| `build` | `tsc && vite build` | Build production |
| `preview` | `vite preview` | Preview du build |
| `lint` | `eslint src` | Vérification code |
| `test` | `vitest` | Tests unitaires |

---

## 🧪 Tests

```bash
# Lancer les tests
npm test

# Mode watch
npm run test:watch

# Couverture
npm run test:coverage
```

---

## 📱 Responsive Design

L'application est optimisée pour :

| Device | Breakpoint | Colonnes |
|--------|------------|----------|
| Mobile | < 640px | 1 |
| Tablet | 640px - 1024px | 2 |
| Desktop | > 1024px | 3 |

---

## ⚡ Performance

- **Code Splitting** automatique avec Vite
- **Tree Shaking** des imports inutilisés
- **Lazy Loading** des composants lourds
- **Compression Gzip** via Nginx

---

## 🔒 Sécurité

- Validation des types de fichiers côté client
- Limite de taille de fichier (50 Mo)
- Sanitization des inputs
- CORS configuré côté backend

---

**Moulinette Frontend** © 2026 SIBM
