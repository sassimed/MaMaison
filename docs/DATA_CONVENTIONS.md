# Conventions de Données - MyDar.tn

Ce document définit les règles et conventions pour la gestion des données dans l'application MyDar.

## 1. Identifiants

### Règle principale
> **Toujours utiliser les `slugs` comme identifiants pour les relations entre collections.**

### Types d'identifiants

| Type | Usage | Exemple |
|------|-------|---------|
| `_id` (ObjectId) | Interne MongoDB uniquement | `ObjectId("6988a9f91ae944926b37e060")` |
| `id` (slug) | Relations, APIs, Frontend | `"alarme"`, `"alarme__detecteurs-contacts"` |
| `slug` | URLs, SEO | `"alarme"`, `"detecteurs-contacts"` |

### Format des slugs
- **Format**: `kebab-case` (minuscules, tirets)
- **Caractères autorisés**: `a-z`, `0-9`, `-`, `_`
- **Sous-catégories**: `parent__enfant` (double underscore)

```javascript
// ✅ BON
"alarme"
"controle-d-acces"
"alarme__detecteurs-contacts"

// ❌ MAUVAIS
"Alarme"                    // Majuscules
"contrôle d'accès"          // Accents et espaces
"6988a9f91ae944926b37e060"  // ObjectId
```

---

## 2. Collections et Schémas

### Categories
```javascript
{
  "_id": ObjectId("..."),           // Interne MongoDB - NE PAS UTILISER
  "id": "6988a9f91ae944926b37e060", // Ancien ObjectId stocké - IGNORER
  "slug": "alarme",                 // ✅ UTILISER COMME ID
  "label": "Alarme",
  "parent_id": "6988...",           // ⚠️ Actuellement ObjectId, devrait être slug
  "level": 1,
  "is_active": true
}
```

**Règles:**
- `slug` = identifiant principal pour les relations
- `parent_id` = slug du parent (migration en cours)
- `level` = 1 pour racine, 2 pour sous-catégorie

### Products
```javascript
{
  "_id": ObjectId("..."),
  "id": "uuid-v4",
  "slug": "shield-7-plus",
  "name": "Shield 7 Plus",
  "category_id": "alarme__centrales-d-alarme",      // ✅ Slug complet
  "category_path_ids": ["alarme", "alarme__centrales-d-alarme"],  // ✅ Slugs
  "category_label": "Alarme",
  "subcategory_label": "Centrales d'alarme",
  "brand": "Schutz",
  "model_code": "SCH-A1B2",
  "price": 450.00,                   // ⚠️ Actuellement manquant
  "active": true
}
```

**Règles:**
- `category_id` = slug complet (parent__enfant)
- `category_path_ids` = tableau de slugs pour le breadcrumb
- Ne jamais utiliser d'ObjectId pour les relations

### Users
```javascript
{
  "_id": ObjectId("..."),
  "id": "uuid-v4",                   // ✅ UUID pour les utilisateurs
  "email": "user@example.com",
  "role": "client|pro|admin",
  "is_active": true
}
```

### Purchase Requests (Commandes)
```javascript
{
  "_id": ObjectId("..."),
  "id": "uuid-v4",                   // 8 premiers caractères = numéro commande
  "user_id": "uuid-v4",              // ✅ UUID de l'utilisateur
  "items": [{
    "product_id": "uuid-v4",         // ✅ UUID du produit
    "product_slug": "shield-7-plus"  // Slug pour référence
  }],
  "status": "pending|confirmed|shipped|delivered|cancelled"
}
```

---

## 3. APIs - Conventions de Réponse

### Règle principale
> **Les APIs doivent retourner le `slug` comme `id`, jamais l'ObjectId MongoDB.**

### Exemple - GET /api/categories
```javascript
// ✅ BON
{
  "id": "alarme",                    // Slug comme ID
  "label": "Alarme",
  "slug": "alarme",
  "subcategories": [
    { "id": "alarme__detecteurs-contacts", "label": "Détecteurs & Contacts" }
  ]
}

// ❌ MAUVAIS
{
  "id": "6988a9f91ae944926b37e060",  // ObjectId exposé
  "label": "Alarme"
}
```

### Sérialisation MongoDB
```python
# ✅ BON - Exclure _id des réponses
await db.products.find({}, {"_id": 0}).to_list(100)

# ✅ BON - Convertir si nécessaire
def serialize_doc(doc):
    doc.pop("_id", None)
    return doc

# ❌ MAUVAIS - Retourner _id directement
await db.products.find({}).to_list(100)  # Erreur: ObjectId not JSON serializable
```

---

## 4. Import de Données

### Checklist avant import
- [ ] Tous les `category_id` utilisent des slugs
- [ ] Tous les `parent_id` utilisent des slugs (pas ObjectId)
- [ ] Les slugs sont en `kebab-case`
- [ ] Pas de doublons de slugs
- [ ] Les relations existent (ex: category_id pointe vers une catégorie existante)

### Script de validation
```bash
# Exécuter avant tout import
python -m pytest /app/backend/tests/test_data_coherence.py -v
```

---

## 5. Migrations et Synchronisation

### Endpoint de migration
```
POST /api/migrations/init
```

Cet endpoint :
1. Exporte les données de développement
2. Importe dans la base cible
3. Valide la cohérence des données

### Avant déploiement en production
1. Exécuter les tests de cohérence
2. Vérifier que toutes les relations utilisent des slugs
3. Appeler `/api/migrations/init` après déploiement

---

## 6. Erreurs Courantes à Éviter

### ❌ Mélanger ObjectId et slugs
```javascript
// PROBLÈME: L'API retourne ObjectId, les produits utilisent slugs
categories: [{ id: "6988a9f91ae944926b37e060" }]
products: [{ category_id: "alarme" }]

// Le filtre ne trouvera rien !
GET /api/products?category=6988a9f91ae944926b37e060
```

### ❌ Oublier d'exclure _id
```python
# PROBLÈME: TypeError: ObjectId is not JSON serializable
return await db.products.find_one({"slug": slug})

# SOLUTION
return await db.products.find_one({"slug": slug}, {"_id": 0})
```

### ❌ Utiliser datetime.utcnow()
```python
# PROBLÈME: Déprécié
created_at = datetime.utcnow()

# SOLUTION
from datetime import datetime, timezone
created_at = datetime.now(timezone.utc)
```

---

## 7. Résumé des Règles

| Règle | Description |
|-------|-------------|
| **R1** | Utiliser `slug` comme identifiant pour toutes les relations |
| **R2** | Ne jamais exposer `_id` MongoDB dans les APIs |
| **R3** | Format slug: `kebab-case`, sous-catégories: `parent__enfant` |
| **R4** | Toujours exclure `_id` des projections MongoDB |
| **R5** | Valider la cohérence avant chaque import |
| **R6** | Utiliser `datetime.now(timezone.utc)` pour les dates |

---

## 8. Contacts

Pour toute question sur ces conventions :
- Consulter ce document en premier
- Vérifier les tests dans `/app/backend/tests/test_data_coherence.py`
- Exécuter `bash /app/backend/run_tests.sh` pour valider

---

*Document créé le 8 Février 2026*
*Dernière mise à jour: 8 Février 2026*
