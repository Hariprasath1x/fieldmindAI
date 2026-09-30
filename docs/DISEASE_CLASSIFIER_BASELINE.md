# Disease Classifier Baseline Evaluation

## A. Model
*   **Path:** `backend/models/fieldmind_pest.onnx`
*   **Architecture:** EfficientNet-B0 (Exported to ONNX)
*   **Classes:** 22 total (identified in `class_names.json`)

## B. Dataset
*   **Status:** **MISSING**
*   **Details:** The `evaluation/data/disease_classifier/` directory is not present in the repository, and no other representative dataset was found for the 22 supported crop/disease classes.
*   **Conclusion:** **Insufficient representative evaluation data to draw reliable conclusions.**

## C. Preprocessing
*(The evaluation script replicates the exact production inference preprocessing)*
*   **Resize:** 224x224 (RGB)
*   **Normalization:** ImageNet (Mean: `[0.485, 0.456, 0.406]`, Std: `[0.229, 0.224, 0.225]`)
*   **Format:** `NCHW` tensor

## D. Overall Metrics
*Insufficient representative evaluation data to draw reliable conclusions.*

## E. Per-Class Metrics
*Insufficient representative evaluation data to draw reliable conclusions.*

## F. Confusion Matrix
*Insufficient representative evaluation data to draw reliable conclusions.*

## G. Confidence Analysis
*Insufficient representative evaluation data to draw reliable conclusions.*

## H. Limitations
*   **No Baseline Data:** Without a representative dataset covering the 22 classes, we cannot measure actual model accuracy, verify if the model exhibits class imbalances, or determine if the current `HIGH` (0.75) and `MEDIUM` (0.45) confidence thresholds are statistically appropriate. 
*   **Action Required:** A dataset containing at least 20-50 verified images per class must be gathered and placed in `evaluation/data/disease_classifier/` before any further tuning or model replacement occurs.
