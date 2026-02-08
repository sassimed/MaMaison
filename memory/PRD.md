# MyDar - Product Requirements Document

## Original Problem Statement
MyDar est une plateforme e-commerce tunisienne spécialisée dans les produits domotiques.

## What's Been Implemented


### ✅ Session du 8 Février 2026 - Correction Filtrage par Catégorie

**Problème résolu:** Le filtrage des produits par catégorie ne fonctionnait pas car l'API categories retournait des ObjectId MongoDB alors que les produits utilisent des slugs.

**Corrections apportées:**

1. **API `/api/categories`** - Retourne maintenant les slugs comme IDs au lieu des ObjectId MongoDB
   - `id: "alarme"` au lieu de `id: "6988a9f91ae944926b37e060"`
   - Sous-catégories incluses avec slugs: `id: "alarme__detecteurs-contacts"`

2. **API `/api/categories/{id}/children`** - Recherche par slug prioritairement

3. **API `/api/admin/categories`** - Recherche les sous-catégories par MongoDB ObjectId parent_id

4. **Correction admin_products.py** - Fix bug `isoformat()` sur string

5. **Fix AdminProducts.js** - Corrigé le parsing des catégories (API retourne array, pas objet)

6. **Fix CatalogPage.js** - Corrigé le useEffect pour fetchProducts avec les bons filtres

**Tests validés (Screenshots):**
- ✅ Catalogue public: 276 produits pour "Alarme", sous-catégories visibles
- ✅ Admin Produits: 2737 produits, filtre "Alarme" = 278 produits
- ✅ Admin Catégories: 15 catégories avec sous-catégories dépliables

---

### ✅ Session du 8 Février 2026 - API de Migration pour Production

**Nouvelle API:** `/api/migrations/run`

**Endpoints disponibles:**
- `GET /api/migrations/available` - Liste les migrations disponibles
- `GET /api/migrations/status` - Statut de la base de données
- `POST /api/migrations/run` - Exécute les migrations (nécessite clé)

**Migrations incluses:**
1. `generate_model_codes` - Génère les codes modèles (BRAND-XXXX)
2. `ensure_indexes` - Crée les index MongoDB pour les performances
3. `cleanup_chat_sessions` - Supprime les anciennes sessions (>30 jours)
4. `set_default_chatbot_model` - Configure GPT-5.2 par défaut
5. `normalize_product_data` - Normalise les champs produits

**Utilisation après déploiement:**
```bash
curl -X POST https://mydar.tn/api/migrations/run \
     -H "X-Migration-Key: mydar-migration-2026" \
     -H "Content-Type: application/json"
```

**Fichier:** `/app/backend/routes/migrations.py`

---

### ✅ Session du 8 Février 2026 - Chatbot utilise les Specs Techniques

**Amélioration:** Le chatbot répond maintenant aux questions techniques en utilisant les spécifications du produit.

**Exemple:**
- Question: "quel codec video supporte ce NVR?" (HIK-7DA0)
- Réponse: "Ce NVR Hikvision supporte: **H.265+, H.265, H.264+, H.264**"

---

### ✅ Session du 8 Février 2026 - Codes Modèles + Bouton Ask IA

**Fonctionnalités ajoutées:**

1. **Codes modèles générés pour 2737 produits**
   - Format: `BRAND-XXXX` (ex: `DAH-EE41`, `SOM-668C`)
   - Basé sur les 3 premières lettres de la marque + hash unique

2. **Page détail produit - Améliorations**
   - ✅ Code modèle affiché sous le titre avec fond violet
   - ✅ Bouton copier le code modèle
   - ✅ Bouton "Ask IA" (icône robot) pour poser des questions

3. **Bouton Ask IA - Comportement**
   - Ouvre le chatbot automatiquement
   - Saute les étapes langue + mode (auto-détection)
   - Envoie directement le code modèle au chatbot
   - Affiche le produit trouvé avec carte interactive

4. **Recherche par code modèle**
   - ✅ Fonctionne dans le catalogue `/catalog?q=DAH-EE41`
   - ✅ Fonctionne dans le chatbot (mode question produit)
   - ✅ Fonctionne dans l'admin produits

**Fichiers modifiés:**
- `/app/backend/routes/products_v2.py` - Recherche par model_code
- `/app/backend/routes/chatbot_v3.py` - Recherche par model_code
- `/app/frontend/src/pages/public/ProductDetailPage.js` - UI code + Ask IA
- `/app/frontend/src/components/chat/ChatWidget.js` - Écoute événement produit

---

### ✅ Session précédente - Suivi Commande Réel + Améliorations Interfaces

**Fonctionnalités ajoutées:**

1. **Chatbot - Suivi commande connecté à la vraie base de données**
   - Recherche dans `purchase_requests` par numéro de commande (8 premiers caractères)
   - Recherche aussi par email ou téléphone
   - Affiche le vrai statut de la commande (EN_ATTENTE, EN_COURS, VALIDEE, REFUSEE)

2. **Admin "Demandes d'Achat" - Améliorations**
   - ✅ Nouvelle colonne "N° COMMANDE" avec format `#580743A6`
   - ✅ Bouton copier le numéro de commande
   - ✅ Champ de recherche par numéro, nom, email, téléphone

3. **Espace Client "Mes Commandes" - Amélioration**
   - ✅ Bouton copier le numéro de commande (pour le donner au chatbot)

