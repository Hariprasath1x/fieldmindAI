import os
import json
import numpy as np
import onnxruntime as ort
from PIL import Image
from pathlib import Path
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
)

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
MODEL_PATH = "backend/models/fieldmind_pest.onnx"
LABELS_PATH = "backend/models/class_names.json"
DATASET_DIR = "evaluation/data/disease_classifier/"

def preprocess_image(image: Image.Image) -> np.ndarray:
    """Apply the exact same preprocessing as the production pipeline."""
    img = image.convert("RGB").resize((224, 224))
    arr = np.asarray(img, dtype=np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    arr = (arr - mean) / std
    arr = np.transpose(arr, (2, 0, 1))
    return np.expand_dims(arr, axis=0).astype(np.float32)

def softmax(logits: np.ndarray) -> np.ndarray:
    arr = np.asarray(logits, dtype=np.float32)
    arr = arr - np.max(arr)
    exp = np.exp(arr)
    return exp / np.sum(exp)

def main():
    if not os.path.exists(DATASET_DIR):
        print(f"Error: Dataset directory {DATASET_DIR} does not exist.")
        print("Please provide a representative dataset organized by class folders.")
        print("Insufficient representative evaluation data to draw reliable conclusions.")
        return

    # Load classes
    with open(LABELS_PATH, "r") as f:
        class_names = json.load(f)
    
    # Load ONNX session
    session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    
    y_true = []
    y_pred = []
    confidences = []
    
    print(f"Evaluating model: {MODEL_PATH}")
    print(f"Dataset path: {DATASET_DIR}")
    
    # Evaluate images
    class_dirs = [d for d in Path(DATASET_DIR).iterdir() if d.is_dir()]
    if not class_dirs:
        print("No class directories found in the dataset folder.")
        print("Insufficient representative evaluation data to draw reliable conclusions.")
        return
        
    for class_dir in class_dirs:
        true_label = class_dir.name
        if true_label not in class_names:
            print(f"Warning: Folder {true_label} is not in class_names.json. Skipping.")
            continue
            
        true_idx = class_names.index(true_label)
        
        for img_path in class_dir.glob("*.jpg"):
            try:
                img = Image.open(img_path)
                tensor = preprocess_image(img)
                raw = session.run(None, {input_name: tensor})[0]
                probs = softmax(np.asarray(raw).squeeze())
                pred_idx = int(np.argmax(probs))
                confidence = float(probs[pred_idx])
                
                y_true.append(true_idx)
                y_pred.append(pred_idx)
                confidences.append(confidence)
            except Exception as e:
                print(f"Failed to process {img_path}: {e}")
                
    if not y_true:
        print("No valid evaluation images found.")
        print("Insufficient representative evaluation data to draw reliable conclusions.")
        return
        
    # Calculate Metrics
    accuracy = accuracy_score(y_true, y_pred)
    macro_prec = precision_score(y_true, y_pred, average='macro', zero_division=0)
    macro_rec = recall_score(y_true, y_pred, average='macro', zero_division=0)
    macro_f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=range(len(class_names)))
    
    print("\n--- OVERALL METRICS ---")
    print(f"Total Images: {len(y_true)}")
    print(f"Accuracy:        {accuracy:.4f}")
    print(f"Macro Precision: {macro_prec:.4f}")
    print(f"Macro Recall:    {macro_rec:.4f}")
    print(f"Macro F1:        {macro_f1:.4f}")
    
    print("\n--- CONFIDENCE ANALYSIS ---")
    correct_confs = [c for t, p, c in zip(y_true, y_pred, confidences) if t == p]
    incorrect_confs = [c for t, p, c in zip(y_true, y_pred, confidences) if t != p]
    
    print(f"Avg Confidence (Correct):   {np.mean(correct_confs) if correct_confs else 0:.4f}")
    print(f"Avg Confidence (Incorrect): {np.mean(incorrect_confs) if incorrect_confs else 0:.4f}")
    
    print(f"Incorrect >= 0.75 (HIGH):   {sum(1 for c in incorrect_confs if c >= 0.75)}")
    print(f"Incorrect >= 0.45 (MEDIUM): {sum(1 for c in incorrect_confs if c >= 0.45)}")
    print(f"Correct < 0.45 (LOW):       {sum(1 for c in correct_confs if c < 0.45)}")
    print(f"Incorrect < 0.45 (LOW):     {sum(1 for c in incorrect_confs if c < 0.45)}")

if __name__ == "__main__":
    main()
