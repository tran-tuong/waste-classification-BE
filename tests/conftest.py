import pytest
from unittest.mock import patch, MagicMock

# Mock modules before they're imported
pytest_plugins = []

# Mock tensorflow and keras modules
mock_tensorflow = MagicMock()
mock_keras = MagicMock()
mock_load_model = MagicMock()

# Patch modules to prevent actual imports
import sys
sys.modules['tensorflow'] = mock_tensorflow
sys.modules['tensorflow.keras'] = mock_keras
sys.modules['tensorflow.keras.models'] = MagicMock()
sys.modules['tensorflow.keras.preprocessing'] = MagicMock()
sys.modules['tensorflow.keras.applications.resnet50'] = MagicMock()
sys.modules['tensorflow.keras.models'].load_model = mock_load_model

@pytest.fixture(autouse=True)
def mock_dependencies_for_app():
    """
    This fixture ensures that the app always starts with mocked dependencies.
    It prevents the app from trying to load a real model or connect to a real MQTT broker during tests.
    """
    # Patch the WasteClassifier to avoid loading model
    with patch("ml.model.load_model") as mock_load_model, \
         patch("app.dependencies.WasteClassifier") as mock_classifier_class, \
         patch("app.dependencies.MQTTClient") as mock_mqtt_client_class, \
         patch("paho.mqtt.client.Client") as mock_paho_client:
        
        # Configure mock load_model to return a mock model
        mock_load_model.return_value = MagicMock()
        
        # Configure mock classifier
        mock_classifier = mock_classifier_class.return_value
        mock_classifier.model = MagicMock()
        mock_classifier.predict.return_value = ("recycle", {"organic": 0.1, "recycle": 0.7, "hazardous": 0.1, "other": 0.1})
        
        # Configure mock MQTT client
        mock_mqtt = mock_mqtt_client_class.return_value
        mock_mqtt.connected = True
        mock_mqtt.esp32_status = "online"
        mock_mqtt.get_bin_status.return_value = "available"
        mock_mqtt.is_device_online.return_value = True
        
        yield