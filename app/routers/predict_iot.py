from fastapi import APIRouter, File, UploadFile, HTTPException
from app.dependencies import classifier, mqtt_client, CLASS_TO_INDEX, INDEX_TO_CLASS

router = APIRouter()

@router.post("/predict_iot")
async def predict_iot(file: UploadFile = File(...)):
    try:
        # Check if file is an image
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Uploaded file must be image (.png, .jpg)")
            
        # Read file data
        image_data = await file.read()
            
        # Predict
        predicted_class, probabilities = classifier.predict(image_data)
            
        if not mqtt_client.is_device_online():
            raise HTTPException(
                status_code=503,
                detail="ESP32 device is offline. Cannot control bin."
            ) 
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
            
        # Send command via MQTT to open corresponding bin
        bin_index = CLASS_TO_INDEX[predicted_class]
        mqtt_client.publish(bin_index)
        bin_name = INDEX_TO_CLASS.get(bin_index, "unknown")
            
        return {
            "class": predicted_class,
            "bin_index": bin_index,
            "bin_opened": bin_name,
            "bin_status": "busy"  # Status will change to busy after command
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")