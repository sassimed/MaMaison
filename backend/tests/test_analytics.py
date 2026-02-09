"""
Analytics Module API Tests
Tests for tracking events and admin analytics endpoints
"""

import pytest
import requests
import os
import time
import uuid

# Use localhost for tests running on the backend server
BASE_URL = os.environ.get('TEST_API_URL', 'http://localhost:8001')

class TestAnalyticsTracking:
    """Tests for analytics tracking endpoints"""
    
    def test_track_page_view_event(self):
        """Test POST /api/analytics/track for page_view event"""
        response = requests.post(f"{BASE_URL}/api/analytics/track", json={
            "event_type": "page_view",
            "page_url": "https://test.com/test-page",
            "page_title": "Test Page"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "session_id" in data
        assert "visitor_id" in data
        assert data["session_id"].startswith("sess_")
    
    def test_track_product_view_event(self):
        """Test POST /api/analytics/track for product_view event"""
        response = requests.post(f"{BASE_URL}/api/analytics/track", json={
            "event_type": "product_view",
            "page_url": "https://test.com/product/123",
            "product_id": "test-product-123",
            "product_name": "Test Product"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_track_search_event(self):
        """Test POST /api/analytics/track for search event"""
        response = requests.post(f"{BASE_URL}/api/analytics/track", json={
            "event_type": "search",
            "page_url": "https://test.com/catalog",
            "search_query": "camera wifi"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_track_add_to_cart_event(self):
        """Test POST /api/analytics/track for add_to_cart event"""
        response = requests.post(f"{BASE_URL}/api/analytics/track", json={
            "event_type": "add_to_cart",
            "page_url": "https://test.com/product/123",
            "product_id": "test-product-123",
            "product_name": "Test Product",
            "metadata": {"quantity": 2}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_track_login_event(self):
        """Test POST /api/analytics/track for login event"""
        response = requests.post(f"{BASE_URL}/api/analytics/track", json={
            "event_type": "login",
            "page_url": "https://test.com/login",
            "user_id": "test-user-123",
            "metadata": {"method": "email"}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_track_event_with_utm_params(self):
        """Test POST /api/analytics/track with UTM parameters"""
        response = requests.post(f"{BASE_URL}/api/analytics/track", json={
            "event_type": "page_view",
            "page_url": "https://test.com/landing",
            "utm_source": "facebook",
            "utm_medium": "social",
            "utm_campaign": "summer_sale"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True


class TestAnalyticsHeartbeat:
    """Tests for heartbeat endpoint"""
    
    def test_heartbeat_basic(self):
        """Test POST /api/analytics/heartbeat"""
        session_id = f"sess_test_{uuid.uuid4().hex[:8]}"
        response = requests.post(f"{BASE_URL}/api/analytics/heartbeat", json={
            "session_id": session_id,
            "current_page": "/test-page"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_heartbeat_with_user_id(self):
        """Test POST /api/analytics/heartbeat with user_id"""
        session_id = f"sess_test_{uuid.uuid4().hex[:8]}"
        response = requests.post(f"{BASE_URL}/api/analytics/heartbeat", json={
            "session_id": session_id,
            "user_id": "test-user-heartbeat",
            "current_page": "/dashboard"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True


class TestAdminStats:
    """Tests for admin statistics endpoints"""
    
    def test_get_stats_default_range(self):
        """Test GET /api/analytics/admin/stats with default 7d range"""
        response = requests.get(f"{BASE_URL}/api/analytics/admin/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Verify summary structure
        assert "summary" in data
        summary = data["summary"]
        assert "total_events" in summary
        assert "page_views" in summary
        assert "unique_visitors" in summary
        assert "unique_sessions" in summary
        assert "avg_pages_per_session" in summary
        
        # Verify other fields
        assert "daily_stats" in data
        assert "top_pages" in data
        assert "traffic_sources" in data
        assert "devices" in data
        assert "browsers" in data
        assert "countries" in data
        assert "date_range" in data
    
    def test_get_stats_24h_range(self):
        """Test GET /api/analytics/admin/stats with 24h range"""
        response = requests.get(f"{BASE_URL}/api/analytics/admin/stats?range=24h")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
    
    def test_get_stats_30d_range(self):
        """Test GET /api/analytics/admin/stats with 30d range"""
        response = requests.get(f"{BASE_URL}/api/analytics/admin/stats?range=30d")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
    
    def test_get_stats_90d_range(self):
        """Test GET /api/analytics/admin/stats with 90d range"""
        response = requests.get(f"{BASE_URL}/api/analytics/admin/stats?range=90d")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data


class TestOnlineUsers:
    """Tests for online users endpoint"""
    
    def test_get_online_users(self):
        """Test GET /api/analytics/admin/online-users"""
        response = requests.get(f"{BASE_URL}/api/analytics/admin/online-users")
        assert response.status_code == 200
        data = response.json()
        
        assert "online_users" in data
        assert "online_users_count" in data
        assert "total_active_sessions" in data
        assert "threshold_minutes" in data
        
        # Verify types
        assert isinstance(data["online_users"], list)
        assert isinstance(data["online_users_count"], int)
        assert isinstance(data["total_active_sessions"], int)
        assert data["threshold_minutes"] == 5


class TestEventsAuditTrail:
    """Tests for events audit trail endpoint"""
    
    def test_get_events_default(self):
        """Test GET /api/analytics/admin/events with defaults"""
        response = requests.get(f"{BASE_URL}/api/analytics/admin/events")
        assert response.status_code == 200
        data = response.json()
        
        assert "events" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "pages" in data
        
        assert isinstance(data["events"], list)
        assert data["page"] == 1
        assert data["limit"] == 50
    
    def test_get_events_with_range(self):
        """Test GET /api/analytics/admin/events with range filter"""
        response = requests.get(f"{BASE_URL}/api/analytics/admin/events?range=7d")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
    
    def test_get_events_with_event_type_filter(self):
        """Test GET /api/analytics/admin/events with event_type filter"""
        response = requests.get(f"{BASE_URL}/api/analytics/admin/events?event_type=page_view")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        # All events should be page_view type
        for event in data["events"]:
            assert event["event_type"] == "page_view"
    
    def test_get_events_with_pagination(self):
        """Test GET /api/analytics/admin/events with pagination"""
        response = requests.get(f"{BASE_URL}/api/analytics/admin/events?page=1&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 10
        assert len(data["events"]) <= 10


class TestUserTimeline:
    """Tests for user timeline endpoint"""
    
    def test_get_user_timeline_existing_user(self):
        """Test GET /api/analytics/admin/user-timeline/{user_id} for existing user"""
        # First, get an existing user ID from online users
        online_response = requests.get(f"{BASE_URL}/api/analytics/admin/online-users")
        if online_response.status_code == 200:
            online_data = online_response.json()
            if online_data["online_users"]:
                user_id = online_data["online_users"][0]["user_id"]
                response = requests.get(f"{BASE_URL}/api/analytics/admin/user-timeline/{user_id}")
                assert response.status_code == 200
                data = response.json()
                
                assert "user" in data
                assert "total_events" in data
                assert "sessions" in data
                assert "session_count" in data
                return
        
        # If no online users, test with a known admin user ID
        response = requests.get(f"{BASE_URL}/api/analytics/admin/user-timeline/1c108e62-780d-4b50-bf28-cfae6fcf3599")
        assert response.status_code == 200
        data = response.json()
        assert "total_events" in data
        assert "sessions" in data
    
    def test_get_user_timeline_nonexistent_user(self):
        """Test GET /api/analytics/admin/user-timeline/{user_id} for non-existent user"""
        response = requests.get(f"{BASE_URL}/api/analytics/admin/user-timeline/nonexistent-user-id")
        assert response.status_code == 200
        data = response.json()
        # Should return empty data for non-existent user
        assert data["user"] is None
        assert data["total_events"] == 0


class TestTopProducts:
    """Tests for top products endpoint"""
    
    def test_get_top_products_default(self):
        """Test GET /api/analytics/admin/top-products with defaults"""
        response = requests.get(f"{BASE_URL}/api/analytics/admin/top-products")
        assert response.status_code == 200
        data = response.json()
        
        assert "top_products" in data
        assert "date_range" in data
        assert isinstance(data["top_products"], list)
    
    def test_get_top_products_with_range(self):
        """Test GET /api/analytics/admin/top-products with range"""
        response = requests.get(f"{BASE_URL}/api/analytics/admin/top-products?range=30d")
        assert response.status_code == 200
        data = response.json()
        assert data["date_range"] == "30d"
    
    def test_get_top_products_with_limit(self):
        """Test GET /api/analytics/admin/top-products with limit"""
        response = requests.get(f"{BASE_URL}/api/analytics/admin/top-products?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["top_products"]) <= 5


class TestSearchTerms:
    """Tests for search terms endpoint"""
    
    def test_get_search_terms_default(self):
        """Test GET /api/analytics/admin/search-terms with defaults"""
        response = requests.get(f"{BASE_URL}/api/analytics/admin/search-terms")
        assert response.status_code == 200
        data = response.json()
        
        assert "search_terms" in data
        assert "date_range" in data
        assert isinstance(data["search_terms"], list)
    
    def test_get_search_terms_with_range(self):
        """Test GET /api/analytics/admin/search-terms with range"""
        response = requests.get(f"{BASE_URL}/api/analytics/admin/search-terms?range=30d")
        assert response.status_code == 200
        data = response.json()
        assert data["date_range"] == "30d"


class TestEndSession:
    """Tests for end session endpoint"""
    
    def test_end_session(self):
        """Test POST /api/analytics/end-session"""
        # First create a session
        track_response = requests.post(f"{BASE_URL}/api/analytics/track", json={
            "event_type": "page_view",
            "page_url": "https://test.com/end-session-test"
        })
        session_id = track_response.json()["session_id"]
        
        # End the session
        response = requests.post(f"{BASE_URL}/api/analytics/end-session?session_id={session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
