# LeafVerifier V3 Dataset Plan

## 1. Goal
Redefine the LeafVerifier task for FieldMind as:
**"Determine whether the uploaded image contains a sufficiently visible plant leaf suitable for downstream plant-disease classification."**
This is NOT simply "leaf vs anything that isn't a leaf."

## 2. Labeling Policy

### Class 1: PROCESSABLE_LEAF
Images that contain leaf features clearly enough that a downstream classifier could reasonably attempt to diagnose a disease, even if the model's confidence might be low due to image conditions.

**Examples:**
- Clear healthy leaves
- Diseased leaves (spots, blight, necrosis, yellowing)
- Partially visible leaves
- Multiple leaves in one frame
- Curled, deformed, or damaged leaves
- Leaves under shadows or sub-optimal lighting
- Leaves with complex backgrounds (soil, hands, sky in the background)
- Different crop species (broadleaf, narrow leaf, ribbed, smooth)
- Different orientations and camera angles
- Different distances (close-up macros, medium distance crop shots)

### Class 2: NON_PROCESSABLE_IMAGE
Images where no usable leaf is visible. 

**Examples:**
- Sky and weather phenomena
- Soil, dirt, and rocks
- People, faces, and full bodies
- Hands without a usable leaf
- Animals (domestic or wild)
- Vehicles (tractors, trucks)
- Farming equipment (shovels, hoes, pipes, irrigation systems)
- Flowers without usable leaves attached in focus
- Fruits/Vegetables without usable leaves attached in focus
- Branches/stems without usable leaves
- Random objects (buildings, signs, paper)
- Completely ambiguous agricultural scenes (e.g., a wide shot of a field where no single leaf is distinct)

**IMPORTANT NOTE ON BLUR:**
Do **NOT** automatically label blurry images as `NON_PROCESSABLE_IMAGE`. Blur is strictly an image-quality problem and is handled by the upstream OpenCV Laplacian variance gate. A blurry image containing a leaf is still physically an image of a leaf.

## 3. Ambiguous Cases

| Ambiguous Case | Assigned Class | Reasoning |
| :--- | :--- | :--- |
| Hand holding a leaf | **PROCESSABLE_LEAF** | Extremely common user behavior. The leaf is the subject of the photo, making it processable. |
| Multiple leaves | **PROCESSABLE_LEAF** | Downstream classifiers (and YOLO) can handle multiple leaves. It is a valid crop image. |
| Leaf occupying only 20% of image | **PROCESSABLE_LEAF** | Still contains valid leaf features. YOLO severity models can crop or localize it. |
| Leaf partially outside frame | **PROCESSABLE_LEAF** | Common framing issue. The visible portion can still show disease markers. |
| Heavily diseased/dead leaf | **PROCESSABLE_LEAF** | Crucial for the disease classifier. The verifier must not reject dead leaves. |
| Very dark leaf | **PROCESSABLE_LEAF** | Downstream classifiers should be given a chance; if too dark, they return low confidence. |
| Wet leaf | **PROCESSABLE_LEAF** | Rain/dew is normal. It is still a leaf. |
| Leaf with strong glare | **PROCESSABLE_LEAF** | Sun glare happens in fields. Downstream handles confidence. |
| Leaf mixed with soil/background | **PROCESSABLE_LEAF** | Realistic agricultural background. The leaf is still present. |
| Branch containing leaves | **PROCESSABLE_LEAF** | As long as leaves are visible and somewhat in focus, it is processable. |
| Bare branch (no leaves) | **NON_PROCESSABLE_IMAGE** | We classify leaf diseases. A bare branch provides no leaf features. |
| Several different plant parts (stem, fruit, flower) without leaf | **NON_PROCESSABLE_IMAGE** | The pipeline relies on leaf symptoms. Fruits/stems without leaves cannot be processed accurately by the current pipeline. |

## 4. Dataset Sources Audit

Current V2 sources and their suitability for V3:

