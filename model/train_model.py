"""
Train the crop disease model from a local PlantVillage-style folder.

Usage:
    python model/train_model.py --data_dir path/to/PlantVillage

The folder must contain one sub-directory per class, e.g.:
    PlantVillage/
        Apple___Apple_scab/  (*.jpg images)
        Apple___healthy/
        ...
"""
import os, json, argparse
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import tensorflow as tf

IMG_SIZE = 224
BATCH = 16
EPOCHS_HEAD = 5
EPOCHS_FINE = 5

def build_model(num_classes):
    base = tf.keras.applications.MobileNetV2(
        input_shape=(IMG_SIZE, IMG_SIZE, 3), include_top=False, weights="imagenet"
    )
    base.trainable = False
    inputs = tf.keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
    x = tf.keras.layers.Rescaling(1.0 / 255)(inputs)
    x = tf.keras.layers.RandomFlip("horizontal")(x)
    x = tf.keras.layers.RandomRotation(0.1)(x)
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    return tf.keras.Model(inputs, outputs), base

def main(data_dir):
    model_dir = os.path.dirname(os.path.abspath(__file__))

    train_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir, validation_split=0.2, subset="training",
        seed=42, image_size=(IMG_SIZE, IMG_SIZE), batch_size=BATCH
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir, validation_split=0.2, subset="validation",
        seed=42, image_size=(IMG_SIZE, IMG_SIZE), batch_size=BATCH
    )
    class_names = train_ds.class_names
    print(f"Found {len(class_names)} classes")

    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.shuffle(500).prefetch(AUTOTUNE)
    val_ds = val_ds.prefetch(AUTOTUNE)

    model, base = build_model(len(class_names))
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])

    print(f"\n--- Phase 1: Training head ({EPOCHS_HEAD} epochs) ---")
    model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS_HEAD)

    print(f"\n--- Phase 2: Fine-tuning top layers ({EPOCHS_FINE} epochs) ---")
    base.trainable = True
    for layer in base.layers[:-30]:
        layer.trainable = False
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-5),
                  loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS_FINE)

    model_path = os.path.join(model_dir, "crop_disease_model.keras")
    model.save(model_path)
    print(f"\nModel saved → {model_path}")

    names_path = os.path.join(model_dir, "class_names.json")
    with open(names_path, "w") as f:
        json.dump(class_names, f, indent=2)
    print(f"Class names saved → {names_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", required=True, help="Path to PlantVillage dataset folder")
    args = parser.parse_args()
    main(args.data_dir)
