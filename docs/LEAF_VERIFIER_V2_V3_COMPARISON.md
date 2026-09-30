# LeafVerifier V2 vs V3 Comparison

## A. Why V3 was Created
During standard UI testing of the FieldMind application, the existing production model (V2) exhibited an uncertain prediction when evaluating a blurry leaf image (`G_blurry_leaf.jpg`). The V2 model returned a confidence of 51%, which bypassed the strict verification thresholds (0.90 for rejecting non-leaves, 0.85 for accepting leaves) and triggered a "fail-open" state, allowing the unprocessable image to reach the downstream disease classification pipeline. 

V3 was created as a student-project experiment to determine if training a simpler, strictly binary classifier (Leaf vs. Non-Leaf) on a small, focused dataset could definitively reject such ambiguous images without compromising overall accuracy.

## B. V2 Results
The existing V2 LeafVerifier is the production model (EfficientNet-B0 ONNX). 
*   **Known Limitations:** The model tends to produce uncertain probabilities (~50%) when encountering severe domain shifts or specific edge cases (like blur). This causes the pipeline's fallback logic to allow the image through.
*   **Historical Claims vs. Local Evaluation:** Historical project reports claim V2 achieved a Test F1 of 0.9982 on a large 580-image test set. However, the locally tracked repository evaluation set contains only 10 images, meaning comprehensive local verification of these claims is limited.

## C. V3 Approach
*   **Architecture:** EfficientNet-B0
*   **Task:** Binary Classification (LEAF vs NON_LEAF)
*   **Dataset Composition:** 1,460 images total. 
    *   **LEAF:** 757 images (sourced from HuggingFace `beans` dataset + FieldMind local test images).
    *   **NON_LEAF:** 703 images (sourced from HF `flowers` + `cats/dogs` + FieldMind local test images).
*   **Splits:** Train: 1014 (70%), Validation: 218 (15%), Test: 228 (15%).
*   **Augmentation:** Applied to the training set only (Random Horizontal Flip, Random Rotation, Color Jitter, Random Resized Crop).
*   **Training Configuration:** PyTorch, CrossEntropyLoss, Adam Optimizer (lr=1e-4), trained for 3 epochs.

## D. V3 Results
After training, V3 was evaluated on the locked Test set:
*   **Test Accuracy:** 0.9781
*   **Test Precision:** 1.0000
*   **Test Recall:** 0.9583
*   **Test F1:** 0.9787

**Confusion Matrix:**
```
[[108 (TN)    0 (FP)]
 [  5 (FN)  115 (TP)]]
```
The model achieved a perfect False Positive rate (no non-leaves were accepted), but rejected 5 valid leaves (False Negatives).

## E. Threshold Experiment
A threshold analysis was conducted on the Validation set evaluating cutoff probabilities (0.50, 0.60, 0.70, 0.80, 0.85, 0.90). 
The simple student-project dataset resulted in the model perfectly separating the Validation set, yielding an F1 score of 1.0000 across all tested thresholds. Consequently, a standard `0.50` threshold was selected. 

*Note: This threshold is not claimed to be universally optimal. The small dataset size allowed the model to over-separate the validation classes. A much larger, more diverse real-world dataset would be required to draw stronger threshold conclusions.*

## F. Problematic Image Comparison
*   **Image tested:** `G_blurry_leaf.jpg`
*   **V2 Prediction:** Uncertain (51%) -> Pipeline fail-open allowed it to process.
*   **V3 Prediction:** `NON_LEAF` (Softmax P(leaf): 0.0021, Softmax P(non_leaf): 0.9979) -> Hard rejection.

While V3 successfully and confidently rejected this specific blurry image, a single image test does not prove V3 is universally superior across all edge cases.

## G. Final Project Decision
1.  **V2 remains the production model.** 
2.  **V3 is an experimental/student-project model.** It successfully demonstrated the end-to-end ML workflow, but its slightly lower overall Test F1 (0.9787 vs V2's 0.9982) and higher False Negative rate do not justify replacing a stable production asset.
3.  **No production model or threshold was changed.** The ONNX pipeline is entirely untouched.
4.  The V3 pipeline successfully fulfills the requirement to demonstrate ML experimentation, dataset engineering, and objective evaluation within the context of a B.Tech project.
