"""
Tests for Categories V2 API - Testing slug-based IDs and product filtering
Tests the fix for category filtering by slug instead of MongoDB ObjectIds
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://smartshop-ai-19.preview.emergentagent.com').rstrip('/')


class TestCategoriesV2API:
    """Tests for the Categories V2 API - slug-based IDs"""
    
    def test_get_categories_returns_slugs_as_ids(self):
        """Test: GET /api/categories returns slugs as IDs (not MongoDB ObjectIds)"""
        response = requests.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Should have at least one category"
        
        # Check first category has slug-based ID
        first_cat = data[0]
        assert "id" in first_cat, "Category should have 'id' field"
        assert "slug" in first_cat, "Category should have 'slug' field"
        assert "mongo_id" in first_cat, "Category should have 'mongo_id' field for reference"
        
        # ID should be the slug (not a MongoDB ObjectId)
        assert first_cat["id"] == first_cat["slug"], f"ID should equal slug: {first_cat['id']} != {first_cat['slug']}"
        
        # ID should NOT look like a MongoDB ObjectId (24 hex chars)
        assert len(first_cat["id"]) != 24 or not all(c in '0123456789abcdef' for c in first_cat["id"]), \
            f"ID should not be a MongoDB ObjectId: {first_cat['id']}"
    
    def test_categories_have_subcategories(self):
        """Test: Categories include subcategories with slug-based IDs"""
        response = requests.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200
        
        data = response.json()
        
        # Find a category with subcategories
        cat_with_subs = None
        for cat in data:
            if cat.get("subcategories") and len(cat["subcategories"]) > 0:
                cat_with_subs = cat
                break
        
        assert cat_with_subs is not None, "Should have at least one category with subcategories"
        
        # Check subcategory structure
        first_sub = cat_with_subs["subcategories"][0]
        assert "id" in first_sub, "Subcategory should have 'id' field"
        assert "slug" in first_sub, "Subcategory should have 'slug' field"
        assert "label" in first_sub, "Subcategory should have 'label' field"
        
        # Subcategory ID should be slug-based (format: parent__child)
        assert "__" in first_sub["id"], f"Subcategory ID should contain '__': {first_sub['id']}"
    
    def test_get_category_children(self):
        """Test: GET /api/categories/{category_id}/children returns subcategories"""
        # First get a parent category
        response = requests.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200
        
        data = response.json()
        parent_cat = None
        for cat in data:
            if cat.get("has_children"):
                parent_cat = cat
                break
        
        assert parent_cat is not None, "Should have at least one category with children"
        
        # Get children using slug
        children_response = requests.get(f"{BASE_URL}/api/categories/{parent_cat['slug']}/children")
        assert children_response.status_code == 200, f"Expected 200, got {children_response.status_code}"
        
        children_data = children_response.json()
        assert "parent" in children_data, "Response should have 'parent' field"
        assert "children" in children_data, "Response should have 'children' field"
        assert "total" in children_data, "Response should have 'total' field"
        
        # Verify parent info
        assert children_data["parent"]["id"] == parent_cat["slug"], "Parent ID should match slug"
        
        # Verify children have slug-based IDs
        if len(children_data["children"]) > 0:
            first_child = children_data["children"][0]
            assert "id" in first_child, "Child should have 'id' field"
            assert "slug" in first_child, "Child should have 'slug' field"
            assert first_child["id"] == first_child["slug"], "Child ID should equal slug"
    
    def test_alarme_category_children(self):
        """Test: GET /api/categories/alarme/children returns correct subcategories"""
        response = requests.get(f"{BASE_URL}/api/categories/alarme/children")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["parent"]["id"] == "alarme", "Parent should be 'alarme'"
        assert len(data["children"]) > 0, "Alarme should have subcategories"
        
        # Check for expected subcategories
        child_ids = [c["id"] for c in data["children"]]
        expected_subs = ["alarme__detecteurs-contacts", "alarme__centrales-d-alarme"]
        
        for expected in expected_subs:
            assert expected in child_ids, f"Expected subcategory '{expected}' not found in {child_ids}"


class TestProductsFilteringByCategory:
    """Tests for product filtering by category using slugs"""
    
    def test_filter_products_by_parent_category(self):
        """Test: GET /api/products?category=alarme filters by parent category"""
        response = requests.get(f"{BASE_URL}/api/products?category=alarme&limit=10")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "products" in data, "Response should have 'products' field"
        assert "total" in data, "Response should have 'total' field"
        assert data["total"] > 0, "Should have products in Alarme category"
        
        # Verify products are from Alarme category
        for product in data["products"]:
            # Products should have category_path_ids containing 'alarme'
            category_path = product.get("category_path_ids", [])
            category_label = product.get("category", "").lower()
            
            assert "alarme" in category_path or "alarme" in category_label, \
                f"Product {product.get('name')} should be in Alarme category"
    
    def test_filter_products_by_subcategory(self):
        """Test: GET /api/products?category_id=alarme__detecteurs-contacts filters by subcategory"""
        response = requests.get(f"{BASE_URL}/api/products?category_id=alarme__detecteurs-contacts&limit=10")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "products" in data, "Response should have 'products' field"
        assert data["total"] > 0, "Should have products in Détecteurs & Contacts subcategory"
        
        # Verify products are from the correct subcategory
        for product in data["products"]:
            category_id = product.get("category_id", "")
            subcategory_label = product.get("subcategory_label", "").lower()
            
            # Product should be in detecteurs-contacts subcategory
            assert "detecteurs" in category_id.lower() or "détecteurs" in subcategory_label or "contacts" in subcategory_label, \
                f"Product {product.get('name')} should be in Détecteurs & Contacts subcategory"
    
    def test_filter_products_by_videosurveillance(self):
        """Test: GET /api/products?category=videosurveillance filters correctly"""
        response = requests.get(f"{BASE_URL}/api/products?category=videosurveillance&limit=10")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["total"] > 0, "Should have products in Vidéosurveillance category"
    
    def test_products_response_structure(self):
        """Test: Products response has correct structure"""
        response = requests.get(f"{BASE_URL}/api/products?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check response structure
        assert "products" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "total_pages" in data
        assert "has_more" in data
        
        # Check product structure
        if len(data["products"]) > 0:
            product = data["products"][0]
            assert "id" in product or "sku" in product, "Product should have identifier"
            assert "name" in product, "Product should have name"


class TestAdminCategoriesAPI:
    """Tests for Admin Categories API"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@mydar.tn", "password": "admin123"}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    def test_admin_categories_requires_auth(self):
        """Test: GET /api/admin/categories requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/categories")
        assert response.status_code in [401, 403], f"Should require authentication, got {response.status_code}"
    
    def test_admin_categories_returns_subcategories(self, admin_token):
        """Test: GET /api/admin/categories returns categories with subcategories"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Should have categories"
        
        # Check category structure
        first_cat = data[0]
        assert "id" in first_cat, "Category should have 'id'"
        assert "name" in first_cat or "label" in first_cat, "Category should have name/label"
        assert "subcategories" in first_cat, "Category should have 'subcategories' field"
        
        # Find a category with subcategories
        cat_with_subs = None
        for cat in data:
            if cat.get("subcategories") and len(cat["subcategories"]) > 0:
                cat_with_subs = cat
                break
        
        assert cat_with_subs is not None, "Should have at least one category with subcategories"
        
        # Check subcategory structure
        first_sub = cat_with_subs["subcategories"][0]
        assert "id" in first_sub, "Subcategory should have 'id'"
        assert "name" in first_sub or "label" in first_sub, "Subcategory should have name/label"
        assert "product_count" in first_sub, "Subcategory should have 'product_count'"
    
    def test_admin_products_filter_by_category(self, admin_token):
        """Test: GET /api/admin/products-manage?category=Alarme filters products"""
        response = requests.get(
            f"{BASE_URL}/api/admin/products-manage?category=Alarme&limit=5",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Response should have 'items' field"
        
        # Verify products are from Alarme category
        for item in data["items"]:
            category_label = item.get("category_label", "").lower()
            category = item.get("category", "").lower()
            
            assert "alarme" in category_label or "alarme" in category, \
                f"Product {item.get('name')} should be in Alarme category"


class TestCategoryBreadcrumb:
    """Tests for category breadcrumb API"""
    
    def test_get_category_breadcrumb(self):
        """Test: GET /api/categories/{category_id}/breadcrumb returns path"""
        response = requests.get(f"{BASE_URL}/api/categories/alarme/breadcrumb")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "breadcrumb" in data, "Response should have 'breadcrumb' field"
        assert len(data["breadcrumb"]) > 0, "Breadcrumb should have at least one item"
        
        # First item should be the category itself
        first_item = data["breadcrumb"][0]
        assert "id" in first_item, "Breadcrumb item should have 'id'"
        assert "label" in first_item, "Breadcrumb item should have 'label'"


class TestCategoryTree:
    """Tests for category tree API"""
    
    def test_get_category_tree(self):
        """Test: GET /api/categories/tree returns hierarchical structure"""
        response = requests.get(f"{BASE_URL}/api/categories/tree")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "tree" in data, "Response should have 'tree' field"
        assert isinstance(data["tree"], list), "Tree should be a list"
        
        # Check tree structure
        if len(data["tree"]) > 0:
            root = data["tree"][0]
            assert "id" in root, "Tree node should have 'id'"
            assert "label" in root, "Tree node should have 'label'"
            assert "children" in root, "Tree node should have 'children'"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
