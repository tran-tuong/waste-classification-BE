from fastapi.openapi.utils import get_openapi

def custom_openapi(app):
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="♻️ Waste Classification API",
        version="1.0.0",
        summary="A smart API integrating Machine Learning for waste image classification and IoT (ESP32 + MQTT) to control trash bins.",
        description="""
### 🚀 Features
- ✅ **Health Check**: Verify model and MQTT status
- 🗑️ **Bin Control**: Open/close bins via MQTT
- 🧠 **Prediction**: Predict waste type from image and auto-open bins

### ⚠️ Error Codes
- `400`: Invalid input (e.g., image type, bin index)
- `409`: Bin is busy
- `503`: IoT device unavailable
- `500`: Internal server error
""",
        routes=app.routes,
    )

    openapi_schema["tags"] = [
        {"name": "Health", "description": "System and connectivity checks"},
        {"name": "Bin Management", "description": "Control and monitor bin status"},
        {"name": "Prediction", "description": "Classify waste images using ML model"},
    ]

    for path, methods in openapi_schema["paths"].items():
        for method, operation in methods.items():
            if path == "/healthcheck":
                operation.update({
                    "tags": ["Health"],
                    "summary": "Check system health",
                    "description": "Returns the ML model load status, MQTT connection, and device state.",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "model_loaded": True,
                                        "mqtt_connected": True,
                                        "device_status": "online"
                                    }
                                }
                            }
                        }
                    }
                })
            elif path == "/bin_status":
                operation.update({
                    "tags": ["Bin Management"],
                    "summary": "Get bin status",
                    "description": "Returns current status of bin: OK, busy, or unknown.",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "bin_status": "OK"
                                    }
                                }
                            }
                        }
                    }
                })
            elif path == "/control_bin":
                operation.update({
                    "tags": ["Bin Management"],
                    "summary": "Control specific bin",
                    "description": "Opens bin by index (0: organic, 1: recycle, 2: hazardous, 3: other).",
                    "responses": {
                        "200": {
                            "description": "Bin opened successfully",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "message": "Opened bin organic",
                                        "bin_status": "OK"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid bin index",
                            "content": {
                                "application/json": {
                                    "example": {"detail": "bin_index must be 0 to 3"}
                                }
                            }
                        },
                        "409": {
                            "description": "Bin busy",
                            "content": {
                                "application/json": {
                                    "example": {"detail": "Bin is currently busy. Please wait."}
                                }
                            }
                        },
                        "503": {
                            "description": "Device offline or unknown status",
                            "content": {
                                "application/json": {
                                    "example": {"detail": "ESP32 device is offline. Cannot control bin."}
                                }
                            }
                        }
                    }
                })
            elif path == "/predict":
                operation.update({
                    "tags": ["Prediction"],
                    "summary": "Classify waste image",
                    "description": "Upload a .jpg or .png waste image to receive predicted class.",
                    "responses": {
                        "200": {
                            "description": "Prediction success",
                            "content": {
                                "application/json": {
                                    "example": {"class": "organic"}
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid file type",
                            "content": {
                                "application/json": {
                                    "example": {"detail": "Uploaded file must be image (.png, .jpg)"}
                                }
                            }
                        },
                        "500": {
                            "description": "Internal server error",
                            "content": {
                                "application/json": {
                                    "example": {"detail": "Error: <error message>"}
                                }
                            }
                        }
                    }
                })
            elif path == "/predict_iot":
                operation.update({
                    "tags": ["Prediction"],
                    "summary": "Predict & auto-open bin",
                    "description": "Upload image → predict → open bin via MQTT (if device is ready).",
                    "responses": {
                        "200": {
                            "description": "Prediction and bin control successful",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "class": "organic",
                                        "bin_index": 0,
                                        "bin_opened": "organic",
                                        "bin_status": "busy"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid file type",
                            "content": {
                                "application/json": {
                                    "example": {"detail": "Uploaded file must be image (.png, .jpg)"}
                                }
                            }
                        },
                        "409": {
                            "description": "Bin busy",
                            "content": {
                                "application/json": {
                                    "example": {"detail": "Bin is currently busy. Please wait."}
                                }
                            }
                        },
                        "503": {
                            "description": "Device offline or unknown status",
                            "content": {
                                "application/json": {
                                    "example": {"detail": "ESP32 device is offline. Cannot control bin."}
                                }
                            }
                        },
                        "500": {
                            "description": "Internal server error",
                            "content": {
                                "application/json": {
                                    "example": {"detail": "Error: <error message>"}
                                }
                            }
                        }
                    }
                })

    app.openapi_schema = openapi_schema
    return app.openapi_schema
