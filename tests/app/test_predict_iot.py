import pytest
import io
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_dependencies():
    with patch("app.routers.predict_iot.classifier") as mock_classifier, \
         patch("app.routers.predict_iot.mqtt_client") as mock_mqtt_client, \
         patch("app.routers.predict_iot.CLASS_TO_INDEX", {"organic": 0, "recycle": 1, "hazardous": 2, "other": 3}), \
         patch("app.routers.predict_iot.INDEX_TO_CLASS", {0: "organic", 1: "recycle", 2: "hazardous", 3: "other"}):
        
        yield {
            "classifier": mock_classifier,
            "mqtt_client": mock_mqtt_client
        }

@pytest.fixture
def image_file():
    # Create a mock image file
    file_content = b"fake image content"
    return ("test_image.jpg", file_content, "image/jpeg")

@pytest.fixture
def non_image_file():
    # Create a mock non-image file
    file_content = b"fake text content"
    return ("test_file.txt", file_content, "text/plain")

def test_predict_iot_success(mock_dependencies, image_file):
    """Test successful image prediction with IoT bin control"""
    # Setup mocks
    mock_dependencies["classifier"].predict.return_value = ("recycle", {
        "organic": 5.2,
        "recycle": 85.1,
        "hazardous": 4.3,
        "other": 5.4
    })
    mock_dependencies["mqtt_client"].is_device_online.return_value = True
    mock_dependencies["mqtt_client"].get_bin_status.return_value = "available"
    mock_dependencies["mqtt_client"].publish = MagicMock()
    
    # Create file for upload
    filename, file_content, content_type = image_file
    files = {"file": (filename, io.BytesIO(file_content), content_type)}
    
    # Make request
    response = client.post("/predict_iot", files=files)
    
    # Check response
    assert response.status_code == 200
    assert response.json() == {
        "class": "recycle",
        "bin_index": 1,
        "bin_opened": "recycle",
        "bin_status": "busy"
    }
    
    # Verify mocks were called correctly
    mock_dependencies["classifier"].predict.assert_called_once()
    mock_dependencies["mqtt_client"].is_device_online.assert_called_once()
    mock_dependencies["mqtt_client"].get_bin_status.assert_called_once()
    mock_dependencies["mqtt_client"].publish.assert_called_once_with(1)

def test_predict_iot_non_image_file(mock_dependencies, non_image_file):
    """Test prediction with non-image file"""
    # Create file for upload
    filename, file_content, content_type = non_image_file
    files = {"file": (filename, io.BytesIO(file_content), content_type)}
    
    # Make request
    response = client.post("/predict_iot", files=files)
    
    # Check response
    assert response.status_code == 400
    assert "Uploaded file must be image" in response.json()["detail"]
    
    # Verify mocks were not called
    mock_dependencies["classifier"].predict.assert_not_called()
    mock_dependencies["mqtt_client"].is_device_online.assert_not_called()

def test_predict_iot_device_offline(mock_dependencies, image_file):
    """Test prediction when IoT device is offline"""
    # Setup mocks
    mock_dependencies["classifier"].predict.return_value = ("organic", {
        "organic": 78.5,
        "recycle": 10.2,
        "hazardous": 5.3,
        "other": 6.0
    })
    mock_dependencies["mqtt_client"].is_device_online.return_value = False
    
    # Create file for upload
    filename, file_content, content_type = image_file
    files = {"file": (filename, io.BytesIO(file_content), content_type)}
    
    # Make request
    response = client.post("/predict_iot", files=files)
    
    # Check response
    assert response.status_code == 503
    assert "ESP32 device is offline" in response.json()["detail"]
    
    # Verify mocks were called correctly
    mock_dependencies["classifier"].predict.assert_called_once()
    mock_dependencies["mqtt_client"].is_device_online.assert_called_once()
    mock_dependencies["mqtt_client"].get_bin_status.assert_not_called()

