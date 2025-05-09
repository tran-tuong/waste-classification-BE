from fastapi import APIRouter
from app.dependencies import classifier, mqtt_client

router = APIRouter()

@router.get("/healthcheck")
async def healthcheck():
    return {
        "model_loaded": classifier.model is not None,
        "mqtt_connected": mqtt_client.connected,
        "device_status": mqtt_client.esp32_status
    }