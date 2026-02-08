"""
Tests API Chatbot
"""
import pytest
import uuid

pytestmark = pytest.mark.asyncio


class TestChatbotAPI:
    """Tests pour l'API du chatbot"""
    
    async def test_chatbot_welcome_message(self, client):
        """Test: Message de bienvenue à l'ouverture"""
        session_id = f"test_{uuid.uuid4()}"
        
        response = await client.post("/chatbot/chat", json={
            "message": "start",
            "session_id": session_id
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert "session_id" in data
        assert "Bienvenue" in data["response"] or "Mar7bé" in data["response"]
        assert data["phase"] == "language_choice"
    
    async def test_chatbot_language_choice_french(self, client):
        """Test: Choix de la langue française"""
        session_id = f"test_{uuid.uuid4()}"
        
        # Start
        await client.post("/chatbot/chat", json={
            "message": "start",
            "session_id": session_id
        })
        
        # Choose French
        response = await client.post("/chatbot/chat", json={
            "message": "1",
            "session_id": session_id
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["phase"] == "mode_choice"
        assert "Comment puis-je t'aider" in data["response"]
    
    async def test_chatbot_language_choice_tunisian(self, client):
        """Test: Choix de la langue tunisienne"""
        session_id = f"test_{uuid.uuid4()}"
        
        # Start
        await client.post("/chatbot/chat", json={
            "message": "start",
            "session_id": session_id
        })
        
        # Choose Tunisian
        response = await client.post("/chatbot/chat", json={
            "message": "2",
            "session_id": session_id
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["phase"] == "mode_choice"
        assert "Kifech" in data["response"] or "n3awnek" in data["response"]
    
    async def test_chatbot_full_flow_order(self, client):
        """Test: Flow complet mode commande"""
        session_id = f"test_{uuid.uuid4()}"
        
        # Start -> French -> Mode 1
        await client.post("/chatbot/chat", json={"message": "start", "session_id": session_id})
        await client.post("/chatbot/chat", json={"message": "1", "session_id": session_id})
        
        response = await client.post("/chatbot/chat", json={
            "message": "1",
            "session_id": session_id
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["phase"] == "conversation"
        assert data["mode"] == "order"
    
    async def test_chatbot_full_flow_question(self, client):
        """Test: Flow complet mode question"""
        session_id = f"test_{uuid.uuid4()}"
        
        # Start -> French -> Mode 2
        await client.post("/chatbot/chat", json={"message": "start", "session_id": session_id})
        await client.post("/chatbot/chat", json={"message": "1", "session_id": session_id})
        
        response = await client.post("/chatbot/chat", json={
            "message": "2",
            "session_id": session_id
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["phase"] == "conversation"
        assert data["mode"] == "question"
    
    async def test_chatbot_full_flow_help(self, client):
        """Test: Flow complet mode aide"""
        session_id = f"test_{uuid.uuid4()}"
        
        # Start -> French -> Mode 3
        await client.post("/chatbot/chat", json={"message": "start", "session_id": session_id})
        await client.post("/chatbot/chat", json={"message": "1", "session_id": session_id})
        
        response = await client.post("/chatbot/chat", json={
            "message": "3",
            "session_id": session_id
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["phase"] == "conversation"
        assert data["mode"] == "help"


class TestChatbotConfig:
    """Tests pour la configuration du chatbot"""
    
    async def test_get_ai_models(self, client):
        """Test: Récupérer les modèles IA disponibles"""
        response = await client.get("/chatbot/admin/ai-models")
        assert response.status_code == 200
        
        data = response.json()
        assert "available_models" in data or "models" in data
    
    async def test_get_current_ai_model(self, client):
        """Test: Récupérer le modèle IA actuel"""
        response = await client.get("/chatbot/admin/ai-models")
        assert response.status_code == 200
        
        data = response.json()
        assert "current_model" in data
