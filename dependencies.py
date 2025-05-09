from ml.model import WasteClassifier
from iot.mqtt_client import MQTTClient

# Initialize classifier and MQTT client
classifier = WasteClassifier()
mqtt_client = MQTTClient()

# Class to index mappings
CLASS_TO_INDEX = {'hazardous': 2, 'organic': 0, 'other': 3, 'recycle': 1}
INDEX_TO_CLASS = {v: k for k, v in CLASS_TO_INDEX.items()}