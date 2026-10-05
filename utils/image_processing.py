import numpy as np
from PIL import Image

def preprocess_image(image: Image.Image) -> np.ndarray:
    img = image.convert("RGB").resize((224, 224))
    arr = np.array(img, dtype=np.float32)
    return np.expand_dims(arr, axis=0)
