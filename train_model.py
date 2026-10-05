"""
Train MobileNetV2 on the class-folder crop disease dataset.

Usage:
    python train_model.py
"""
import os, json
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, Model
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE       = os.path.dirname(os.path.abspath(__file__))
TRAIN_DIR  = os.path.join(BASE, "dataset", "train")
VAL_DIR    = os.path.join(BASE, "dataset", "validation")
TEST_DIR   = os.path.join(BASE, "dataset", "test")
MODELS_DIR = os.path.join(BASE, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODELS_DIR, "crop_disease_mobilenetv2.keras")
NAMES_PATH = os.path.join(MODELS_DIR, "class_names.json")

IMG_SIZE = 224
BATCH    = 32
EPOCHS_HEAD = 8
EPOCHS_FINE = 8

# ── Validate dataset ──────────────────────────────────────────────────────────
for d in [TRAIN_DIR, VAL_DIR, TEST_DIR]:
    if not os.path.isdir(d):
        raise FileNotFoundError(f"Missing directory: {d}\nRun: python prepare_dataset.py")

class_names = sorted(os.listdir(TRAIN_DIR))
print(f"Classes ({len(class_names)}): {class_names}")

# ── Data pipelines ────────────────────────────────────────────────────────────
def make_dataset(directory, augment=False):
    ds = tf.keras.utils.image_dataset_from_directory(
        directory,
        image_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH,
        label_mode="int",
        class_names=class_names,
        shuffle=augment,
        seed=42,
    )
    def preprocess(x, y):
        x = tf.cast(x, tf.float32)
        x = preprocess_input(x)          # MobileNetV2 [-1, 1] normalisation
        return x, y

    def augment_fn(x, y):
        x = tf.image.random_flip_left_right(x)
        x = tf.image.random_brightness(x, 0.2)
        x = tf.image.random_contrast(x, 0.8, 1.2)
        x = tf.image.random_saturation(x, 0.8, 1.2)
        return x, y

    ds = ds.map(preprocess, num_parallel_calls=tf.data.AUTOTUNE)
    if augment:
        ds = ds.map(augment_fn, num_parallel_calls=tf.data.AUTOTUNE)
    return ds.prefetch(tf.data.AUTOTUNE)

train_ds = make_dataset(TRAIN_DIR, augment=True)
val_ds   = make_dataset(VAL_DIR)
test_ds  = make_dataset(TEST_DIR)

# ── Build model ───────────────────────────────────────────────────────────────
base = MobileNetV2(input_shape=(IMG_SIZE, IMG_SIZE, 3), include_top=False, weights="imagenet")
base.trainable = False

inputs  = tf.keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
x       = base(inputs, training=False)
x       = layers.GlobalAveragePooling2D()(x)
x       = layers.Dropout(0.3)(x)
outputs = layers.Dense(len(class_names), activation="softmax")(x)
model   = Model(inputs, outputs)

model.compile(
    optimizer=tf.keras.optimizers.Adam(1e-3),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

callbacks = [
    EarlyStopping(patience=4, restore_best_weights=True, verbose=1),
    ModelCheckpoint(MODEL_PATH, save_best_only=True, verbose=1),
    ReduceLROnPlateau(factor=0.5, patience=2, verbose=1),
]

# ── Phase 1: Train head ───────────────────────────────────────────────────────
print(f"\n--- Phase 1: Training classifier head ({EPOCHS_HEAD} epochs) ---")
h1 = model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS_HEAD, callbacks=callbacks)

# ── Phase 2: Fine-tune top layers ─────────────────────────────────────────────
print(f"\n--- Phase 2: Fine-tuning top 30 layers ({EPOCHS_FINE} epochs) ---")
base.trainable = True
for layer in base.layers[:-30]:
    layer.trainable = False

model.compile(
    optimizer=tf.keras.optimizers.Adam(1e-5),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)
h2 = model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS_FINE, callbacks=callbacks)

# ── Save class names ──────────────────────────────────────────────────────────
with open(NAMES_PATH, "w") as f:
    json.dump(class_names, f, indent=2)
print(f"\nClass names saved: {NAMES_PATH}")

# ── Training graphs ───────────────────────────────────────────────────────────
acc  = h1.history["accuracy"]      + h2.history["accuracy"]
vacc = h1.history["val_accuracy"]  + h2.history["val_accuracy"]
loss = h1.history["loss"]          + h2.history["loss"]
vloss= h1.history["val_loss"]      + h2.history["val_loss"]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
ax1.plot(acc, label="Train"); ax1.plot(vacc, label="Val")
ax1.set_title("Accuracy"); ax1.legend()
ax2.plot(loss, label="Train"); ax2.plot(vloss, label="Val")
ax2.set_title("Loss"); ax2.legend()
graph_path = os.path.join(MODELS_DIR, "training_history.png")
plt.savefig(graph_path, dpi=100, bbox_inches="tight")
print(f"Training graph saved: {graph_path}")

# ── Evaluation ────────────────────────────────────────────────────────────────
print("\n--- Test Set Evaluation ---")
y_true, y_pred = [], []
for imgs, labels in test_ds:
    preds = model.predict(imgs, verbose=0)
    y_pred.extend(np.argmax(preds, axis=1))
    y_true.extend(labels.numpy())

print(classification_report(y_true, y_pred, target_names=class_names))
cm = confusion_matrix(y_true, y_pred)
print("Confusion Matrix:")
print(cm)
print(f"\nModel saved: {MODEL_PATH}")
