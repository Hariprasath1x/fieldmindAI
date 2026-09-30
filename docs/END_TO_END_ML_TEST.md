# End-to-End ML Pipeline Test

## A. Test Objective
The goal of this test is to verify the end-to-end behavior of the existing ML pipeline using a small sample of locally available test images. The focus is to observe the interaction between the image validation, LeafVerifier, and Disease Classifier stages, ensuring that obviously unsuitable images are correctly handled before generating potentially misleading disease predictions.

## B. Images Tested
The following images from `tests/ml/test_images/` were used:
1. `A_clear_leaf.jpg`
2. `D_non_leaf_object.jpg`
3. `G_blurry_leaf.jpg`
4. `I_partial_leaf.jpg`

*(Note: No ground-truth disease labels are available for these images. Metrics like "correctness" cannot be assessed.)*

## C. Pipeline Flow
The backend pipeline executes sequentially:
1. **Image Validation:** Checks format, size, and blur (`cv2.Laplacian` variance).
2. **LeafVerifier:** Predicts if the image is a leaf. Rejects if not.
3. **Disease Classifier:** Predicts the disease label and categorizes confidence (HIGH/MEDIUM/LOW).
4. **YOLO Severity:** (If HIGH/MEDIUM confidence) Locates affected areas.
5. **Final Recommendation:** Generates user-facing text based on the confidence level.

## D. Results Table

| Image | Validation Stage | LeafVerifier (Allow?) | Disease Classifier | Confidence Level | Final Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`A_clear_leaf.jpg`** | Passed | Verified (99.9%) - **Yes** | `cassava_brown_spot` (0.46) | MEDIUM | `ok` (Tentative result) |
| **`D_non_leaf_object.jpg`**| Passed | Rejected (99.5%) - **No** | *Skipped* | N/A | `rejected` (Not a leaf) |
| **`G_blurry_leaf.jpg`** | **Failed (Blurry)** | *Skipped* | *Skipped* | N/A | `failed` (Image too blurry) |
| **`I_partial_leaf.jpg`** | **Failed (Blurry)** | *Skipped* | *Skipped* | N/A | `failed` (Image too blurry) |

## E. Previous Problematic Case
**Image:** `G_blurry_leaf.jpg`
*   **Historical Issue:** It was previously reported that the LeafVerifier allowed this image through with an "Uncertain" status, causing the Disease Classifier to predict "Maize Streak Virus" with ~45% confidence.
*   **Current Observation:** The pipeline successfully **prevented** this image from reaching the LeafVerifier or Disease Classifier. It was rejected at Stage 1 (`image_validation`) with the error code `IMAGE_TOO_BLURRY` (blur score 0.0 vs threshold 100.0). The pipeline correctly short-circuited and prevented a misleading prediction.

## F. Observed Limitations
1. **No Ground Truth:** The pipeline returned `cassava_brown_spot` for `A_clear_leaf.jpg`, but without a verified ground-truth label, we cannot confirm if the model is accurate.
2. **Medium Confidence Output:** For `A_clear_leaf.jpg`, the disease classifier output a maximum confidence of ~46%. Because this crosses the `0.45` threshold, it was presented as a "Medium" confidence result, which still outputs a specific disease label to the user.
3. **YOLO Misalignment:** The YOLO severity model ran on `A_clear_leaf.jpg` and detected "anthracnose" and "fall armyworm" despite the main disease classifier outputting "cassava_brown_spot". The YOLO and classification pipelines operate independently, which could lead to conflicting user information.

## G. Final Conclusion
The backend inference pipeline functions cohesively. It correctly short-circuits on low-quality (blurry) and non-leaf images, successfully protecting the Disease Classifier from garbage inputs. However, because we lack a representative evaluation dataset, the actual accuracy of the disease and YOLO models remains completely unknown.
