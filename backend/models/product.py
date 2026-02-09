"""
Modèle Produit Universel - MaMaison
Support pour tous types de produits (électronique, meubles, déco, jardin, etc.)
avec système d'affiliation multi-sources
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid


# ══════════════════════════════════════════════════════════════
# SOUS-MODÈLES POUR STRUCTURE FLEXIBLE
# ══════════════════════════════════════════════════════════════

class SpecValue(BaseModel):
    """Spécification flexible clé-valeur"""
    key: str                              # Ex: "screen_size", "capacity", "weight"
    value: Any                            # Ex: 55, "4K", True, ["WiFi", "Bluetooth"]
    unit: Optional[str] = None            # Ex: "pouces", "kg", "L", "W"
    display: Optional[str] = None         # Ex: "55 pouces", "4K UHD"
    group: str = "general"                # Ex: "dimensions", "energy", "connectivity"
    comparable: bool = True               # Utilisé pour comparaisons IA
    filterable: bool = False              # Apparaît dans les filtres boutique


class PriceSource(BaseModel):
    """Prix provenant d'une source d'affiliation"""
    source: str                           # Ex: "amazon", "fnac", "cdiscount", "internal"
    price: Optional[float] = None
    currency: str = "EUR"
    original_price: Optional[float] = None  # Prix barré
    discount_percent: Optional[float] = None
    url: Optional[str] = None             # URL directe
    affiliate_url: Optional[str] = None   # URL avec tracking affiliation
    affiliate_tag: Optional[str] = None   # Tag affilié (ex: "mamaison-21")
    in_stock: bool = True
    stock_quantity: Optional[int] = None
    delivery_info: Optional[str] = None   # Ex: "Livraison Prime 1j"
    delivery_cost: Optional[float] = None
    seller: Optional[str] = None          # Ex: "Amazon", "Vendeur tiers"
    condition: str = "new"                # new, refurbished, used
    updated_at: Optional[datetime] = None


class BestPrice(BaseModel):
    """Meilleur prix parmi toutes les sources"""
    source: str
    price: float
    currency: str = "EUR"
    url: Optional[str] = None
    affiliate_url: Optional[str] = None


class PriceHistoryEntry(BaseModel):
    """Historique des prix"""
    date: datetime
    price: float
    source: str


class ProductPrices(BaseModel):
    """Structure complète des prix multi-sources"""
    default: Optional[PriceSource] = None           # Prix interne MaMaison
    sources: List[PriceSource] = []                 # Prix des sources affiliées
    best_price: Optional[BestPrice] = None          # Meilleur prix calculé
    price_history: List[PriceHistoryEntry] = []     # Historique


class ProductVariant(BaseModel):
    """Variante de produit (couleur, taille, etc.)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sku: Optional[str] = None
    name: str                              # Ex: "Blanc 147x147cm"
    attributes: Dict[str, Any] = {}        # Ex: {"color": "Blanc", "size": "4x4"}
    price: Optional[float] = None
    in_stock: bool = True
    image: Optional[str] = None


class ProductCategory(BaseModel):
    """Catégorisation hiérarchique"""
    id: str                                # Ex: "meubles__rangement__etageres"
    path: List[str] = []                   # Ex: ["Meubles", "Rangement", "Étagères"]
    type: Optional[str] = None             # Type générique pour requêtes
    room: List[str] = []                   # Pièces de destination
    universe: Optional[str] = None         # Univers principal


class ProductMedia(BaseModel):
    """Médias associés au produit"""
    primary_image: Optional[str] = None
    images: List[str] = []
    video_url: Optional[str] = None        # YouTube ou autre
    manual_pdf: Optional[str] = None
    datasheet_pdf: Optional[str] = None
    model_3d: Optional[str] = None         # Pour AR/VR futur


class ProductTags(BaseModel):
    """Tags pour recherche et filtres IA"""
    features: List[str] = []               # Ex: ["4k", "hdr", "smart_tv"]
    rooms: List[str] = []                  # Ex: ["salon", "bureau"]
    styles: List[str] = []                 # Ex: ["scandinave", "moderne"]
    usage: List[str] = []                  # Ex: ["gaming", "cinema"]
    audience: List[str] = []               # Ex: ["famille", "gamers"]
    tier: Optional[str] = None             # budget, mid_range, premium, luxury


class ProductScores(BaseModel):
    """Scores pour classement IA"""
    overall: Optional[float] = None        # Score global 0-100
    value_for_money: Optional[float] = None
    quality: Optional[float] = None
    design: Optional[float] = None
    durability: Optional[float] = None
    ease_of_use: Optional[float] = None
    popularity: Optional[float] = None
    eco_score: Optional[float] = None
    reviews_score: Optional[float] = None  # Note moyenne avis (/5)
    reviews_count: int = 0


class ProductAI(BaseModel):
    """Données pour assistant IA"""
    summary: Optional[str] = None          # Résumé court
    bullets: List[str] = []                # Points clés
    pros: List[str] = []                   # Avantages
    cons: List[str] = []                   # Inconvénients
    best_for: List[str] = []               # Idéal pour...
    not_for: List[str] = []                # Pas recommandé pour...
    alternatives_ids: List[str] = []       # IDs produits alternatifs
    accessories_ids: List[str] = []        # IDs accessoires recommandés
    bundle_suggestion: Optional[str] = None


class ProductMeta(BaseModel):
    """Métadonnées système"""
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    source: Optional[str] = None           # Source du scraping
    source_url: Optional[str] = None
    data_quality: float = 0.0              # Complétude des données 0-1
    last_price_check: Optional[datetime] = None
    active: bool = True
    verified: bool = False
    schema_version: str = "v3_universal"


