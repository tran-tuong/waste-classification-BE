import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

@pytest.fixture
def app():
    from app.main import app
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture
def mock_mqtt_client():
    with patch("app.routers.bin_status.mqtt_client") as mock_client:
        yield mock_client

def test_get_bin_status_available(client, mock_mqtt_client):
    """Test getting bin status when bin is available"""
    mock_mqtt_client.get_bin_status.return_value = "OK"
    
    response = client.get("/bin_status")
    
    assert response.status_code == 200
    assert response.json() == {"bin_status": "OK"}
    mock_mqtt_client.get_bin_status.assert_called_once()

def test_get_bin_status_busy(client, mock_mqtt_client):
    """Test getting bin status when bin is busy"""
    mock_mqtt_client.get_bin_status.return_value = "busy"
    
    response = client.get("/bin_status")
    
    assert response.status_code == 200
    assert response.json() == {"bin_status": "busy"}
    mock_mqtt_client.get_bin_status.assert_called_once()

def test_get_bin_status_unknown(client, mock_mqtt_client):
    """Test getting bin status when status is unknown"""
    mock_mqtt_client.get_bin_status.return_value = "unknown"
    
    response = client.get("/bin_status")
    
    assert response.status_code == 200
    assert response.json() == {"bin_status": "unknown"}
    mock_mqtt_client.get_bin_status.assert_called_once()

def test_get_bin_status_error(client, mock_mqtt_client):
    """Test getting bin status when an exception occurs"""
    mock_mqtt_client.get_bin_status.side_effect = Exception("MQTT Error")
    
    # Since the router doesn't have error handling for the get_bin_status function,
    # this would raise a 500 error in a real application
    # In a real test, you might want to add error handling in the router
    with pytest.raises(Exception, match="MQTT Error"):
        client.get("/bin_status")