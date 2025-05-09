from fastapi import APIRouter
from app.dependencies import mqtt_client

router = APIRouter()

@router.get("/bin_status")
async def get_bin_status():
    """Get current status of the waste bin system"""
    status = mqtt_client.get_bin_status()
    return {"bin_status": status}