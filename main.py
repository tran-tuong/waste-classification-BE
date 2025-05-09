from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import healthcheck, bin_status, control_bin, predict, predict_iot

app = FastAPI(
    title="Waste Classification",
    summary="API to connect with Classification Model and IoT system",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite localhost
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