import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Import app after pytest fixture has run
@pytest.fixture
def app():
    from app.main import app
    return app

@pytest.fixture
def client(app):
    return TestClient(app)



@pytest.fixture
def mock_dependencies():
    with patch("app.routers.healthcheck.classifier") as mock_classifier, \
         patch("app.routers.healthcheck.mqtt_client") as mock_mqtt_client:
        # Set up mocks
        mock_classifier.model = MagicMock()
        mock_mqtt_client.connected = True
        mock_mqtt_client.esp32_status = "online"
        
        yield {
            "classifier": mock_classifier,
            "mqtt_client": mock_mqtt_client
        }

def test_healthcheck_all_systems_ok(client, mock_dependencies):
    """Test healthcheck when all systems are functioning properly"""
    response = client.get("/healthcheck")
    
    assert response.status_code == 200
    assert response.json() == {
        "model_loaded": True,
        "mqtt_connected": True,
        "device_status": "online"
    }

def test_healthcheck_model_not_loaded(client, mock_dependencies):
    """Test healthcheck when model is not loaded"""
    mock_dependencies["classifier"].model = None
    
    response = client.get("/healthcheck")
    
    assert response.status_code == 200
    assert response.json() == {
        "model_loaded": False,
        "mqtt_connected": True,
        "device_status": "online"
    }

def test_healthcheck_mqtt_disconnected(client, mock_dependencies):
    """Test healthcheck when MQTT client is disconnected"""
    mock_dependencies["mqtt_client"].connected = False
    
    response = client.get("/healthcheck")
    
    assert response.status_code == 200
    assert response.json() == {
        "model_loaded": True,
        "mqtt_connected": False,
        "device_status": "online"
    }

def test_healthcheck_device_offline(client, mock_dependencies):
    """Test healthcheck when ESP32 device is offline"""
    mock_dependencies["mqtt_client"].esp32_status = "offline"
    
    response = client.get("/healthcheck")
    
    assert response.status_code == 200
    assert response.json() == {
        "model_loaded": True,
        "mqtt_connected": True,
        "device_status": "offline"
    }

def test_healthcheck_all_systems_down(client, mock_dependencies):
    """Test healthcheck when all systems are down"""
    mock_dependencies["classifier"].model = None
    mock_dependencies["mqtt_client"].connected = False
    mock_dependencies["mqtt_client"].esp32_status = "unknown"
    
    response = client.get("/healthcheck")
    
    assert response.status_code == 200
    assert response.json() == {
        "model_loaded": False,
        "mqtt_connected": False,
        "device_status": "unknown"
    }