import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import io
from PIL import Image

# Import the WasteClassifier class (will use mocked dependencies from config)
from ml.model import WasteClassifier

@pytest.fixture
def waste_classifier():
    """Fixture to create a WasteClassifier instance with mocked model."""
    classifier = WasteClassifier(model_path='dummy_path')
    classifier.model = MagicMock()
    return classifier

@pytest.fixture
def sample_image_data():
    """Fixture to create sample image data for testing."""
    # Create a simple 224x224 RGB image
    img = Image.new('RGB', (224, 224), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

def test_preprocess_image(waste_classifier, sample_image_data):
    """Test the preprocess_image method."""
    with patch('ml.model.image.load_img') as mock_load_img, \
         patch('ml.model.image.img_to_array') as mock_img_to_array, \
         patch('ml.model.preprocess_input') as mock_preprocess_input:
        
        # Configure mocks
        mock_img = MagicMock()
        mock_load_img.return_value = mock_img
        mock_array = np.zeros((224, 224, 3))
        mock_img_to_array.return_value = mock_array
        mock_processed = np.zeros((1, 224, 224, 3))
        mock_preprocess_input.return_value = mock_processed

        # Call the method
        result = waste_classifier.preprocess_image(sample_image_data)

        # Assertions
        mock_load_img.assert_called_once()
        mock_img_to_array.assert_called_once_with(mock_img)
        mock_preprocess_input.assert_called_once()
        assert result.shape == (1, 224, 224, 3)
        np.testing.assert_array_equal(result, mock_processed)

def test_predict(waste_classifier, sample_image_data):
    """Test the predict method."""
    with patch.object(waste_classifier, 'preprocess_image') as mock_preprocess, \
         patch.object(waste_classifier.model, 'predict') as mock_predict:
        
        # Configure mocks
        mock_preprocess.return_value = np.zeros((1, 224, 224, 3))
        mock_predict.return_value = np.array([[0.1, 0.7, 0.1, 0.1]])
        
        # Call the method
        predicted_class, probabilities = waste_classifier.predict(sample_image_data)

        # Assertions
        mock_preprocess.assert_called_once_with(sample_image_data)
        mock_predict.assert_called_once()
        assert predicted_class == 'organic'  # Index 1 corresponds to 'organic'
        assert isinstance(probabilities, dict)
        assert probabilities == {
            'hazardous': 10.0,
            'organic': 70.0,
            'other': 10.0,
            'recycle': 10.0
        }

def test_predict_invalid_image_data(waste_classifier):
    """Test predict method with invalid image data."""
    with patch.object(waste_classifier, 'preprocess_image') as mock_preprocess:
        mock_preprocess.side_effect = Exception("Invalid image data")
        
        # Test that exception is raised
        with pytest.raises(Exception, match="Invalid image data"):
            waste_classifier.predict(b'invalid_data')