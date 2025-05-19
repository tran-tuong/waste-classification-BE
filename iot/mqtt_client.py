
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os
import time
import ssl

load_dotenv()

class MQTTClient:
    def __init__(self):
        self.broker = os.getenv("MQTT_BROKER")
        self.port = int(os.getenv("MQTT_PORT", 8883)) 
        self.username = os.getenv("MQTT_USERNAME")
        self.password = os.getenv("MQTT_PASSWORD")
        self.base_topic = os.getenv("MQTT_BASE_TOPIC")
        
        # SSL/TLS Configuration
        self.ca_cert_content = os.getenv("MQTT_CA_CERT")  # CA cert content từ .env
        self.ca_cert_path = os.getenv("MQTT_CA_CERT_PATH")  # Hoặc đường dẫn file
        
        # SSL/TLS Options
        self.use_ssl = os.getenv("MQTT_USE_SSL", "true").lower() == "true"
        self.verify_certs = os.getenv("MQTT_VERIFY_CERTS", "true").lower() == "true"
        
        # MQTT state
        self.bin_status = "unknown"
        self.esp32_status = "unknown"
        self.last_status_update = 0
        self.connected = False
        
        # Create MQTT client
        self.client = mqtt.Client()
        self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        
        # Configure SSL/TLS if enabled
        if self.use_ssl:
            self.configure_ssl()
        
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"[ERROR] Failed to connect to MQTT broker: {e}")
            self.connected = False
            self.bin_status = "unknown"

    def configure_ssl(self):
        """Configure SSL/TLS for MQTT connection"""
        print("[INFO] Configuring SSL/TLS for MQTT connection...")
        
        try:
            # Create SSL context
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            
            # Load CA certificate - từ content trong .env hoặc từ file
            if self.ca_cert_content:
                # Tạo file tạm thời từ content trong .env
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as temp_file:
                    temp_file.write(self.ca_cert_content)
                    temp_ca_path = temp_file.name
                
                context.load_verify_locations(temp_ca_path)
                print("[INFO] Loaded CA certificate from environment variable")
                
                # Xóa file tạm thời
                os.unlink(temp_ca_path)
                
            elif self.ca_cert_path and os.path.exists(self.ca_cert_path):
                context.load_verify_locations(self.ca_cert_path)
                print(f"[INFO] Loaded CA certificate from {self.ca_cert_path}")
            else:
                print("[WARN] No CA certificate provided")
            
            # Configure certificate verification
            if not self.verify_certs:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                print("[WARN] Certificate verification disabled (not recommended for production)")
            
            # Apply SSL context to MQTT client
            self.client.tls_set_context(context)
            print("[INFO] SSL/TLS configuration completed")
            
        except Exception as e:
            print(f"[ERROR] SSL/TLS configuration failed: {e}")
            raise

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            ssl_info = "with SSL/TLS" if self.use_ssl else "without SSL/TLS"
            print(f"[INFO] Connected to MQTT broker {ssl_info}")
            self.connected = True
            # Subscribing to bin status topics
            self.client.subscribe(f"{self.base_topic}/servo/status")
            self.client.subscribe(f"{self.base_topic}/status")
        else:
            print(f"[ERROR] Failed to connect to MQTT broker, return code={rc}")
            self.connected = False

    def on_disconnect(self, client, userdata, rc):
        print("[WARN] Disconnected from MQTT broker")
        self.connected = False
        self.bin_status = "unknown"

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()
        print(f"[MQTT] Message received | Topic: {topic} | Payload: {payload}")
        
        if topic == f"{self.base_topic}/servo/status":
            self.bin_status = payload
            self.last_status_update = time.time()
        elif topic == f"{self.base_topic}/status":
            self.esp32_status = payload.lower()

    def is_device_online(self) -> bool:
        return self.esp32_status == "online"

    def get_bin_status(self):
        if not self.connected:
            return "unknown"
        if time.time() - self.last_status_update <= 1.5:
            return "busy"
        return self.bin_status

    def publish(self, bin_index: int):
        if not self.connected:
            raise ConnectionError("MQTT client not connected to broker")
        topic = f"{self.base_topic}/{bin_index}"
        result = self.client.publish(topic, str(bin_index))
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise ConnectionError(f"Failed to publish to {topic}")
        print(f"[MQTT] Published to {topic}: {bin_index}")

    def get_connection_info(self):
        """Get connection status and SSL information"""
        return {
            "connected": self.connected,
            "broker": self.broker,
            "port": self.port,
            "ssl_enabled": self.use_ssl,
            "cert_verification": self.verify_certs,
            "ca_cert_configured": bool(self.ca_cert_content or (self.ca_cert_path and os.path.exists(self.ca_cert_path))),
            "esp32_status": self.esp32_status,
            "bin_status": self.bin_status
        }

    def disconnect(self):
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False