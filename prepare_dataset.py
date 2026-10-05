"""
Prepares dataset for all available crops from PlantVillage.
Run: python prepare_dataset.py
"""
import os, shutil, random

SOURCE = r"C:\Users\ajmee\Downloads\archive (1)\plantvillage dataset\color"
DEST   = os.path.join(os.path.dirname(__file__), "dataset")

# dest_class_name -> source_folder_name
CLASS_MAP = {
    # Tomato (5 classes)
    "Tomato_Healthy":           "Tomato___healthy",
    "Tomato_Bacterial_Spot":    "Tomato___Bacterial_spot",
    "Tomato_Early_Blight":      "Tomato___Early_blight",
    "Tomato_Late_Blight":       "Tomato___Late_blight",
    "Tomato_Leaf_Mold":         "Tomato___Leaf_Mold",
    "Tomato_Septoria_Leaf_Spot":"Tomato___Septoria_leaf_spot",
    "Tomato_Spider_Mites":      "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato_Target_Spot":       "Tomato___Target_Spot",
    "Tomato_Mosaic_Virus":      "Tomato___Tomato_mosaic_virus",
    "Tomato_Yellow_Leaf_Curl":  "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    # Potato (3 classes)
    "Potato_Healthy":           "Potato___healthy",
    "Potato_Early_Blight":      "Potato___Early_blight",
    "Potato_Late_Blight":       "Potato___Late_blight",
    # Corn/Maize (4 classes)
    "Corn_Healthy":             "Corn_(maize)___healthy",
    "Corn_Gray_Leaf_Spot":      "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_Common_Rust":         "Corn_(maize)___Common_rust_",
    "Corn_Northern_Leaf_Blight":"Corn_(maize)___Northern_Leaf_Blight",
    # Apple (4 classes)
    "Apple_Healthy":            "Apple___healthy",
    "Apple_Apple_Scab":         "Apple___Apple_scab",
    "Apple_Black_Rot":          "Apple___Black_rot",
    "Apple_Cedar_Apple_Rust":   "Apple___Cedar_apple_rust",
    # Grape (4 classes)
    "Grape_Healthy":            "Grape___healthy",
    "Grape_Black_Rot":          "Grape___Black_rot",
    "Grape_Esca_Black_Measles": "Grape___Esca_(Black_Measles)",
    "Grape_Leaf_Blight":        "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    # Chili/Pepper (2 classes)
    "Chili_Healthy":            "Pepper,_bell___healthy",
    "Chili_Bacterial_Spot":     "Pepper,_bell___Bacterial_spot",
}

IMAGES_PER_CLASS = 200
TRAIN_R, VAL_R   = 0.70, 0.15
random.seed(42)

def copy_split(src_dir, cls_name):
    imgs = [f for f in os.listdir(src_dir)
            if f.lower().endswith((".jpg",".jpeg",".png"))]
    random.shuffle(imgs)
    imgs = imgs[:IMAGES_PER_CLASS]
    n_train = int(len(imgs) * TRAIN_R)
    n_val   = int(len(imgs) * VAL_R)
    splits  = {
        "train":      imgs[:n_train],
        "validation": imgs[n_train:n_train+n_val],
        "test":        imgs[n_train+n_val:],
    }
    for split, files in splits.items():
        d = os.path.join(DEST, split, cls_name)
        os.makedirs(d, exist_ok=True)
        for f in files:
            shutil.copy2(os.path.join(src_dir, f), os.path.join(d, f))
        print(f"  {split:12s} {cls_name:35s} {len(files)} images")

print("Preparing dataset...\n")
for cls_name, src_folder in CLASS_MAP.items():
    src = os.path.join(SOURCE, src_folder)
    if not os.path.isdir(src):
        print(f"  SKIP (not found): {src_folder}")
        continue
    copy_split(src, cls_name)

print(f"\nDone. Dataset: {DEST}")
print(f"Total classes: {len(CLASS_MAP)}")