**Fichiers modifiés:**
- `/app/backend/routes/chatbot_v3.py` - Fonction `track_order()` connectée à `purchase_requests`
- `/app/frontend/src/pages/admin/AdminPurchaseRequests.js` - Colonne N°, recherche, copier
- `/app/frontend/src/pages/dashboard/MyPurchaseRequestsPage.js` - Bouton copier

---

### ✅ Session précédente - Nouveau Flux Chatbot avec Choix de Langue

**Nouveau flux en 3 étapes:**

```
ÉTAPE 1 - Choix de langue (automatique à l'ouverture):
  Bienvenue 👋 / Mar7bé 👋
  🇫🇷 1 - Français
  🇹🇳 2 - Tounsi (arabizi)

ÉTAPE 2 - Choix du mode (dans la langue choisie)
  1️⃣ Suivre commande
  2️⃣ Question produit
  3️⃣ Aide au choix

ÉTAPE 3 - Conversation dans UNE seule langue
```

---

### ✅ Session précédente - Interface Admin Changement Modèle IA

**Nouvelle fonctionnalité :** Interface d'administration permettant de changer le modèle IA du chatbot.

**Fichier modifié:** `/app/frontend/src/pages/admin/AdminChatbot.js`

**Fonctionnalités ajoutées:**
- ✅ Panneau "Configuration du Modèle IA" dans `/dashboard/admin/chatbot`
- ✅ Dropdown pour sélectionner le modèle actif (GPT-5.2, GPT-4o, Gemini 2/3, Claude Sonnet)
- ✅ Indicateur visuel du modèle actif avec coche verte
- ✅ Liste des modèles disponibles avec descriptions
- ✅ Mise à jour dynamique de la section "Information Facturation"
- ✅ Spinner de chargement pendant le changement de modèle

**Modèles disponibles:**
| ID | Provider | Modèle | Description |
|----|----------|--------|-------------|
| gpt-5.2 | OpenAI | gpt-5.2 | Meilleure qualité (recommandé) |
| gpt-4o | OpenAI | gpt-4o | Rapide et efficace |
| gemini-2 | Gemini | gemini-2.0-flash | Alternative économique |
| gemini-3-flash | Gemini | gemini-3-flash | Dernière version Gemini |
| claude-sonnet | Anthropic | claude-sonnet-4-5 | Bon pour les conversations |

---

### ✅ Session précédente - Chatbot V3 avec Flux Guidé

**Fichier actif:** `/app/backend/routes/chatbot_v3.py`

**ÉTAPE 1 - Accueil Bilingue (FR + Arabizi):**
```
Bienvenue 👋 / Mar7bé 👋
1️⃣ Suivre une commande / ttabba3 commande
2️⃣ Poser une question sur un produit / so2él 3la produit
3️⃣ T'aider à choisir un produit / n3awnek tkhtar produit mneseb
```

**ÉTAPE 2 - Conversation selon le mode:**
- **Mode 1 (Commande)**: Demande numéro de commande, affiche statut
- **Mode 2 (Questions)**: Répond aux questions techniques SANS proposer de produits
- **Mode 3 (Aide)**: Pose questions puis propose 3-5 produits avec cartes

**Règles strictes:**
- Détection automatique de la langue (FR ou Tunisien arabizi)
- NE JAMAIS inventer d'informations (prix, stock, specs)
- Reproposer les 3 options à la fin de chaque réponse

## Current Status

### ✅ Resolved
- Interface admin de sélection du modèle IA (testé et fonctionnel)
- Chatbot V3 avec flux guidé bilingue
- Restauration des 2737 produits dans MongoDB

### 🔴 P0 - Critical (BLOQUANT)
1. **⚠️ Prix manquants** - TOUS les 2737 produits n'ont pas de prix → E-commerce non viable

### 🟠 P1 - High Priority  
1. Créer vraie API suivi commande (`/api/orders/{order_id}`)
2. Filtres facettes sur page catalogue (marque, connectivité)
3. 82 produits Somfy sans images

### 🟡 P2 - Medium Priority
1. Drag-and-drop réorganisation sous-catégories admin
2. Options paiement "Livraison" et "Virement bancaire"
3. Nettoyer code obsolète (`chatbot.py`, `chatbot_v2/`, `chatbot_gpt.py`)

### 🔵 Backlog
1. Intégration Monétique Tunisie (en attente credentials)
2. Générateur sitemap.xml
3. Téléchargement fiches techniques PDF

## Tech Stack
- **Frontend**: React + Tailwind CSS + Shadcn/UI
- **Backend**: FastAPI + Motor (async MongoDB)
- **AI**: Configurable via admin (GPT-5.2 par défaut) via Emergent LLM Key

## Test Credentials
| Rôle | Email | Mot de passe |
|------|-------|--------------|
| 👑 Admin | admin@mydar.tn | admin123 |
| 🔧 Pro | pro@mydar.tn | pro123 |
| 👤 Client | client@mydar.tn | client123 |

## Key API Endpoints
- `POST /api/chatbot/chat` - Endpoint principal chatbot (V3)
- `GET /api/chatbot/admin/ai-models` - Liste modèles IA disponibles
- `POST /api/chatbot/admin/ai-model` - Changer le modèle IA actif
- `GET /api/products` - Liste produits catalogue