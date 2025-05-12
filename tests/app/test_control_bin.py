import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

@pytest.fixture
def app():
    from app.main import app
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture
def mock_dependencies():
    with patch("app.routers.control_bin.mqtt_client") as mock_mqtt_client, \
         patch("app.routers.control_bin.INDEX_TO_CLASS", {0: "organic", 1: "recycle", 2: "hazardous", 3: "other"}):
        yield mock_mqtt_client

def test_control_bin_success(client, mock_dependencies):
    """Test successfully controlling the bin"""
    # Setup mocks
    mock_dependencies.is_device_online.return_value = True
    mock_dependencies.get_bin_status.return_value = "OK"
    mock_dependencies.publish = MagicMock()
    
    # Send request
    response = client.post("/control_bin", json={"bin_index": 1})
    
    # Assert response
    assert response.status_code == 200
    assert response.json() == {"message": "Opened bin recycle", "bin_status": "OK"}
    
    # Verify mocks were called correctly
    mock_dependencies.is_device_online.assert_called_once()
    mock_dependencies.get_bin_status.assert_called_once()
    mock_dependencies.publish.assert_called_once_with(1)

def test_control_bin_invalid_index(client, mock_dependencies):
    """Test controlling bin with invalid bin index"""
    # Setup mocks
    mock_dependencies.is_device_online.return_value = True
    
    # Test with index below valid range
    response = client.post("/control_bin", json={"bin_index": -1})
    assert response.status_code == 400
    assert "bin_index must be 0 to 3" in response.json()["detail"]
    
    # Test with index above valid range
    response = client.post("/control_bin", json={"bin_index": 4})
    assert response.status_code == 400
    assert "bin_index must be 0 to 3" in response.json()["detail"]

def test_control_bin_device_offline(client, mock_dependencies):
    """Test controlling bin when device is offline"""
    # Setup mocks
    mock_dependencies.is_device_online.return_value = False
    
    # Send request
    response = client.post("/control_bin", json={"bin_index": 1})
    
    # Assert response
    assert response.status_code == 503
    assert "ESP32 device is offline" in response.json()["detail"]
    
    # Verify mock was called correctly
    mock_dependencies.is_device_online.assert_called_once()
    mock_dependencies.get_bin_status.assert_not_called()

def test_control_bin_busy(client, mock_dependencies):
    """Test controlling bin when bin is busy"""
    # Setup mocks
    mock_dependencies.is_device_online.return_value = True
    mock_dependencies.get_bin_status.return_value = "busy"
    
    # Send request
    response = client.post("/control_bin", json={"bin_index": 2})
    
    # Assert response
    assert response.status_code == 409
    assert "Bin is currently busy" in response.json()["detail"]
    
    # Verify mocks were called correctly
    mock_dependencies.is_device_online.assert_called_once()
    mock_dependencies.get_bin_status.assert_called_once()
    mock_dependencies.publish.assert_not_called()

def test_control_bin_unknown_status(client, mock_dependencies):
    """Test controlling bin when bin status is unknown"""
    # Setup mocks
    mock_dependencies.is_device_online.return_value = True
    mock_dependencies.get_bin_status.return_value = "unknown"
    
    # Send request
    response = client.post("/control_bin", json={"bin_index": 0})
    
    # Assert response
    assert response.status_code == 503
    assert "Bin status is unknown" in response.json()["detail"]
    
    # Verify mocks were called correctly
    mock_dependencies.is_device_online.assert_called_once()
    mock_dependencies.get_bin_status.assert_called_once()
    mock_dependencies.publish.assert_not_called()

def test_control_bin_mqtt_error(client, mock_dependencies):
    """Test controlling bin when MQTT publish fails"""
    # Setup mocks
    mock_dependencies.is_device_online.return_value = True
    mock_dependencies.get_bin_status.return_value = "OK"
    mock_dependencies.publish.side_effect = ConnectionError("Failed to publish")
    
    # Send request
    response = client.post("/control_bin", json={"bin_index": 3})
    
    # Assert response
    assert response.status_code == 500
    assert "Error: Failed to publish" in response.json()["detail"]
    
    # Verify mocks were called correctly
    mock_dependencies.is_device_online.assert_called_once()
    mock_dependencies.get_bin_status.assert_called_once()
    mock_dependencies.publish.assert_called_once_with(3)