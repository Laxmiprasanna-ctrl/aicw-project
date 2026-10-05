"""Evaluate the saved classifier on dataset/test and write real metrics."""
import json
import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
import numpy as np
import tensorflow as tf
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, precision_recall_fscore_support)

BASE = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(BASE, "dataset", "test")
MODEL_PATH = os.path.join(BASE, "models", "crop_disease_mobilenetv2.keras")
NAMES_PATH = os.path.join(BASE, "models", "class_names.json")
OUTPUT_PATH = os.path.join(BASE, "models", "metrics.json")


def main():
    if not os.path.isfile(MODEL_PATH):
        raise FileNotFoundError(f"Trained model not found: {MODEL_PATH}")
    if not os.path.isdir(TEST_DIR):
        raise FileNotFoundError(f"Test dataset not found: {TEST_DIR}")
    with open(NAMES_PATH, encoding="utf-8") as f:
        names = json.load(f)
    ds = tf.keras.utils.image_dataset_from_directory(
        TEST_DIR, image_size=(224, 224), batch_size=32, shuffle=False,
        class_names=names, label_mode="int")
    ds = ds.map(lambda images, labels: (
        tf.keras.applications.mobilenet_v2.preprocess_input(tf.cast(images, tf.float32)), labels))
    model = tf.keras.models.load_model(MODEL_PATH)
    y_true, y_pred = [], []
    for images, labels in ds:
        probabilities = model.predict(images, verbose=0)
        y_pred.extend(np.argmax(probabilities, axis=1).tolist())
        y_true.extend(labels.numpy().tolist())
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=list(range(len(names))), zero_division=0)
    report = classification_report(y_true, y_pred, labels=list(range(len(names))),
                                   target_names=names, output_dict=True, zero_division=0)
    metrics = {
        "model": "MobileNetV2", "evaluation_split": "dataset/test",
        "samples": len(y_true), "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(np.mean(precision)), "recall_macro": float(np.mean(recall)),
        "f1_macro": float(np.mean(f1)), "class_names": names,
        "class_wise": {name: report[name] for name in names},
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=list(range(len(names)))).tolist(),
    }
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"Evaluation saved to {OUTPUT_PATH}")
    print(f"Accuracy: {metrics['accuracy']:.4f} | Macro F1: {metrics['f1_macro']:.4f}")


if __name__ == "__main__":
    main()
