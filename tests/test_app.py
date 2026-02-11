import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

# Create a test client
client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Basketball Club": {
            "description": "Practice basketball skills and compete in games",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": []
        },
        "Tennis Club": {
            "description": "Develop tennis technique and play matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 10,
            "participants": []
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        }
    }
    
    # Clear and restore
    activities.clear()
    activities.update(original_activities)
    yield
    # Cleanup
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Test cases for fetching activities"""
    
    def test_get_activities_success(self, reset_activities):
        """Test that activities endpoint returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Basketball Club" in data
    
    def test_get_activities_structure(self, reset_activities):
        """Test that activity objects have correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
    
    def test_get_activities_participants(self, reset_activities):
        """Test that participants list is correct"""
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignup:
    """Test cases for signing up for activities"""
    
    def test_signup_success(self, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball%20Club/signup",
            params={"email": "john@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "john@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "john@mergington.edu" in activities_data["Basketball Club"]["participants"]
    
    def test_signup_nonexistent_activity(self, reset_activities):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/NonExistent/signup",
            params={"email": "john@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate(self, reset_activities):
        """Test that a student cannot sign up twice for same activity"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_multiple_activities(self, reset_activities):
        """Test that a student can sign up for multiple activities"""
        # Sign up for first activity
        response1 = client.post(
            "/activities/Basketball%20Club/signup",
            params={"email": "alex@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Sign up for second activity
        response2 = client.post(
            "/activities/Tennis%20Club/signup",
            params={"email": "alex@mergington.edu"}
        )
        assert response2.status_code == 200
        
        # Verify both signups
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "alex@mergington.edu" in activities_data["Basketball Club"]["participants"]
        assert "alex@mergington.edu" in activities_data["Tennis Club"]["participants"]


class TestUnregister:
    """Test cases for unregistering from activities"""
    
    def test_unregister_success(self, reset_activities):
        """Test successful unregistration from an activity"""
        response = client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_activity(self, reset_activities):
        """Test unregister from non-existent activity"""
        response = client.delete(
            "/activities/NonExistent/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_not_registered(self, reset_activities):
        """Test unregister for student not in activity"""
        response = client.delete(
            "/activities/Basketball%20Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_removes_participant(self, reset_activities):
        """Test that unregister properly removes participant"""
        # First add a participant
        client.post(
            "/activities/Basketball%20Club/signup",
            params={"email": "testuser@mergington.edu"}
        )
        
        # Verify they're added
        activities_response = client.get("/activities")
        assert "testuser@mergington.edu" in activities_response.json()["Basketball Club"]["participants"]
        
        # Now unregister
        response = client.delete(
            "/activities/Basketball%20Club/unregister",
            params={"email": "testuser@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Verify they're removed
        activities_response = client.get("/activities")
        assert "testuser@mergington.edu" not in activities_response.json()["Basketball Club"]["participants"]


class TestIntegration:
    """Integration tests combining multiple operations"""
    
    def test_full_workflow(self, reset_activities):
        """Test complete workflow: signup, view, unregister"""
        email = "workflow@mergington.edu"
        activity = "Tennis%20Club"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Get activities and verify signup
        activities_response = client.get("/activities")
        assert email in activities_response.json()["Tennis Club"]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistered
        final_response = client.get("/activities")
        assert email not in final_response.json()["Tennis Club"]["participants"]
    
    def test_multiple_participants_management(self, reset_activities):
        """Test managing multiple participants in same activity"""
        activity = "Basketball%20Club"
        users = [f"user{i}@mergington.edu" for i in range(3)]
        
        # Sign up multiple users
        for user in users:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": user}
            )
            assert response.status_code == 200
        
        # Verify all signed up
        activities_response = client.get("/activities")
        participants = activities_response.json()["Basketball Club"]["participants"]
        for user in users:
            assert user in participants
        
        # Unregister one user
        client.delete(
            f"/activities/{activity}/unregister",
            params={"email": users[1]}
        )
        
        # Verify one removed but others remain
        activities_response = client.get("/activities")
        participants = activities_response.json()["Basketball Club"]["participants"]
        assert users[0] in participants
        assert users[1] not in participants
        assert users[2] in participants