def test_predict_iot_bin_busy(mock_dependencies, image_file):
    """Test prediction when bin is busy"""
    # Setup mocks
    mock_dependencies["classifier"].predict.return_value = ("hazardous", {
        "organic": 5.1,
        "recycle": 12.3,
        "hazardous": 75.6,
        "other": 7.0
    })
    mock_dependencies["mqtt_client"].is_device_online.return_value = True
    mock_dependencies["mqtt_client"].get_bin_status.return_value = "busy"
    
    # Create file for upload
    filename, file_content, content_type = image_file
    files = {"file": (filename, io.BytesIO(file_content), content_type)}
    
    # Make request
    response = client.post("/predict_iot", files=files)
    
    # Check response
    assert response.status_code == 409
    assert "Bin is currently busy" in response.json()["detail"]
    
    # Verify mocks were called correctly
    mock_dependencies["classifier"].predict.assert_called_once()
    mock_dependencies["mqtt_client"].is_device_online.assert_called_once()
    mock_dependencies["mqtt_client"].get_bin_status.assert_called_once()
    mock_dependencies["mqtt_client"].publish.assert_not_called()

def test_predict_iot_bin_unknown_status(mock_dependencies, image_file):
    """Test prediction when bin status is unknown"""
    # Setup mocks
    mock_dependencies["classifier"].predict.return_value = ("other", {
        "organic": 10.1,
        "recycle": 20.3,
        "hazardous": 5.6,
        "other": 64.0
    })
    mock_dependencies["mqtt_client"].is_device_online.return_value = True
    mock_dependencies["mqtt_client"].get_bin_status.return_value = "unknown"
    
    # Create file for upload
    filename, file_content, content_type = image_file
    files = {"file": (filename, io.BytesIO(file_content), content_type)}
    
    # Make request
    response = client.post("/predict_iot", files=files)
    
    # Check response
    assert response.status_code == 503
    assert "Bin status is unknown" in response.json()["detail"]
    
    # Verify mocks were called correctly
    mock_dependencies["classifier"].predict.assert_called_once()
    mock_dependencies["mqtt_client"].is_device_online.assert_called_once()
    mock_dependencies["mqtt_client"].get_bin_status.assert_called_once()
    mock_dependencies["mqtt_client"].publish.assert_not_called()

def test_predict_iot_model_error(mock_dependencies, image_file):
    """Test prediction when model encounters an error"""
    # Setup mock classifier to raise an exception
    mock_dependencies["classifier"].predict.side_effect = Exception("Model prediction error")
    
    # Create file for upload
    filename, file_content, content_type = image_file
    files = {"file": (filename, io.BytesIO(file_content), content_type)}
    
    # Make request
    response = client.post("/predict_iot", files=files)
    
    # Check response
    assert response.status_code == 500
    assert "Error: Model prediction error" in response.json()["detail"]

def test_predict_iot_mqtt_error(mock_dependencies, image_file):
    """Test prediction when MQTT publish fails"""
    # Setup mocks
    mock_dependencies["classifier"].predict.return_value = ("recycle", {
        "organic": 5.2,
        "recycle": 85.1,
        "hazardous": 4.3,
        "other": 5.4
    })
    mock_dependencies["mqtt_client"].is_device_online.return_value = True
    mock_dependencies["mqtt_client"].get_bin_status.return_value = "available"
    mock_dependencies["mqtt_client"].publish.side_effect = ConnectionError("Failed to publish")
    
    # Create file for upload
    filename, file_content, content_type = image_file
    files = {"file": (filename, io.BytesIO(file_content), content_type)}
    
    # Make request
    response = client.post("/predict_iot", files=files)
    
    # Check response
    assert response.status_code == 500
    assert "Error: Failed to publish" in response.json()["detail"]
    
    # Verify mocks were called correctly
    mock_dependencies["classifier"].predict.assert_called_once()
    mock_dependencies["mqtt_client"].is_device_online.assert_called_once()
    mock_dependencies["mqtt_client"].get_bin_status.assert_called_once()
    mock_dependencies["mqtt_client"].publish.assert_called_once_with(1)