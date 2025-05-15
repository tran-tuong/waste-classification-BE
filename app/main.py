from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import healthcheck, bin_status, control_bin, predict, predict_iot
from config.swagger import custom_openapi
import uvicorn
import os

app = FastAPI(
    title="Waste Classification API",
    summary="API for waste classification using machine learning and IoT integration",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Update for production later
    # allow_origins=["https://waste-classification-blush.vercel.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(healthcheck.router)
app.include_router(bin_status.router)
app.include_router(control_bin.router)
app.include_router(predict.router)
app.include_router(predict_iot.router)

# Set custom OpenAPI schema
app.openapi = lambda: custom_openapi(app)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Use Render's PORT or default to 8000
    uvicorn.run(app, host="0.0.0.0", port=port)