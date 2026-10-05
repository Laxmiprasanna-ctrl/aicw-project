import os
import json
import warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore")

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE, "model", "crop_disease_model.keras")
NAMES_PATH = os.path.join(BASE, "model", "class_names.json")

_model = None
_class_names = None


def _load():
    global _model, _class_names
    if _model is None:
        import tensorflow as tf
        _model = tf.keras.models.load_model(MODEL_PATH)
        with open(NAMES_PATH) as f:
            _class_names = json.load(f)


def is_model_trained():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(NAMES_PATH):
        return False
    with open(NAMES_PATH) as f:
        names = json.load(f)
    return len(names) == 38


def predict_disease(image_array):
    _load()
    preds = _model.predict(image_array, verbose=0)[0]
    idx = int(np.argmax(preds))
    confidence = float(preds[idx])
    class_name = _class_names[idx]
    parts = class_name.split("___")
    crop = parts[0].replace("_", " ")
    disease = parts[1].replace("_", " ") if len(parts) > 1 else "Unknown"
    return {
        "class_name": class_name,
        "crop": crop,
        "disease": disease,
        "confidence": confidence,
        "is_healthy": "healthy" in class_name.lower(),
    }
