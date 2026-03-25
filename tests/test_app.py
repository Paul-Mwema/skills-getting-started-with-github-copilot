import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

# Create a test client
client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities before each test"""
    # Store original state
    original_activities = {
        k: {"participants": v["participants"].copy()}
        for k, v in activities.items()
    }
    yield
    # Restore original state after test
    for activity_name, activity_data in activities.items():
        activities[activity_name]["participants"] = original_activities[activity_name]["participants"]


class TestGetActivities:
    """Test the GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self):
        """Arrange: No setup needed"""
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_get_activities_has_correct_structure(self):
        """Arrange: No setup needed"""
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


class TestSignup:
    """Test the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful(self, reset_activities):
        """Arrange: Prepare test data"""
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        assert email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count + 1

    def test_signup_nonexistent_activity(self, reset_activities):
        """Arrange: Invalid activity name"""
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_student(self, reset_activities):
        """Arrange: Student already signed up"""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_same_student_different_activities(self, reset_activities):
        """Arrange: Student signs up for multiple activities"""
        email = "testuser@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Programming Class"
        
        # Act
        response1 = client.post(f"/activities/{activity1}/signup?email={email}")
        response2 = client.post(f"/activities/{activity2}/signup?email={email}")
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email in activities[activity1]["participants"]
        assert email in activities[activity2]["participants"]


class TestUnregister:
    """Test the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_successful(self, reset_activities):
        """Arrange: Add student then remove"""
        activity_name = "Chess Club"
        email = "testuser@mergington.edu"
        
        # Sign up first
        client.post(f"/activities/{activity_name}/signup?email={email}")
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count - 1

    def test_unregister_nonexistent_activity(self, reset_activities):
        """Arrange: Invalid activity name"""
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_student_not_signed_up(self, reset_activities):
        """Arrange: Try to remove student not in activity"""
        activity_name = "Chess Club"
        email = "notstudent@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not signed up for this activity"

    def test_unregister_then_signup_again(self, reset_activities):
        """Arrange: Remove and re-add same student"""
        activity_name = "Chess Club"
        email = "testuser@mergington.edu"
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={email}")
        response_unregister = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        response_signup = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response_unregister.status_code == 200
        assert response_signup.status_code == 200
        assert email in activities[activity_name]["participants"]


class TestRoot:
    """Test the GET / endpoint"""

    def test_root_redirects_to_index(self):
        """Arrange: No setup needed"""
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