# ══════════════════════════════════════════════════════════════
# MODÈLE PRODUIT PRINCIPAL
# ══════════════════════════════════════════════════════════════

class Product(BaseModel):
    """
    Modèle Produit Universel
    Supporte tous types de produits pour la maison avec affiliation multi-sources
    """
    
    # ────── IDENTIFICATION ──────
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sku: Optional[str] = None              # Code interne
    ean: Optional[str] = None              # Code-barres européen (pour Icecat, matching)
    upc: Optional[str] = None              # Code-barres US
    asin: Optional[str] = None             # Amazon ID
    mpn: Optional[str] = None              # Manufacturer Part Number
    model_code: Optional[str] = None       # Code modèle fabricant
    slug: Optional[str] = None             # URL-friendly slug
    
    # ────── INFORMATIONS DE BASE ──────
    name: str
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    
    # ────── CATÉGORISATION ──────
    # Nouveau format structuré
    category_data: Optional[ProductCategory] = None
    # Rétrocompatibilité avec ancien format
    category: Optional[str] = None
    category_id: Optional[str] = None
    category_path_ids: List[str] = []
    category_label: Optional[str] = None
    subcategory_label: Optional[str] = None
    
    # ────── SPECIFICATIONS UNIVERSELLES ──────
    specs: List[SpecValue] = []            # Nouveau format flexible
    # Rétrocompatibilité
    specifications: List[Dict[str, Any]] = []  # Ancien format [{name, specs: [{key, value}]}]
    attributes: Dict[str, Any] = {}
    attributes_norm: Dict[str, Any] = {}
    technology: str = "WiFi"               # Legacy field
    compatibility: List[str] = []
    technologies: List[str] = []
    
    # ────── PRIX MULTI-SOURCES ──────
    prices: Optional[ProductPrices] = None  # Nouveau format complet
    # Rétrocompatibilité
    price: Optional[float] = None           # Prix principal (legacy)
    currency: str = "TND"
    
    # ────── VARIANTES ──────
    variants: List[ProductVariant] = []
    
    # ────── MÉDIAS ──────
    media: Optional[ProductMedia] = None    # Nouveau format
    # Rétrocompatibilité
    image_url: Optional[str] = None
    image: Optional[str] = None
    primary_image_url: Optional[str] = None
    images: List[str] = []
    gallery_images: List[str] = []
    youtube_url: Optional[str] = None
    manual_url: Optional[str] = None
    datasheet_url: Optional[str] = None
    
    # ────── STOCK ──────
    in_stock: bool = True
    stock_quantity: int = 0
    image_missing: bool = False
    
    # ────── TAGS & FILTRES ──────
    tags: Optional[ProductTags] = None      # Nouveau format
    # Rétrocompatibilité
    search: Dict[str, Any] = {}             # {keywords, synonyms, facets}
    
    # ────── SCORES & CLASSEMENT ──────
    scores: Optional[ProductScores] = None  # Nouveau format
    # Rétrocompatibilité
    ranking: Dict[str, Any] = {}            # {quality_score, ...}
    featured: bool = False
    
    # ────── DONNÉES IA ──────
    ai_data: Optional[ProductAI] = None     # Nouveau format
    # Rétrocompatibilité
    ai: Dict[str, Any] = {}                 # {summary, bullets, ...}
    
    # ────── MÉTADONNÉES ──────
    meta: Optional[ProductMeta] = None      # Nouveau format
    # Rétrocompatibilité
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    scraped_source: Optional[str] = None
    fournisseur: Optional[str] = None
    active: bool = True
    schema_version: str = "v3_universal"
    
    # ────── AUTRES (usage legacy) ──────
    usage: Optional[str] = None
    original_image_url: Optional[str] = None
    image_migrated_at: Optional[str] = None
    data_enriched_at: Optional[str] = None

    class Config:
        extra = "allow"  # Permet les champs additionnels pour flexibilité


# ══════════════════════════════════════════════════════════════
# MODÈLES POUR API RESPONSES
# ══════════════════════════════════════════════════════════════

class ProductListItem(BaseModel):
    """Version légère pour listes"""
    id: str
    name: str
    brand: Optional[str] = None
    price: Optional[float] = None
    prices: Optional[ProductPrices] = None
    primary_image_url: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    in_stock: bool = True
    scores: Optional[ProductScores] = None
    

class ProductDetail(Product):
    """Version complète avec données calculées"""
    related_products: List[ProductListItem] = []
    price_comparison: List[PriceSource] = []


class ProductSearchResult(BaseModel):
    """Résultat de recherche"""
    products: List[ProductListItem]
    total: int
    page: int
    limit: int
    filters_applied: Dict[str, Any] = {}


# ══════════════════════════════════════════════════════════════
# TEMPLATES DE SPECS PAR CATÉGORIE
# ══════════════════════════════════════════════════════════════

class SpecTemplate(BaseModel):
    """Template de spécification pour une catégorie"""
    key: str
    label: str
    label_fr: Optional[str] = None
    unit: Optional[str] = None
    type: str = "string"                   # string, number, boolean, array
    required: bool = False
    comparable: bool = True
    filterable: bool = False
    options: List[str] = []                # Options pour select


class CategorySpecsTemplate(BaseModel):
    """Template de specs pour une catégorie"""
    category_id: str
    category_name: str
    specs_template: List[SpecTemplate] = []
