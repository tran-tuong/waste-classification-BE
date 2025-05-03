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
    return {"status": "OK", "model_loaded": classifier.model is not None}

@app.post("/control_bin")
async def control_bin(request: BinControlRequest):
    try:
        bin_index = request.bin_index
        if bin_index < 0 or bin_index > 3:
            raise HTTPException(status_code=400, detail="bin_index is 0 to 3")
        
        # Lấy tên loại rác từ bin_index
        bin_name = INDEX_TO_CLASS.get(bin_index, "unknown")
        
        # Gửi lệnh qua MQTT
        mqtt_client.publish(bin_index)
        return {"message": f"Opened bin {bin_name}"}
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
async def predict(file: UploadFile = File(...)):
    try:
        # Kiểm tra file có phải hình ảnh
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Uploaded file must be image (.png, .jpg)")
        
        # Đọc dữ liệu file
        image_data = await file.read()
        
        # Dự đoán
        predicted_class, probabilities = classifier.predict(image_data)
        
        # Gửi lệnh qua MQTT để mở thùng rác tương ứng
        bin_index = CLASS_TO_INDEX[predicted_class]
        mqtt_client.publish(bin_index)
        bin_name = INDEX_TO_CLASS.get(bin_index, "unknown")
        
        return {
            "class": predicted_class,
            "bin_index": bin_index,
            "bin_opened": bin_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")