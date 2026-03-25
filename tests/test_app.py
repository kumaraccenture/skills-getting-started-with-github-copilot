import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns status 200"""
        # Arrange
        # No setup needed - endpoint doesn't require parameters
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary"""
        # Arrange
        # No setup needed
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert isinstance(response.json(), dict)
    
    def test_get_activities_returns_activity_details(self, client):
        """Test that activities contain required fields"""
        # Arrange
        expected_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            for field in expected_fields:
                assert field in activity_data, f"Missing field '{field}' in {activity_name}"
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client, reset_activities):
        """Test successful signup for an activity"""
        # Arrange
        activity_name = "Basketball"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in response.json()["message"]
    
    def test_signup_updates_participants_list(self, client, reset_activities):
        """Test that signup adds student to participants list"""
        # Arrange
        activity_name = "Basketball"
        email = "newstudent@mergington.edu"
        
        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        response = client.get("/activities")
        
        # Assert
        activities = response.json()
        assert email in activities[activity_name]["participants"]
    
    def test_signup_duplicate_registration(self, client, reset_activities):
        """Test that attempting duplicate signup fails"""
        # Arrange
        activity_name = "Basketball"
        email = "james@mergington.edu"  # Already registered in Basketball
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "Already registered" in response.json()["detail"]
    
    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity"""
        # Arrange
        activity_name = "NonExistentActivity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_activity_full(self, client, reset_activities):
        """Test signup fails when activity is at max capacity"""
        # Arrange
        activity_name = "Tennis Club"
        response = client.get("/activities")
        tennis = response.json()[activity_name]
        max_participants = tennis["max_participants"]
        current_count = len(tennis["participants"])
        spots_available = max_participants - current_count
        
        # Fill remaining spots
        for i in range(spots_available):
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": f"filler{i}@mergington.edu"}
            )
        
        # Act - Try to sign up when full
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "fullstudent@mergington.edu"}
        )
        
        # Assert
        assert response.status_code == 400
        assert "Activity is full" in response.json()["detail"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successful(self, client, reset_activities):
        """Test successful unregistration from activity"""
        # Arrange
        activity_name = "Basketball"
        email = "james@mergington.edu"  # Already in Basketball
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister removes student from participants"""
        # Arrange
        activity_name = "Basketball"
        email = "james@mergington.edu"
        
        # Act
        client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        response = client.get("/activities")
        
        # Assert
        activities = response.json()
        assert email not in activities[activity_name]["participants"]
    
    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity"""
        # Arrange
        activity_name = "NonExistentActivity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_student_not_registered(self, client, reset_activities):
        """Test unregister fails when student not registered"""
        # Arrange
        activity_name = "Basketball"
        email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]


class TestIntegration:
    """Integration tests combining multiple operations"""
    
    def test_signup_then_unregister(self, client, reset_activities):
        """Test full cycle: signup and then unregister"""
        # Arrange
        activity_name = "Basketball"
        email = "integrationtest@mergington.edu"
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Assert - Verify signup
        response = client.get("/activities")
        assert email in response.json()[activity_name]["participants"]
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert - Response successful
        assert unregister_response.status_code == 200
        
        # Assert - Verify unregister
        response = client.get("/activities")
        assert email not in response.json()[activity_name]["participants"]
    
    def test_multiple_signups_increase_participant_count(self, client, reset_activities):
        """Test that multiple signups correctly increase participant count"""
        # Arrange
        activity_name = "Art Studio"
        emails = [
            "artist1@mergington.edu",
            "artist2@mergington.edu",
            "artist3@mergington.edu"
        ]
        response = client.get("/activities")
        initial_count = len(response.json()[activity_name]["participants"])
        
        # Act - Sign up multiple students
        for email in emails:
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
        
        # Assert - Verify count increased correctly
        response = client.get("/activities")
        final_count = len(response.json()[activity_name]["participants"])
        assert final_count == initial_count + len(emails)
        
        for email in emails:
            assert email in response.json()[activity_name]["participants"]
