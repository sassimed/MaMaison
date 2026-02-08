"""
Tests API Authentification
"""
import pytest

pytestmark = pytest.mark.asyncio


class TestAuthAPI:
    """Tests pour l'authentification"""
    
    async def test_login_missing_fields(self, client):
        """Test: Login sans email retourne erreur validation"""
        response = await client.post("/auth/login", json={
            "password": "test"
        })
        assert response.status_code == 422
    
    async def test_login_with_invalid_credentials(self, client):
        """Test: Login avec mauvais credentials"""
        response = await client.post("/auth/login", json={
            "email": "fake@fake.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 404]
