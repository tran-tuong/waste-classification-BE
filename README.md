# ♻️ Waste Classification API

A smart backend API integrating Machine Learning for waste image classification and IoT (ESP32 + MQTT) for controlling smart trash bins. This project automates waste sorting by predicting waste types from images and managing bin operations in real-time.

## 🚀 Features

- **Health Check**: Monitor the status of the ML model, MQTT connection, and ESP32 device.
- **Bin Management**: Control and monitor smart bins (open/close) via MQTT with statuses: OK, busy, or unknown.
- **Waste Prediction**: Classify waste images into categories (organic, recycle, hazardous, other) using a trained ML model.
- **IoT Integration**: Automatically open the appropriate bin based on image prediction when the device is online.
- **Robust Error Handling**: Comprehensive error codes (400, 409, 422, 500, 503) for invalid inputs, busy bins, or system failures.

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python) for high-performance API development.
- **Machine Learning**: Custom classifier for waste image prediction.
- **IoT**: MQTT protocol for communication with ESP32-based smart bins.
- **Testing**: Pytest with mocked dependencies for comprehensive test coverage.
- **Documentation**: OpenAPI (Swagger) for interactive API documentation.

## 📋 Prerequisites

- Python 3.8+
- **pip** for package management
- **MQTT broker** broker for IoT communication
- **ESP32** device with MQTT client configured
- **Trained ML** model for waste classification (not included in this repo)

## 🚀 Access the API

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 📚 API Endpoints

### Health Check

- **GET /healthcheck**
  - **Description**: Check the status of the ML model, MQTT connection, and ESP32 device.

### Bin Management

- **GET /bin_status**
  - **Description**: Retrieve the current bin status (OK, busy, unknown).
 
- **POST /control_bin**
  - **Description**: Open a specific bin by index (0: organic, 1: recycle, 2: hazardous, 3: other).

### Prediction
- **POST /predict**
  - **Description**: Classify a waste image (.jpg or .png).
  - **Request Body**: Multipart form-data with file (image).


- **POST /predict_iot**
  - **Description**: Classify an image and automatically open the corresponding bin via MQTT.
  - **Request Body**: Multipart form-data with file (image).
 

## 🧪 Testing

The project includes comprehensive unit tests using Pytest to cover all API endpoints and edge cases.

### Test Coverage:
- **Health check**: Model loaded/not loaded, MQTT connected/disconnected, device online/offline/unknown.
- **Bin status**: OK, busy, unknown, and error scenarios.
- **Bin control**: Valid/invalid indices, device offline, bin busy/unknown, MQTT errors.
- **Prediction**: Valid/invalid images, missing files, model errors.
- **Predict IoT**: Successful prediction and bin control, invalid files, device offline, bin busy/unknown, model/MQTT errors.

## 📜 Error Codes

- **400**: Invalid input (e.g., wrong file type, invalid bin index).
- **409**: Bin is currently busy.
- **422**: Missing required fields (e.g., no file uploaded).
- **500**: Internal server error (e.g., model failure, MQTT connection issues).
- **503**: IoT device offline or bin status unknown.

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 📬 Contact

For questions or feedback, please open an issue on GitHub or contact [tranvantuong2k3@gmail.com](mailto:tranvantuong2k3@gmail.com).

## 🌱 Built with 💚 for a cleaner planet!
