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
- **Health Check**: Verify model and MQTT status
- **Bin Control**: Open/close bins via MQTT
- **Prediction**: Predict waste type from image and auto-open bins

### ⚠️ Error Codes
- 400: Invalid input (e.g., image type, bin index)
- 409: Bin is busy
- 422: Missing required fields
- 500: Internal server error (e.g., model or MQTT failure)
- 503: IoT device unavailable or unknown status
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
            if path == "/healthcheck" and method == "get":
                operation.update({
                    "tags": ["Health"],
                    "summary": "Check system health",
                    "description": "Returns the ML model load status, MQTT connection, and ESP32 device state.",
                    "responses": {
                        "200": {
                            "description": "System health status",
                            "content": {
                                "application/json": {
                                    "examples": {
                                        "all_systems_ok": {
                                            "summary": "All systems operational",
                                            "value": {
                                                "model_loaded": True,
                                                "mqtt_connected": True,
                                                "device_status": "online"
                                            }
                                        },
                                        "model_not_loaded": {
                                            "summary": "Model not loaded",
                                            "value": {
                                                "model_loaded": False,
                                                "mqtt_connected": True,
                                                "device_status": "online"
                                            }
                                        },
                                        "mqtt_disconnected": {
                                            "summary": "MQTT disconnected",
                                            "value": {
                                                "model_loaded": True,
                                                "mqtt_connected": False,
                                                "device_status": "online"
                                            }
                                        },
                                        "device_offline": {
                                            "summary": "Device offline",
                                            "value": {
                                                "model_loaded": True,
                                                "mqtt_connected": True,
                                                "device_status": "offline"
                                            }
                                        },
                                        "all_systems_down": {
                                            "summary": "All systems down",
                                            "value": {
                                                "model_loaded": False,
                                                "mqtt_connected": False,
                                                "device_status": "unknown"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                })
            elif path == "/bin_status" and method == "get":
                operation.update({
                    "tags": ["Bin Management"],
                    "summary": "Get bin status",
                    "description": "Returns current bin status: OK, busy, or unknown.",
                    "responses": {
                        "200": {
                            "description": "Bin status retrieved",
                            "content": {
                                "application/json": {
                                    "examples": {
                                        "available": {
                                            "summary": "Bin available",
                                            "value": {"bin_status": "OK"}
                                        },
                                        "busy": {
                                            "summary": "Bin busy",
                                            "value": {"bin_status": "busy"}
                                        },
                                        "unknown": {
                                            "summary": "Bin status unknown",
                                            "value": {"bin_status": "unknown"}
                                        }
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Internal server error",
                            "content": {
                                "application/json": {
                                    "example": {"detail": "Error: MQTT Error"}
                                }
                            }
                        }
                    }
                })
            elif path == "/control_bin" and method == "post":
                operation.update({
                    "tags": ["Bin Management"],
                    "summary": "Control specific bin",
                    "description": "Opens bin by index (0: organic, 1: recycle, 2: hazardous, 3: other).",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "bin_index": {
                                            "type": "integer",
                                            "minimum": 0,
                                            "maximum": 3
                                        }
                                    },
                                    "required": ["bin_index"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Bin opened successfully",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "message": "Opened bin recycle",
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
                                    "examples": {
                                        "device_offline": {
                                            "summary": "Device offline",
                                            "value": {"detail": "ESP32 device is offline. Cannot control bin."}
                                        },
                                        "unknown_status": {
                                            "summary": "Unknown bin status",
                                            "value": {"detail": "Bin status is unknown. Cannot control bin."}
                                        }
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Internal server error",
                            "content": {
                                "application/json": {
                                    "example": {"detail": "Error: Failed to publish"}
                                }
                            }
                        }
                    }
                })
            elif path == "/predict" and method == "post":
                operation.update({
                    "tags": ["Prediction"],
                    "summary": "Classify waste image",
                    "description": "Upload a .jpg or .png waste image to receive predicted class.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "file": {
                                            "type": "string",
                                            "format": "binary"
                                        }
                                    },
                                    "required": ["file"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Prediction success",
                            "content": {
                                "application/json": {
                                    "example": {"class": "recycle"}
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
                        "422": {
                            "description": "Missing file",
                            "content": {
                                "application/json": {
                                    "example": {"detail": [{"loc": ["body", "file"], "msg": "Field required", "type": "missing"}]}
                                }
                            }
                        },
                        "500": {
                            "description": "Internal server error",
                            "content": {
                                "application/json": {
                                    "example": {"detail": "Error: Model prediction error"}
                                }
                            }
                        }
                    }
                })
            elif path == "/predict_iot" and method == "post":
                operation.update({
                    "tags": ["Prediction"],
                    "summary": "Predict & auto-open bin",
                    "description": "Upload image → predict → open bin via MQTT (if device is ready).",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "file": {
                                            "type": "string",
                                            "format": "binary"
                                        }
                                    },
                                    "required": ["file"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Prediction and bin control successful",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "class": "recycle",
                                        "bin_index": 1,
                                        "bin_opened": "recycle",
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
                                    "examples": {
                                        "device_offline": {
                                            "summary": "Device offline",
                                            "value": {"detail": "ESP32 device is offline. Cannot control bin."}
                                        },
                                        "unknown_status": {
                                            "summary": "Unknown bin status",
                                            "value": {"detail": "Bin status is unknown. Cannot control bin."}
                                        }
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Internal server error",
                            "content": {
                                "application/json": {
                                    "examples": {
                                        "model_error": {
                                            "summary": "Model prediction error",
                                            "value": {"detail": "Error: Model prediction error"}
                                        },
                                        "mqtt_error": {
                                            "summary": "MQTT publish error",
                                            "value": {"detail": "Error: Failed to publish"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                })

    app.openapi_schema = openapi_schema
    return app.openapi_schema