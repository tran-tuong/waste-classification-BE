from fastapi import APIRouter, File, UploadFile, HTTPException
from app.dependencies import classifier

router = APIRouter()

@router.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        # Check if file is an image
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Uploaded file must be image (.png, .jpg)")
            
        # Read file data
        image_data = await file.read()
            
        # Predict
        predicted_class, probabilities = classifier.predict(image_data)
        return {
            "class": predicted_class
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")