| Source | Intended Class | Advantages | Weaknesses | Domain Mismatch | Retain? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AI-Lab-Makerere/beans` | PROCESSABLE_LEAF | High-quality, real field bean leaves. | Over-represents a single crop type and geography. | Low for beans, high for other crops. | **YES**, but dilute heavily with other crops. |
| `ayerr/plant-disease-classification` | PROCESSABLE_LEAF | Broad range of crops and diseases. | Backgrounds are often artificial (lab settings, solid colors). | High, lacks realistic field backgrounds. | **YES**, but supplement with field photos. |
| `Bingsu/Cat_and_Dog` | NON_PROCESSABLE_IMAGE | Good basic negative class. | Zero agricultural relevance. | Extremely high. | **NO**, discard entirely. |
| `nelorth/oxford-flowers` | NON_PROCESSABLE_IMAGE | Plant-related negatives. | Focused mostly on aesthetic floral photography. | High. Real agricultural negatives (soil, tractors) are missing. | **NO**, or severely reduce. |

## 5. Hard Negatives Requirements

A rigorous negative dataset must contain the following to prevent False Positives:
- **Soil & Ground:** The most common background when pointing a phone down.
- **Sky & Clouds:** The most common background when pointing a phone up.
- **Bark, Branches, & Stems:** Highly plant-related but lacking leaf tissue for diagnosis.
- **Hands & People:** Users accidentally taking photos of themselves or their hands.
- **Flowers & Fruits:** Plant features that the disease classifier is not trained for.
- **Agricultural Equipment:** Tractors, irrigation pipes, tools.
- **Random Objects:** Green fabrics, green paper, boots.
- **Leaf-like Shapes:** Objects with contours mimicking leaves (e.g., certain insects, green crumpled materials).
- **Ambiguous Agricultural Scenes:** Wide shots of a field where individual leaves are indistinguishable.

## 6. Hard Positives Requirements

To prevent False Negatives (rejecting valid leaves), the positive dataset must contain:
- **Healthy Leaves:** Baseline crop appearances.
- **Diseased Leaves:** All severity levels, including entirely necrotic/dead leaves.
- **Partial/Cropped Leaves:** Leaves cut off by the camera frame.
- **Curled/Damaged Leaves:** Leaves deformed by pests or environmental stress.
- **Low-light/Shadowed Leaves:** Photos taken at dawn, dusk, or under heavy canopy shadow.
- **Complex Backgrounds:** Leaves blending into weeds, soil, or other leaves.
- **Multiple Leaves:** Cluttered frames.
- **Different Crops:** Ensuring broadleaf, narrow leaf, and diverse morphologies are represented.
- **Different Camera Distances:** Ranging from extreme macro to 2-3 feet away.

## 7. Dataset Split Strategy

**Rule:** The Test Set must NEVER influence model selection, hyperparameter tuning, or threshold selection.

**Leakage Prevention:**
- **Source-Aware Splitting:** If multiple images come from the same physical plant/video, all images from that source must go into the SAME split.
- **Deduplication:** Run exact and perceptual hashing (e.g., PHash) to remove duplicate or near-duplicate images before splitting.
- **Augmentation Safety:** Augmentations must ONLY be applied to the Training set dynamically at train-time, never pre-generated and leaked across splits.

**Target Distribution:**
- **TRAIN (70%):** Used for backpropagation.
- **VALIDATION (15%):** Used for Early Stopping, model selection (Experiment A vs B), and Threshold tuning.
- **TEST (15%):** Completely locked. Used strictly for the final metrics report.

## 8. Dataset Size Target

Realistic engineering targets for a robust V3 verification model:
- **Total Positive Images:** ~2,500 - 3,500
- **Total Negative Images:** ~2,500 - 3,500
- **Number of Hard Negatives:** At least 1,500 (soil, hands, branches, agricultural scenes).
- **Validation Size:** ~750 - 1,000 images.
- **Test Size:** ~750 - 1,000 images.

*(Note: These are minimum engineering targets. More high-quality, deduplicated data is always better.)*

## 9. Augmentation Plan

Augmentations must be realistic and reflect conditions a mobile phone camera might capture in a field.

**Recommended:**
- **Horizontal/Vertical Flip:** Plants lack strict up/down orientation rules in macro shots.
- **Small Rotations:** $\pm 45^\circ$ to simulate casual phone angles.
- **Brightness & Contrast Jitter:** To simulate varying sunlight, shadows, and overexposure/underexposure.
- **Crop & Scale (Random Resized Crop):** To simulate different distances and framing.
- **Mild Blur / Gaussian Noise:** To ensure the model remains robust to slight camera movement, even if severe blur is handled upstream.
- **JPEG Compression Artifacts:** Simulates uploads from low-bandwidth mobile connections.

**AVOID:**
- **Extreme color jitter (Hue shifts):** Turning a green leaf purple destroys disease-related color semantics.
- **Unrealistic warps/distortions:** Shearing or extreme perspective shifts that physically break plant morphology.
- **Cutout / MixUp:** While mathematically sound, they create visually impossible images (e.g., half a tractor merged with half a leaf) which is unnecessary for this simple verification task.
