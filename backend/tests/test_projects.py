import pytest
from fastapi import status


def test_create_project(client):
    """Test creating a new project."""
    project_data = {
        "name": "Test Project",
        "description": "A test project",
        "goal": "Test the project creation",
        "acceptance_criteria": ["Criterion 1", "Criterion 2"],
        "risk_level": "low"
    }

    response = client.post("/api/projects/", json=project_data)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["name"] == project_data["name"]
    assert data["description"] == project_data["description"]
    assert data["goal"] == project_data["goal"]
    assert data["risk_level"] == "low"
    assert data["status"] == "draft"
    assert "id" in data


def test_list_projects(client):
    """Test listing projects."""
    # Create a project first
    project_data = {
        "name": "Test Project",
        "description": "A test project",
        "goal": "Test the project listing",
        "risk_level": "medium"
    }
    client.post("/api/projects/", json=project_data)

    # List projects
    response = client.get("/api/projects/")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "projects" in data
    assert "total" in data
    assert data["total"] >= 1
    assert len(data["projects"]) >= 1


def test_get_project(client):
    """Test getting a specific project."""
    # Create a project
    project_data = {
        "name": "Test Project",
        "description": "A test project",
        "goal": "Test getting a project",
        "risk_level": "high"
    }
    create_response = client.post("/api/projects/", json=project_data)
    project_id = create_response.json()["id"]

    # Get the project
    response = client.get(f"/api/projects/{project_id}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == project_data["name"]


def test_update_project(client):
    """Test updating a project."""
    # Create a project
    project_data = {
        "name": "Test Project",
        "description": "A test project",
        "goal": "Test updating a project",
        "risk_level": "low"
    }
    create_response = client.post("/api/projects/", json=project_data)
    project_id = create_response.json()["id"]

    # Update the project
    update_data = {
        "name": "Updated Project",
        "status": "planning"
    }
    response = client.patch(f"/api/projects/{project_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["name"] == "Updated Project"
    assert data["status"] == "planning"


def test_delete_project(client):
    """Test deleting a project."""
    # Create a project
    project_data = {
        "name": "Test Project",
        "description": "A test project",
        "goal": "Test deleting a project",
        "risk_level": "low"
    }
    create_response = client.post("/api/projects/", json=project_data)
    project_id = create_response.json()["id"]

    # Delete the project
    response = client.delete(f"/api/projects/{project_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify deletion
    get_response = client.get(f"/api/projects/{project_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_generate_plan(client):
    """Test generating a plan for a project."""
    # Create a project
    project_data = {
        "name": "Test Project",
        "description": "Build a simple web app",
        "goal": "Create a working web application",
        "acceptance_criteria": ["Working frontend", "Working backend", "Tests pass"],
        "risk_level": "medium"
    }
    create_response = client.post("/api/projects/", json=project_data)
    project_id = create_response.json()["id"]

    # Generate plan
    response = client.post(f"/api/projects/{project_id}/generate-plan")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "task_count" in data
    assert data["task_count"] > 0
    assert "estimated_total_hours" in data


def test_get_audit_log(client):
    """Test getting audit log for a project."""
    # Create a project
    project_data = {
        "name": "Test Project",
        "description": "A test project",
        "goal": "Test audit logging",
        "risk_level": "low"
    }
    create_response = client.post("/api/projects/", json=project_data)
    project_id = create_response.json()["id"]

    # Get audit log
    response = client.get(f"/api/projects/{project_id}/audit-log")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "logs" in data
    assert len(data["logs"]) >= 1  # At least project_created event
    assert data["logs"][0]["action"] == "project_created"


def test_get_nonexistent_project(client):
    """Test getting a project that doesn't exist."""
    response = client.get("/api/projects/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
