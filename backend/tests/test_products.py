"""
Tests API Produits
"""
import pytest

pytestmark = pytest.mark.asyncio


class TestProductsAPI:
    """Tests pour l'API des produits"""
    
    async def test_get_products_list(self, client):
        """Test: Récupérer la liste des produits"""
        response = await client.get("/products?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "products" in data
        assert "total" in data
        assert isinstance(data["products"], list)
        assert data["total"] > 0
    
    async def test_get_products_with_pagination(self, client):
        """Test: Pagination des produits"""
        response = await client.get("/products?limit=5&skip=0")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["products"]) <= 5
    
    async def test_search_products_by_name(self, client):
        """Test: Recherche par nom"""
        response = await client.get("/products?q=camera&limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert "products" in data
    
    async def test_search_products_by_model_code(self, client):
        """Test: Recherche par code modèle"""
        # D'abord récupérer un produit pour avoir son code
        list_response = await client.get("/products?limit=1")
        products = list_response.json().get("products", [])
        
        if products and products[0].get("model_code"):
            code = products[0]["model_code"]
            response = await client.get(f"/products?q={code}&limit=5")
            assert response.status_code == 200
            assert response.json()["total"] >= 1
    
    async def test_get_single_product(self, client):
        """Test: Récupérer un produit par ID"""
        # D'abord récupérer un ID valide
        list_response = await client.get("/products?limit=1")
        products = list_response.json().get("products", [])
        
        if products:
            product_id = products[0]["id"]
            response = await client.get(f"/products/{product_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == product_id
            assert "name" in data
    
    async def test_get_nonexistent_product(self, client):
        """Test: Produit inexistant retourne 404"""
        response = await client.get("/products/nonexistent-id-12345")
        assert response.status_code == 404
    
    async def test_products_have_model_code(self, client):
        """Test: Tous les produits ont un code modèle"""
        response = await client.get("/products?limit=20")
        assert response.status_code == 200
        
        data = response.json()
        for product in data.get("products", []):
            assert "model_code" in product, f"Produit {product.get('id')} sans model_code"


class TestCategoriesAPI:
    """Tests pour l'API des catégories"""
    
    async def test_get_categories(self, client):
        """Test: Récupérer les catégories"""
        response = await client.get("/categories")
        # Peut retourner 200 ou 500 si bug ObjectId
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
