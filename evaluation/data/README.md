# Evaluation Dataset Guide

This directory holds evaluation datasets for FieldMind's ML models.
None of these datasets are committed to the repository — you must provide them.

## Disease Classifier

**Location**: `evaluation/data/disease_classifier/`

**Format**: Class-named subdirectories containing image files.

```
disease_classifier/
    cashew_anthracnose/
        img001.jpg
        img002.jpg
    cashew_healthy/
        img001.jpg
    ...
```

Each subdirectory name must exactly match a class from `models/class_names.json`:

```json
["cashew_anthracnose", "cashew_gumosis", "cashew_healthy", "cashew_leaf_miner",
 "cashew_red_rust", "cassava_bacterial_blight", "cassava_brown_spot",
 "cassava_green_mite", "cassava_healthy", "cassava_mosaic",
 "maize_fall_armyworm", "maize_grasshoper", "maize_healthy",
 "maize_leaf_beetle", "maize_leaf_blight", "maize_leaf_spot",
 "maize_streak_virus", "tomato_healthy", "tomato_leaf_blight",
 "tomato_leaf_curl", "tomato_septoria_leaf_spot", "tomato_verticulium_wilt"]
```

Minimum recommended: 20 images per class for meaningful metrics.

---

## Leaf Verifier

**Location**: `evaluation/data/leaf_verifier/`

**Format**:
```
leaf_verifier/
    leaf/
        img001.jpg ...
    non_leaf/
        img001.jpg ...
```

---

## YOLO Detector

**Location**: `evaluation/data/yolo_detector/`

**Format**: YOLO annotation format (class cx cy w h — normalised).
```
yolo_detector/
    images/
        img001.jpg
    labels/
        img001.txt   ← one detection per line: "0 0.5 0.4 0.3 0.2"
```

Class indices correspond to `models/yolo_classes.json`:
```json
{"0": "anthracnose", "1": "fall armyworm", "2": "leaf blight", "3": "leaf_curl"}
```

---

## Crop Recommender

**Location**: `evaluation/data/crop_recommender/test.csv`

**Format**: CSV with header row.
```
N,P,K,temperature,humidity,pH,rainfall,label
90,42,43,20.87,82.00,6.5,202.9,rice
```

The `label` column must match the crop names the model was trained on.

---

## Running Evaluation

```bash
# Evaluate all models
python -m evaluation.evaluate

# Evaluate only the disease classifier
python -m evaluation.evaluate --models disease

# Custom directories
python -m evaluation.evaluate --models-dir /path/to/models --output-dir /path/to/results
```

Results are saved as timestamped JSON files in `evaluation/results/`.
