import pytest
from unittest.mock import patch, MagicMock, mock_open
import time
import os
import ssl
import tempfile
from iot.mqtt_client import MQTTClient

@pytest.fixture
def mock_env_vars():
    """Fixture to mock environment variables with default values."""
    with patch('os.getenv') as mock_getenv:
        mock_getenv.side_effect = lambda key, default=None: {
            'MQTT_BROKER': 'test.broker.com',
            'MQTT_PORT': '8883',
            'MQTT_USERNAME': 'test_user',
            'MQTT_PASSWORD': 'test_pass',
            'MQTT_BASE_TOPIC': 'test/waste',
            'MQTT_CA_CERT': None,
            'MQTT_CA_CERT_PATH': None,
            'MQTT_USE_SSL': 'true',
            'MQTT_VERIFY_CERTS': 'true'
        }.get(key, default)
        yield mock_getenv

@pytest.fixture
def mqtt_client(mock_env_vars):
    """Fixture to create an MQTTClient instance with mocked dependencies."""
    with patch('paho.mqtt.client.Client') as mock_mqtt_client, \
         patch('iot.mqtt_client.MQTTClient.configure_ssl') as mock_configure_ssl:
        client = MQTTClient()
        client.client = mock_mqtt_client.return_value
        return client

def test_mqtt_client_init_success(mock_env_vars):
    """Test successful MQTTClient initialization."""
    with patch('paho.mqtt.client.Client') as mock_mqtt_client, \
         patch('iot.mqtt_client.MQTTClient.configure_ssl') as mock_configure_ssl:
        client = MQTTClient()
        
        assert client.broker == 'test.broker.com'
        assert client.port == 8883
        assert client.username == 'test_user'
        assert client.password == 'test_pass'
        assert client.base_topic == 'test/waste'
        assert client.connected == False
        assert client.bin_status == 'unknown'
        assert client.esp32_status == 'unknown'
        assert client.use_ssl == True
        assert client.verify_certs == True
        
        mock_mqtt_client.return_value.username_pw_set.assert_called_with('test_user', 'test_pass')
        mock_configure_ssl.assert_called_once()
        mock_mqtt_client.return_value.connect.assert_called_with('test.broker.com', 8883, 60)
        mock_mqtt_client.return_value.loop_start.assert_called_once()

def test_mqtt_client_init_invalid_port(mock_env_vars):
    """Test initialization with invalid MQTT_PORT."""
    mock_env_vars.side_effect = lambda key, default=None: {
        'MQTT_BROKER': 'test.broker.com',
        'MQTT_PORT': 'invalid',
        'MQTT_USERNAME': 'test_user',
        'MQTT_PASSWORD': 'test_pass',
        'MQTT_BASE_TOPIC': 'test/waste',
        'MQTT_USE_SSL': 'true',
        'MQTT_VERIFY_CERTS': 'true'
    }.get(key, default)
    
    with patch('paho.mqtt.client.Client') as mock_mqtt_client, \
         patch('iot.mqtt_client.MQTTClient.configure_ssl') as mock_configure_ssl:
        with pytest.raises(ValueError):
            MQTTClient()

def test_mqtt_client_init_connection_failure(mock_env_vars):
    """Test initialization with connection failure."""
    with patch('paho.mqtt.client.Client') as mock_mqtt_client, \
         patch('iot.mqtt_client.MQTTClient.configure_ssl') as mock_configure_ssl:
        mock_mqtt_client.return_value.connect.side_effect = Exception("Connection refused")
        client = MQTTClient()
        assert client.connected == False
        assert client.bin_status == 'unknown'

def test_mqtt_client_ssl_disabled(mock_env_vars):
    """Test initialization with SSL disabled."""
    mock_env_vars.side_effect = lambda key, default=None: {
        'MQTT_BROKER': 'test.broker.com',
        'MQTT_PORT': '1883',
        'MQTT_USERNAME': 'test_user',
        'MQTT_PASSWORD': 'test_pass',
        'MQTT_BASE_TOPIC': 'test/waste',
        'MQTT_USE_SSL': 'false',
        'MQTT_VERIFY_CERTS': 'true'
    }.get(key, default)
    
    with patch('paho.mqtt.client.Client') as mock_mqtt_client, \
         patch('iot.mqtt_client.MQTTClient.configure_ssl') as mock_configure_ssl:
        client = MQTTClient()
        assert client.use_ssl == False
        assert client.port == 1883
        mock_configure_ssl.assert_not_called()

