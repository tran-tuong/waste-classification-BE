import numpy as np
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.models import load_model
import io

class WasteClassifier:
    def __init__(self, model_path='ml/model/model.keras'):
        self.model = load_model(model_path)
        self.class_names = ['hazardous', 'organic', 'other', 'recycle']

    #Preprocessing step
    def preprocess_image(self, image_data):
        img = image.load_img(io.BytesIO(image_data), target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        return img_array

    def predict(self, image_data):
        img_array = self.preprocess_image(image_data)
        prediction = self.model.predict(img_array)[0]  # Lấy vector xác suất
        predicted_class = self.class_names[np.argmax(prediction)]
        # Tạo dictionary chứa xác suất cho từng lớp (chuyển sang phần trăm)
        probabilities = {class_name: float(prob * 100) for class_name, prob in zip(self.class_names, prediction)}
        return predicted_class, probabilities