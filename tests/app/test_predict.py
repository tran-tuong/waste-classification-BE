import pytest
import io
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
def mock_classifier():
    with patch("app.routers.predict.classifier") as mock_clf:
        yield mock_clf

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

def test_predict_success(client, mock_classifier, image_file):
    """Test successful image prediction"""
    # Setup mock classifier
    mock_classifier.predict.return_value = ("recycle", {
        "organic": 5.2,
        "recycle": 85.1,
        "hazardous": 4.3, 
        "other": 5.4
    })
    
    # Create file for upload
    filename, file_content, content_type = image_file
    files = {"file": (filename, io.BytesIO(file_content), content_type)}
    
    # Make request
    response = client.post("/predict", files=files)
    
    # Check response
    assert response.status_code == 200
    assert response.json() == {"class": "recycle"}
    
    # Verify mock called correctly
    mock_classifier.predict.assert_called_once()
    # Check that the image data was passed to predict
    args, _ = mock_classifier.predict.call_args
    assert isinstance(args[0], bytes)

def test_predict_non_image_file(client, mock_classifier, non_image_file):
    """Test prediction with non-image file"""
    # Create file for upload
    filename, file_content, content_type = non_image_file
    files = {"file": (filename, io.BytesIO(file_content), content_type)}
    
    # Make request
    response = client.post("/predict", files=files)
    
    # Check response
    assert response.status_code == 500
    assert "Uploaded file must be image" in response.json()["detail"]
    
    # Verify mock was not called
    mock_classifier.predict.assert_not_called()

def test_predict_model_error(client, mock_classifier, image_file):
    """Test prediction when model encounters an error"""
    # Setup mock classifier to raise an exception
    mock_classifier.predict.side_effect = Exception("Model prediction error")
    
    # Create file for upload
    filename, file_content, content_type = image_file
    files = {"file": (filename, io.BytesIO(file_content), content_type)}
    
    # Make request
    response = client.post("/predict", files=files)
    
    # Check response
    assert response.status_code == 500
    assert "Error: Model prediction error" in response.json()["detail"]

def test_predict_missing_file(client):
    """Test prediction without providing a file"""
    # Make request with no files
    response = client.post("/predict")
    
    # Check response - should be a validation error
    assert response.status_code == 422  # Unprocessable Entity
    assert "Field required" in response.json()["detail"][0]["msg"]