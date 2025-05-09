from fastapi import APIRouter, HTTPException
from schemas import BinControlRequest
from dependencies import mqtt_client, INDEX_TO_CLASS

router = APIRouter()

@router.post("/control_bin")
async def control_bin(request: BinControlRequest):
    try:
        # Check if device is online
        if not mqtt_client.is_device_online():
            raise HTTPException(
                status_code=503,
                detail="ESP32 device is offline. Cannot control bin."
            )
        bin_index = request.bin_index
        if bin_index < 0 or bin_index > 3:
            raise HTTPException(status_code=400, detail="bin_index must be 0 to 3")
            
        # Check bin status before sending command
        bin_status = mqtt_client.get_bin_status()
        if bin_status == "busy":
            raise HTTPException(
                status_code=409,  
                detail="Bin is currently busy. Please wait until it's available."
            )
        elif bin_status == "unknown":
            raise HTTPException(
                status_code=503, 
                detail="Bin status is unknown. Please check the connection to the IoT device."
            )
        
        # Get bin name from index
        bin_name = INDEX_TO_CLASS.get(bin_index, "unknown")
            
        # Send command via MQTT
        mqtt_client.publish(bin_index)
        return {"message": f"Opened bin {bin_name}", "bin_status": bin_status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")