def test_configure_ssl_with_ca_cert_path():
    """Test SSL configuration with CA certificate path."""
    with patch('os.getenv') as mock_getenv:
        mock_getenv.side_effect = lambda key, default=None: {
            'MQTT_BROKER': 'test.broker.com',
            'MQTT_PORT': '8883',
            'MQTT_USERNAME': 'test_user',
            'MQTT_PASSWORD': 'test_pass',
            'MQTT_BASE_TOPIC': 'test/waste',
            'MQTT_CA_CERT_PATH': '/path/to/ca.pem',
            'MQTT_USE_SSL': 'true',
            'MQTT_VERIFY_CERTS': 'true'
        }.get(key, default)
        
        with patch('paho.mqtt.client.Client') as mock_mqtt_client, \
             patch('ssl.create_default_context') as mock_ssl_context, \
             patch('os.path.exists', return_value=True) as mock_exists:
            
            mock_context = MagicMock()
            mock_ssl_context.return_value = mock_context
            
            client = MQTTClient()
            
            mock_ssl_context.assert_called_with(ssl.Purpose.SERVER_AUTH)
            mock_context.load_verify_locations.assert_called_with('/path/to/ca.pem')
            mock_mqtt_client.return_value.tls_set_context.assert_called_with(mock_context)

def test_configure_ssl_without_cert_verification():
    """Test SSL configuration with certificate verification disabled."""
    with patch('os.getenv') as mock_getenv:
        mock_getenv.side_effect = lambda key, default=None: {
            'MQTT_BROKER': 'test.broker.com',
            'MQTT_PORT': '8883',
            'MQTT_USERNAME': 'test_user',
            'MQTT_PASSWORD': 'test_pass',
            'MQTT_BASE_TOPIC': 'test/waste',
            'MQTT_USE_SSL': 'true',
            'MQTT_VERIFY_CERTS': 'false'
        }.get(key, default)
        
        with patch('paho.mqtt.client.Client') as mock_mqtt_client, \
             patch('ssl.create_default_context') as mock_ssl_context:
            
            mock_context = MagicMock()
            mock_ssl_context.return_value = mock_context
            
            client = MQTTClient()
            
            assert mock_context.check_hostname == False
            assert mock_context.verify_mode == ssl.CERT_NONE
            mock_mqtt_client.return_value.tls_set_context.assert_called_with(mock_context)

def test_configure_ssl_failure():
    """Test SSL configuration failure."""
    with patch('os.getenv') as mock_getenv:
        mock_getenv.side_effect = lambda key, default=None: {
            'MQTT_BROKER': 'test.broker.com',
            'MQTT_PORT': '8883',
            'MQTT_USERNAME': 'test_user',
            'MQTT_PASSWORD': 'test_pass',
            'MQTT_BASE_TOPIC': 'test/waste',
            'MQTT_USE_SSL': 'true',
            'MQTT_VERIFY_CERTS': 'true'
        }.get(key, default)
        
        with patch('paho.mqtt.client.Client') as mock_mqtt_client, \
             patch('ssl.create_default_context', side_effect=Exception("SSL Error")):
            
            with pytest.raises(Exception, match="SSL Error"):
                MQTTClient()

def test_on_connect_success(mqtt_client):
    """Test on_connect callback with successful connection."""
    mqtt_client.on_connect(None, None, None, 0)
    assert mqtt_client.connected == True
    mqtt_client.client.subscribe.assert_any_call('test/waste/servo/status')
    mqtt_client.client.subscribe.assert_any_call('test/waste/status')

def test_on_connect_failure(mqtt_client):
    """Test on_connect callback with various failure codes."""
    for rc in [1, 2, 3, 4, 5]:  # Common MQTT error codes
        mqtt_client.connected = False
        mqtt_client.on_connect(None, None, None, rc)
        assert mqtt_client.connected == False
        # Reset mock call history for each iteration
        mqtt_client.client.subscribe.reset_mock()

def test_on_disconnect_expected(mqtt_client):
    """Test on_disconnect callback with expected disconnection."""
    mqtt_client.connected = True
    mqtt_client.bin_status = 'OK'
    mqtt_client.on_disconnect(None, None, 0)
    assert mqtt_client.connected == False
    assert mqtt_client.bin_status == 'unknown'

def test_on_disconnect_unexpected(mqtt_client):
    """Test on_disconnect callback with unexpected disconnection."""
    mqtt_client.connected = True
    mqtt_client.on_disconnect(None, None, 1)  # Non-zero rc indicates unexpected disconnect
    assert mqtt_client.connected == False
    assert mqtt_client.bin_status == 'unknown'

def test_on_message_servo_status(mqtt_client):
    """Test on_message callback for servo/status topic."""
    mock_message = MagicMock()
    mock_message.topic = 'test/waste/servo/status'
    mock_message.payload.decode.return_value = 'OK'
    
    with patch('time.time', return_value=1000):
        mqtt_client.on_message(None, None, mock_message)
    
    assert mqtt_client.bin_status == 'OK'
    assert mqtt_client.last_status_update == 1000

def test_on_message_status(mqtt_client):
    """Test on_message callback for status topic."""
    mock_message = MagicMock()
    mock_message.topic = 'test/waste/status'
    mock_message.payload.decode.return_value = 'ONLINE'
    
    mqtt_client.on_message(None, None, mock_message)
    assert mqtt_client.esp32_status == 'online'

def test_on_message_invalid_topic(mqtt_client):
    """Test on_message callback with unexpected topic."""
    mock_message = MagicMock()
    mock_message.topic = 'test/waste/invalid'
    mock_message.payload.decode.return_value = 'something'
    
    mqtt_client.bin_status = 'OK'
    mqtt_client.esp32_status = 'online'
    mqtt_client.on_message(None, None, mock_message)
    
    assert mqtt_client.bin_status == 'OK'  # Should not change
    assert mqtt_client.esp32_status == 'online'  # Should not change

