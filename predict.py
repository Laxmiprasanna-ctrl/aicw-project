"""
predict.py — disease prediction for all trained crops.
"""
import os, json, warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore")

import numpy as np
from PIL import Image

BASE       = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "models", "crop_disease_mobilenetv2.keras")
NAMES_PATH = os.path.join(BASE, "models", "class_names.json")

LOW_CONF = 0.60

_model       = None
_class_names = None

# class_key -> (crop_display, disease_display)
_DISPLAY = {
    # Tomato
    "Tomato_Healthy":            ("Tomato", "Healthy"),
    "Tomato_Bacterial_Spot":     ("Tomato", "Bacterial Spot"),
    "Tomato_Early_Blight":       ("Tomato", "Early Blight"),
    "Tomato_Late_Blight":        ("Tomato", "Late Blight"),
    "Tomato_Leaf_Mold":          ("Tomato", "Leaf Mold"),
    "Tomato_Septoria_Leaf_Spot": ("Tomato", "Septoria Leaf Spot"),
    "Tomato_Spider_Mites":       ("Tomato", "Spider Mites"),
    "Tomato_Target_Spot":        ("Tomato", "Target Spot"),
    "Tomato_Mosaic_Virus":       ("Tomato", "Mosaic Virus"),
    "Tomato_Yellow_Leaf_Curl":   ("Tomato", "Yellow Leaf Curl Virus"),
    # Potato
    "Potato_Healthy":            ("Potato", "Healthy"),
    "Potato_Early_Blight":       ("Potato", "Early Blight"),
    "Potato_Late_Blight":        ("Potato", "Late Blight"),
    # Corn
    "Corn_Healthy":              ("Corn/Maize", "Healthy"),
    "Corn_Gray_Leaf_Spot":       ("Corn/Maize", "Gray Leaf Spot"),
    "Corn_Common_Rust":          ("Corn/Maize", "Common Rust"),
    "Corn_Northern_Leaf_Blight": ("Corn/Maize", "Northern Leaf Blight"),
    # Apple
    "Apple_Healthy":             ("Apple", "Healthy"),
    "Apple_Apple_Scab":          ("Apple", "Apple Scab"),
    "Apple_Black_Rot":           ("Apple", "Black Rot"),
    "Apple_Cedar_Apple_Rust":    ("Apple", "Cedar Apple Rust"),
    # Grape
    "Grape_Healthy":             ("Grape", "Healthy"),
    "Grape_Black_Rot":           ("Grape", "Black Rot"),
    "Grape_Esca_Black_Measles":  ("Grape", "Esca / Black Measles"),
    "Grape_Leaf_Blight":         ("Grape", "Leaf Blight"),
    # Chili
    "Chili_Healthy":             ("Chili", "Healthy"),
    "Chili_Bacterial_Spot":      ("Chili", "Bacterial Spot"),
}

# Crops whose leaf images the model can actually classify
TRAINED_CROPS = {"Tomato", "Potato", "Corn/Maize", "Apple", "Grape", "Chili"}


def is_model_available():
    return os.path.exists(MODEL_PATH) and os.path.exists(NAMES_PATH)


def _load():
    global _model, _class_names
    if _model is not None:
        return
    import tensorflow as tf
    _model = tf.keras.models.load_model(MODEL_PATH)
    with open(NAMES_PATH) as f:
        _class_names = json.load(f)


def _preprocess(pil_image: Image.Image) -> np.ndarray:
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
    img = pil_image.convert("RGB").resize((224, 224))
    arr = np.array(img, dtype=np.float32)
    return np.expand_dims(preprocess_input(arr), axis=0)


def predict_disease(pil_image: Image.Image, selected_crop: str = None) -> dict:
    """
    Runs the model and returns the best prediction.
    If selected_crop is given, also checks whether the predicted crop
    matches the user's selection and flags a mismatch.
    """
    if not is_model_available():
        raise ValueError("Trained model not found. Run: python train_model.py")

    _load()
    arr   = _preprocess(pil_image)
    preds = _model.predict(arr, verbose=0)[0]
    # A crop is explicitly selected in the scanner. Classify among that
    # crop's trained disease classes so a small cross-crop score advantage
    # cannot route the user to another crop's treatment plan.
    selected_indices = [
        i for i, key in enumerate(_class_names)
        if selected_crop is not None
        and _DISPLAY.get(key, (key, "Unknown"))[0].lower() == selected_crop.lower()
    ]
    crop_probs = None
    if selected_indices:
        selected_scores = preds[selected_indices]
        idx = selected_indices[int(np.argmax(selected_scores))]
        crop_total = float(np.sum(selected_scores))
        conf = float(preds[idx] / crop_total) if crop_total > 0 else float(preds[idx])
        crop_probs = {
            crop_name: float(sum(preds[i] for i, key in enumerate(_class_names)
                                 if _DISPLAY.get(key, (key, "Unknown"))[0] == crop_name))
            for crop_name in sorted(TRAINED_CROPS)
        }
    else:
        idx = int(np.argmax(preds))
        conf = float(preds[idx])

    class_key          = _class_names[idx]
    crop_disp, dis_disp = _DISPLAY.get(class_key, (class_key, "Unknown"))
    is_healthy         = "Healthy" in dis_disp

    strongest_crop = max(crop_probs, key=crop_probs.get) if crop_probs else crop_disp
    crop_mismatch = bool(selected_crop and strongest_crop.lower() != selected_crop.lower())

    top_indices = np.argsort(preds)[::-1][:3]
    top_predictions = []
    if selected_indices:
        top_indices = np.array(selected_indices)[np.argsort(preds[selected_indices])[::-1][:3]]
    for top_idx in top_indices:
        top_key = _class_names[int(top_idx)]
        top_crop, top_disease = _DISPLAY.get(top_key, (top_key, "Unknown"))
        top_predictions.append({"crop": top_crop, "disease": top_disease,
                                "class_key": top_key, "confidence": float(preds[top_idx])})

    return {
        "crop":           crop_disp,
        "disease":        dis_disp,
        "class_key":      class_key,
        "confidence":     conf,
        "model_confidence": float(preds[idx]),
        "confidence_pct": f"{conf * 100:.2f}%",
        "status":         "Healthy" if is_healthy else "Diseased",
        "low_confidence": conf < LOW_CONF,
        "crop_mismatch":  crop_mismatch,
        "strongest_crop": strongest_crop,
        "crop_probabilities": crop_probs,
        "selected_crop":  selected_crop,
        "top_predictions": top_predictions,
    }
