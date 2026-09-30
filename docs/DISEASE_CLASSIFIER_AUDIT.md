# Disease Classifier Audit Report

## A. Current Architecture
The Disease Classification pipeline is executed by the `MLInferenceService` (in `backend/services/ml_inference.py`), which is called asynchronously by `run_inference_job` (in `backend/worker/inference_worker.py`). 

**Flow:**
Frontend image → API Request → Redis Queue (RQ) → `inference_worker` → Image Validation → Leaf Verification → `MLInferenceService.run_classifier` → Preprocessing → ONNX Inference → Softmax Confidence Calculation → Confidence Categorization (High/Medium/Low) → YOLO Severity (if High/Medium) → Firestore Persistence → Response returned to Frontend.

## B. Model Details
*   **Model File:** `backend/models/fieldmind_pest.onnx` (16MB, likely EfficientNet-B0 based on size).
*   **Format:** ONNX (Open Neural Network Exchange).
*   **Input Preprocessing:** 
    *   Resized to 224x224 (RGB).
    *   ImageNet Normalization: Mean `[0.485, 0.456, 0.406]`, Std `[0.229, 0.224, 0.225]`.
    *   Transposed to `NCHW` format tensor.
*   **Number of Classes:** 22
*   **Class Labels:** Found in `class_names.json`. Includes 5 Cashew, 5 Cassava, 7 Maize, and 5 Tomato classes (healthy and various diseases).

## C. Dataset / Evaluation Details
*   **Dataset Used:** **UNKNOWN**. There is no documentation or metadata in the repository detailing the dataset used to train the `fieldmind_pest.onnx` model.
*   **Evaluation Images:** **UNKNOWN**.

## D. Current Metrics
*   **Accuracy / Precision / Recall / F1:** **NOT AVAILABLE**. 
*   **Confusion Matrix:** **NOT AVAILABLE**.
There are no existing evaluation scripts or ML reports for the Disease Classifier in the repository.

## E. Confidence / Threshold Behavior
*   **Confidence Calculation:** The raw logits from the ONNX model are passed through a Softmax function `_softmax()`. The confidence is the maximum probability (`np.max(probs)`).
*   **Current Thresholds:** Defined in `backend/core/config.py`.
    *   **HIGH:** `>= 0.75`
    *   **MEDIUM:** `>= 0.45`
    *   **LOW:** `< 0.45`

## F. Low-Confidence Prediction Behavior
The model **does not** have an explicit "Unknown" or "Uncertain" class. It always performs a forced choice among the 22 classes using `argmax`.

When confidence is low (e.g., `< 0.45`), the backend:
1.  Still extracts the forced `disease_label`.
2.  Sets the pipeline `status` to `"uncertain"`.
3.  Returns a specific `user_message`: *"FieldMind could not confidently identify this disease. Please upload a clearer image..."*
4.  Skips the YOLO severity analysis.
5.  **Crucially:** It still returns the `disease_label` and `confidence` in the final JSON payload (`result["disease"] = disease_label`).

**The Problematic Image (`G_blurry_leaf.jpg`):**
Because the LeafVerifier (V2) produced a 51% (Uncertain) prediction and "failed open", it passed the blurry image to the Disease Classifier. The Disease Classifier, lacking an "Unknown" class, was forced to guess. It guessed "Maize Streak Virus" with ~45% confidence. Since 45% is `>= 0.45`, it was categorized as **MEDIUM** confidence, resulting in the backend returning a "Tentative result: maize_streak_virus" to the user for an image that wasn't even a leaf.

## G. Known Limitations
1.  **Forced Choice Constraint:** The ONNX model always picks one of the 22 crops/diseases, regardless of whether the image is actually a plant. It relies entirely on the upstream LeafVerifier to filter bad images.
2.  **Blind Spot in Evaluation:** We have no idea how accurate the model is because there is no evaluation data in the repository.
3.  **Medium Threshold is Too Low:** A 45% confidence threshold for "Medium" allows highly uncertain guesses to be presented as "Tentative results" rather than being fully rejected.

## H. Recommended Next Step
**DO NOT change the model or thresholds yet.** 
The immediate next step must be to establish a **Baseline Evaluation**. We need to assemble a representative test dataset of the 22 supported classes and write an evaluation script to measure the actual Accuracy, Precision, Recall, and Confusion Matrix of the current `fieldmind_pest.onnx` production model. We cannot improve what we cannot measure.
