"""
Configuration des tests - Fixtures partagées
Tests via HTTP externe pour éviter les problèmes d'event loop
"""
import pytest
import asyncio
import httpx
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# URL de l'API
API_BASE_URL = os.environ.get("API_URL", "http://localhost:8001/api")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    """Client HTTP asynchrone pour les tests"""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as ac:
        yield ac


@pytest.fixture
def sync_client():
    """Client HTTP synchrone pour les tests"""
    with httpx.Client(base_url=API_BASE_URL, timeout=30.0) as client:
        yield client


# ============ CREDENTIALS FIXTURES ============

@pytest.fixture
def admin_credentials():
    """Admin user credentials"""
    return {
        "email": "admin@mydar.tn",
        "password": "admin123"
    }


@pytest.fixture
def pro_credentials():
    """Professional user credentials"""
    return {
        "email": "pro@mydar.tn",
        "password": "pro123"
    }


@pytest.fixture
def client_credentials():
    """Client user credentials"""
    return {
        "email": "client@mydar.tn",
        "password": "client123"
    }


@pytest.fixture
async def admin_token(client, admin_credentials) -> str:
    """Get admin authentication token"""
    response = await client.post("/auth/login", json=admin_credentials)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None


@pytest.fixture
async def pro_token(client, pro_credentials) -> str:
    """Get professional authentication token"""
    response = await client.post("/auth/login", json=pro_credentials)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None


@pytest.fixture
async def client_token(client, client_credentials) -> str:
    """Get client authentication token"""
    response = await client.post("/auth/login", json=client_credentials)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None


# ============ DATA FIXTURES ============

@pytest.fixture
async def sample_product(client):
    """Get a sample product from API"""
    response = await client.get("/products?limit=1")
    if response.status_code == 200:
        data = response.json()
        if data.get("products"):
            return data["products"][0]
    return None


@pytest.fixture
async def sample_category(client):
    """Get a sample category from API"""
    response = await client.get("/categories")
    if response.status_code == 200:
        data = response.json()
        if data and len(data) > 0:
            return data[0]
    return None


@pytest.fixture
def test_user_data():
    """Test user registration data"""
    import uuid
    return {
        "email": f"test_{uuid.uuid4().hex[:8]}@test.com",
        "password": "TestPass123!",
        "full_name": "Test User",
        "phone": "+216 50 000 000",
        "role": "PARTICULIER"
    }


@pytest.fixture
def migration_key():
    """Migration key for admin operations"""
    return os.environ.get("MIGRATION_KEY", "mydar-migration-2026")


# ============ UTILITY FUNCTIONS ============

def assert_valid_response(response, expected_status=200):
    """Assert response is valid with expected status"""
    assert response.status_code == expected_status, \
        f"Expected {expected_status}, got {response.status_code}: {response.text}"