def test_is_device_online(mqtt_client):
    """Test is_device_online method with various statuses."""
    mqtt_client.esp32_status = 'online'
    assert mqtt_client.is_device_online() == True
    mqtt_client.esp32_status = 'offline'
    assert mqtt_client.is_device_online() == False
    mqtt_client.esp32_status = 'unknown'
    assert mqtt_client.is_device_online() == False

def test_get_bin_status_not_connected(mqtt_client):
    """Test get_bin_status when not connected."""
    mqtt_client.connected = False
    assert mqtt_client.get_bin_status() == 'unknown'

def test_get_bin_status_busy(mqtt_client):
    """Test get_bin_status when recently updated (busy)."""
    mqtt_client.connected = True
    mqtt_client.last_status_update = time.time()
    assert mqtt_client.get_bin_status() == 'busy'

def test_get_bin_status_OK(mqtt_client):
    """Test get_bin_status when update is old and bin is available."""
    mqtt_client.connected = True
    mqtt_client.last_status_update = time.time() - 2
    mqtt_client.bin_status = 'OK'
    assert mqtt_client.get_bin_status() == 'OK'

def test_get_bin_status_edge_time(mqtt_client):
    """Test get_bin_status at the edge of the 1.5-second threshold."""
    mqtt_client.connected = True
    mqtt_client.bin_status = 'OK'
    
    # Just within 1.5 seconds
    mqtt_client.last_status_update = time.time() - 1.4
    assert mqtt_client.get_bin_status() == 'busy'
    
    # Just beyond 1.5 seconds
    mqtt_client.last_status_update = time.time() - 1.6
    assert mqtt_client.get_bin_status() == 'OK'

def test_publish_success(mqtt_client):
    """Test publish method with successful publication."""
    mqtt_client.connected = True
    mqtt_client.client.publish.return_value.rc = 0
    
    mqtt_client.publish(1)
    mqtt_client.client.publish.assert_called_with('test/waste/1', '1')

def test_publish_not_connected(mqtt_client):
    """Test publish method when not connected."""
    mqtt_client.connected = False
    
    with pytest.raises(ConnectionError, match="MQTT client not connected to broker"):
        mqtt_client.publish(1)
    mqtt_client.client.publish.assert_not_called()

def test_publish_invalid_bin_index(mqtt_client):
    """Test publish method with invalid bin index."""
    mqtt_client.connected = True
    mqtt_client.client.publish.return_value.rc = 0
    
    # Negative index
    mqtt_client.publish(-1)
    mqtt_client.client.publish.assert_called_with('test/waste/-1', '-1')
    
    # Non-integer index
    mqtt_client.publish(1.5)
    mqtt_client.client.publish.assert_called_with('test/waste/1.5', '1.5')

def test_publish_failure(mqtt_client):
    """Test publish method with publication failure."""
    mqtt_client.connected = True
    mqtt_client.client.publish.return_value.rc = 1
    
    with pytest.raises(ConnectionError, match="Failed to publish to test/waste/1"):
        mqtt_client.publish(1)

def test_get_connection_info(mqtt_client):
    """Test get_connection_info method."""
    mqtt_client.connected = True
    mqtt_client.esp32_status = 'online'
    mqtt_client.bin_status = 'OK'
    
    info = mqtt_client.get_connection_info()
    
    expected_info = {
        "connected": True,
        "broker": 'test.broker.com',
        "port": 8883,
        "ssl_enabled": True,
        "cert_verification": True,
        "ca_cert_configured": False,  # No CA cert in default fixture
        "esp32_status": 'online',
        "bin_status": 'OK'
    }
    
    assert info == expected_info

def test_disconnect_connected(mqtt_client):
    """Test disconnect method when connected."""
    mqtt_client.connected = True
    mqtt_client.disconnect()
    mqtt_client.client.loop_stop.assert_called_once()
    mqtt_client.client.disconnect.assert_called_once()
    assert mqtt_client.connected == False

def test_disconnect_not_connected(mqtt_client):
    """Test disconnect method when not connected."""
    mqtt_client.connected = False
    mqtt_client.disconnect()
    mqtt_client.client.loop_stop.assert_not_called()
    mqtt_client.client.disconnect.assert_not_called()
    assert mqtt_client.connected == False

def test_multiple_connect_disconnect_cycles(mqtt_client):
    """Test multiple connect-disconnect cycles."""
    # Connect
    mqtt_client.on_connect(None, None, None, 0)
    assert mqtt_client.connected == True
    
    # Disconnect
    mqtt_client.disconnect()
    assert mqtt_client.connected == False
    
    # Reconnect
    mqtt_client.on_connect(None, None, None, 0)
    assert mqtt_client.connected == True
    mqtt_client.client.subscribe.assert_called()
    
    # Disconnect again
    mqtt_client.disconnect()
    assert mqtt_client.connected == False