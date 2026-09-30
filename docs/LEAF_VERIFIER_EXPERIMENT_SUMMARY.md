# Leaf Verification ML Experiment (Student Project Summary)

## 1. Objective
The goal of this experiment was to build and evaluate a simplified binary image classifier that can answer a single question: **"Does this image contain a plant leaf suitable for disease classification?"** 

This experiment was conducted to understand the end-to-end machine learning lifecycle (data gathering, preprocessing, training, threshold tuning, and evaluation) in response to edge cases observed in the original production model.

## 2. Dataset Collection & Preparation
Instead of using massive enterprise datasets, a practical, accessible dataset of 1,460 images was compiled:
*   **LEAF Class (757 images):** Sourced from the HuggingFace `beans` dataset and local FieldMind test images.
*   **NON_LEAF Class (703 images):** Sourced from HuggingFace `flowers`, `cats/dogs`, and local test images (representing hands, soil, and sky).

The dataset was safely split into three isolated groups:
*   **Training Set (70%):** 1,014 images used to update model weights.
*   **Validation Set (15%):** 218 images used to evaluate thresholds.
*   **Test Set (15%):** 228 images securely locked away for the final evaluation.

## 3. Model Training
*   **Architecture:** EfficientNet-B0 (a lightweight, highly efficient CNN).
*   **Augmentation:** To prevent overfitting on a small dataset, training images were dynamically augmented using Random Horizontal Flips, Random Rotations, Color Jitter, and Random Resized Cropping.
*   **Optimization:** Trained using the Adam optimizer and standard Cross-Entropy Loss for 3 epochs.

## 4. Evaluation & Metrics
The model was first evaluated on the Validation set across various confidence thresholds (0.50 to 0.90). Due to the dataset's simplicity, the model perfectly separated the validation images, allowing us to safely choose a standard 0.50 threshold.

**Final Test Set Results:**
*   **Accuracy:** 97.81%
*   **Precision:** 100% (Zero False Positives: No non-leaves were wrongly accepted).
*   **Recall:** 95.83% (Five True leaves were wrongly rejected).
*   **F1-Score:** 0.9787

## 5. Conclusion
The experiment successfully produced a highly accurate binary classifier capable of filtering out non-leaf images with 100% precision on the test set. It also successfully identified and rejected specific blurry edge-case images that confused previous models. 

However, because the existing FieldMind production model (V2) is already highly optimized in ONNX format and demonstrates slightly higher overall recall, this V3 model is retained purely as a successful academic experiment and proof-of-concept. The production environment remains unchanged.
