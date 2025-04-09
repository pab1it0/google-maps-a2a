import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json
import uuid
from datetime import datetime

from main import app

client = TestClient(app)

# Mock API key for testing
TEST_API_KEY = "test_api_key"

# Replace the verify_api_key dependency
@pytest.fixture(autouse=True)
def mock_verify_api_key():
    with patch("main.verify_api_key", return_value=TEST_API_KEY):
        yield

# Mock Google Maps client
@pytest.fixture
def mock_google_maps_client():
    async_mock = AsyncMock()
    with patch("main.google_maps_client", return_value=AsyncMock(
        __aenter__=AsyncMock(return_value=async_mock),
        __aexit__=AsyncMock()
    )):
        yield async_mock

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "version" in response.json()

def test_get_agent_card():
    response = client.get("/agent-card")
    assert response.status_code == 200
    agent_card = response.json()
    assert agent_card["name"] == "Google Maps A2A"
    assert len(agent_card["tasks"]) > 0

def test_create_task():
    task_data = {
        "id": str(uuid.uuid4()),
        "type": "geocode",
        "status": "created",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "input": {
            "format": "text",
            "content": "1600 Amphitheatre Parkway, Mountain View, CA"
        }
    }
    
    response = client.post(
        "/tasks", 
        json=task_data,
        headers={"X-API-Key": TEST_API_KEY}
    )
    
    assert response.status_code == 200
    created_task = response.json()
    assert created_task["id"] == task_data["id"]
    assert created_task["type"] == "geocode"
    assert created_task["status"] == "created"

def test_get_task():
    # First create a task
    task_id = str(uuid.uuid4())
    task_data = {
        "id": task_id,
        "type": "geocode",
        "status": "created",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "input": {
            "format": "text",
            "content": "1600 Amphitheatre Parkway, Mountain View, CA"
        }
    }
    
    client.post(
        "/tasks", 
        json=task_data,
        headers={"X-API-Key": TEST_API_KEY}
    )
    
    # Now retrieve it
    response = client.get(
        f"/tasks/{task_id}",
        headers={"X-API-Key": TEST_API_KEY}
    )
    
    assert response.status_code == 200
    task = response.json()
    assert task["id"] == task_id
    assert task["type"] == "geocode"

def test_execute_geocode_task(mock_google_maps_client):
    # Mock the Google Maps API response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "OK",
        "results": [
            {
                "formatted_address": "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA",
                "geometry": {
                    "location": {
                        "lat": 37.4224764,
                        "lng": -122.0842499
                    }
                },
                "place_id": "ChIJ2eUgeAK6j4ARbn5u_wAGqWA"
            }
        ]
    }
    mock_google_maps_client.get.return_value = mock_response
    
    # Create a task
    task_id = str(uuid.uuid4())
    task_data = {
        "id": task_id,
        "type": "geocode",
        "status": "created",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "input": {
            "format": "text",
            "content": "1600 Amphitheatre Parkway, Mountain View, CA"
        }
    }
    
    client.post(
        "/tasks", 
        json=task_data,
        headers={"X-API-Key": TEST_API_KEY}
    )
    
    # Execute the task
    response = client.put(
        f"/tasks/{task_id}/execute",
        headers={"X-API-Key": TEST_API_KEY}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "completed"
    assert result["output"]["format"] == "application/json"
    assert "results" in result["output"]["content"]

def test_execute_unsupported_task():
    # Create a task with unsupported type
    task_id = str(uuid.uuid4())
    task_data = {
        "id": task_id,
        "type": "unsupported_task",
        "status": "created",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "input": {
            "format": "text",
            "content": "test content"
        }
    }
    
    # Should fail with 400 Bad Request
    response = client.post(
        "/tasks", 
        json=task_data,
        headers={"X-API-Key": TEST_API_KEY}
    )
    
    assert response.status_code == 400
    assert "Unsupported task type" in response.json()["detail"]