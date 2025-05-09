import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os
import time

load_dotenv()

class MQTTClient:
    def __init__(self):
        self.broker = os.getenv("MQTT_BROKER", "broker.emqx.io")
        self.port = int(os.getenv("MQTT_PORT", "1883"))
        self.username = os.getenv("MQTT_USERNAME", "emqx")
        self.password = os.getenv("MQTT_PASSWORD", "public")
        self.base_topic = os.getenv("MQTT_BASE_TOPIC", "waste")

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

        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"[ERROR] Failed to connect to MQTT broker: {e}")
            self.connected = False
            self.bin_status = "unknown"

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[INFO] Connected to MQTT broker")
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

    def disconnect(self):
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False