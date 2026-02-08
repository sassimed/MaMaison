"""
Configuration des tests - Fixtures partagées
Tests via HTTP externe (pas ASGI direct)
"""
import pytest
import asyncio
import httpx
import os

# URL de l'API
API_BASE_URL = os.environ.get("API_URL", "http://localhost:8001/api")

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def client():
    """Client HTTP asynchrone pour les tests"""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as ac:
        yield ac

@pytest.fixture
def migration_key():
    """Clé de migration pour les tests"""
    return os.environ.get("MIGRATION_KEY", "mydar-migration-2026")

@pytest.fixture
def test_user():
    """Utilisateur de test"""
    return {
        "email": "test@mydar.tn",
        "password": "test123",
        "name": "Test User"
    }

@pytest.fixture
def admin_user():
    """Admin de test"""
    return {
        "email": "admin@mydar.tn",
        "password": "admin123"
    }
