from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from model import WasteClassifier
from mqtt_client import MQTTClient

app = FastAPI(
    title="Waste Classification",
    summary="API to connect with Classification Model and IoT system"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], #Vite localhost 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo classifier và MQTT client
classifier = WasteClassifier()
mqtt_client = MQTTClient()

# Ánh xạ lớp và index
CLASS_TO_INDEX = {'hazardous': 2, 'organic': 0, 'other': 3, 'recycle': 1}
INDEX_TO_CLASS = {v: k for k, v in CLASS_TO_INDEX.items()}

class BinControlRequest(BaseModel):
    bin_index: int

@app.get("/healthcheck")
async def healthcheck():
    return {
        "model_loaded": classifier.model is not None,
        "mqtt_connected": mqtt_client.connected,
        "device_status": mqtt_client.esp32_status
    }

@app.get("/bin_status")
async def get_bin_status():
    """Get current status of the waste bin system"""
    status = mqtt_client.get_bin_status()
    return {"bin_status": status}

@app.post("/control_bin")
async def control_bin(request: BinControlRequest):
    try:
        # Thêm kiểm tra trước khi bin control
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
        
        # Lấy tên loại rác từ bin_index
        bin_name = INDEX_TO_CLASS.get(bin_index, "unknown")
            
        # Gửi lệnh qua MQTT
        mqtt_client.publish(bin_index)
        return {"message": f"Opened bin {bin_name}", "bin_status": bin_status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        # Kiểm tra file có phải hình ảnh
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Uploaded file must be image (.png, .jpg)")
            
        # Đọc dữ liệu file
        image_data = await file.read()
            
        # Dự đoán
        predicted_class, probabilities = classifier.predict(image_data)
        return {
            "class": predicted_class
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/predict_iot")
async def predict_iot(file: UploadFile = File(...)):
    try:
        # Kiểm tra file có phải hình ảnh
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Uploaded file must be image (.png, .jpg)")
            
        # Đọc dữ liệu file
        image_data = await file.read()
            
        # Dự đoán
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
            
        # Gửi lệnh qua MQTT để mở thùng rác tương ứng
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