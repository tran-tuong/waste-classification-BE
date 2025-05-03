import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os

load_dotenv()

class MQTTClient:
    def __init__(self):
        self.broker = os.getenv("MQTT_BROKER")
        self.port = int(os.getenv("MQTT_PORT"))
        self.username = os.getenv("MQTT_USERNAME")
        self.password = os.getenv("MQTT_PASSWORD")
        self.base_topic = os.getenv("MQTT_BASE_TOPIC")
        
        self.client = mqtt.Client()
        self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.on_connect
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
        else:
            print(f"Failed to connect, return code {rc}")

    def publish(self, bin_index):
        topic = f"{self.base_topic}/{bin_index}"
        self.client.publish(topic, str(bin_index))
        print(f"Published to {topic}: {bin_index}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()