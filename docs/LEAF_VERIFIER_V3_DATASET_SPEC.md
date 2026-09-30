# LeafVerifier V3 Dataset Specification

## 1. Final Label Definitions

The annotation process relies on a tri-state system. The final trained model will remain binary (`PROCESSABLE_LEAF` vs `NON_PROCESSABLE_IMAGE`), but the intermediate `AMBIGUOUS_REVIEW` class prevents annotators from forcing highly uncertain images into either class, allowing a senior reviewer to decide if the sample is viable or should be discarded.

### A. PROCESSABLE_LEAF
An image containing sufficient leaf structure and visual detail that a downstream disease classification model or human expert could reasonably attempt a diagnosis.
*   **Partial leaves / Leaves partially outside frame:** `PROCESSABLE_LEAF` as long as enough surface area is visible to identify potential disease markers.
*   **Small leaves / Distant leaves:** `PROCESSABLE_LEAF` if they occupy enough pixels for disease textures to be resolvable (not merely green specks).
*   **Multiple leaves:** `PROCESSABLE_LEAF` (highly common).
*   **Diseased / Heavily necrotic leaves:** `PROCESSABLE_LEAF`. We must not reject sick/dying leaves.
*   **Curled leaves:** `PROCESSABLE_LEAF`.
*   **Leaves held by hand / mixed with soil / complex backgrounds:** `PROCESSABLE_LEAF`. Background clutter does not invalidate the leaf.
*   **Leaves with flowers/fruits:** `PROCESSABLE_LEAF` if the leaf itself is sufficiently visible and in focus.
*   **Branches containing leaves:** `PROCESSABLE_LEAF` if the leaves are visible.
*   **Low-light / shadowed leaves / glare:** `PROCESSABLE_LEAF`. Downstream models handle low confidence.

### B. NON_PROCESSABLE_IMAGE
An image where no usable leaf is present, or leaf material is so minimal/distorted that a disease diagnosis is fundamentally impossible.
*   **Extremely small leaves:** `NON_PROCESSABLE_IMAGE` (e.g., a landscape shot of a field where leaves are just a few green pixels).
*   **Completely unrecognizable plant material:** `NON_PROCESSABLE_IMAGE` (e.g., a dried-up stem with no leaf tissue left).
*   **Pure non-leaf images:** Soil, sky, hands, tractors, buildings, animals.
*   **Bare branches / stems / bark:** `NON_PROCESSABLE_IMAGE`.
*   **Isolated flowers/fruits:** `NON_PROCESSABLE_IMAGE` (if no attached leaf is visible).

### C. AMBIGUOUS_REVIEW
Samples where the annotator is uncertain if enough structural detail exists to diagnose a disease.
*   **Severe Occlusion:** A leaf is barely visible behind a thick branch.
*   **Extreme Macro:** An image zoomed in so closely on a leaf's veins that the context of "leaf" is lost.
*   **Severe Camera Blur:** While blur is normally handled upstream, if an annotator cannot tell if the blurry green blob is a leaf or a green jacket, it goes to review.

---

## 2. Annotation Decision Tree

Annotators must follow this logic flow for every image:

```text
[START]
  |
  +-- Does the image contain any plant leaf tissue?
       |
       +-- NO ---> [NON_PROCESSABLE_IMAGE]
       |
       +-- YES ---> Is the leaf tissue large and detailed enough to potentially show disease markers?
                     |
                     +-- NO ---> Is it truly impossible to diagnose (e.g., landscape shot)?
                     |            |
                     |            +-- YES ---> [NON_PROCESSABLE_IMAGE]
                     |            |
                     |            +-- NO (Unsure) ---> [AMBIGUOUS_REVIEW]
                     |
                     +-- YES ---> Is the leaf heavily obscured by extreme blur, occlusion, or lighting?
                                   |
                                   +-- YES (Unsure if usable) ---> [AMBIGUOUS_REVIEW]
                                   |
                                   +-- NO ---> [PROCESSABLE_LEAF]
```

---

## 3. Dataset Sources

We must curate real-world datasets rather than synthetic or purely academic sets. 

### A. Positive Agricultural Leaf Images
*   **Source Name:** PlantVillage (Kaggle/Penn State)
    *   **URL:** https://github.com/spMohanty/PlantVillage-Dataset
    *   **License:** Open/CC
    *   **Approx. Size:** 54,000+ images
    *   **Intended Class:** `PROCESSABLE_LEAF`
    *   **Strengths:** Massive variety of crops (apples, tomatoes, potatoes) and diseases.
    *   **Weaknesses:** Backgrounds are highly artificial (lab settings, paper).
    *   **Domain Mismatch:** High mismatch in backgrounds; requires heavy supplementation.
    *   **Decision:** **USE (Sampled heavily to avoid domination).**

*   **Source Name:** CGIAR Crop Disease Datasets (e.g., Cassava Disease)
    *   **URL:** https://www.kaggle.com/c/cassava-disease
    *   **License:** Varies / Kaggle
    *   **Approx. Size:** 10,000+ images
    *   **Intended Class:** `PROCESSABLE_LEAF`
    *   **Strengths:** Real field photos, African/tropical contexts, hands, soil backgrounds.
    *   **Weaknesses:** Skewed heavily to specific crops (Cassava).
    *   **Domain Mismatch:** Low (highly representative of FieldMind).
    *   **Decision:** **USE (Primary positive source).**

### B. Agricultural Hard Negatives
*   **Source Name:** Crop/Weed Field Image Dataset (CWFID)
    *   **URL:** https://github.com/cwfid/dataset
    *   **License:** MIT
    *   **Approx. Size:** ~60 images (very small)
    *   **Intended Class:** Mixed / `NON_PROCESSABLE_IMAGE` (if zooming on soil)
    *   **Decision:** Skip due to size. 

*   **Source Name:** OpenImages V7 (Filtered for specific classes)
    *   **URL:** https://storage.googleapis.com/openimages/web/index.html
    *   **License:** CC BY 4.0
    *   **Approx. Size:** Millions (Filter for: "Soil", "Tractor", "Human hand", "Tree bark")
    *   **Intended Class:** `NON_PROCESSABLE_IMAGE`
    *   **Strengths:** Immense scale and variety.
    *   **Weaknesses:** Requires careful filtering to ensure leaves aren't accidentally present in "Tractor" images.
    *   **Domain Mismatch:** Medium (general photography vs smartphone farm photos).
    *   **Decision:** **USE (Requires strict manual filtering).**

### C. Custom FieldMind Dataset (To Be Collected)
*   **Source Name:** Internal FieldMind Pilot Data
    *   **Intended Class:** Both
    *   **Strengths:** Zero domain mismatch; exactly what users upload.
    *   **Decision:** **USE (Highest priority for Test Set).**

---

## 4. Hard Negative Priority

To combat the high False Acceptance Rate observed when lowering thresholds, we must prioritize negative samples that smartphone users physically encounter on farms:

1.  **Hands / Human skin:** (Most common accidental framing).
2.  **Soil / Dirt / Rocks:** (Background when pointing phone downward).
3.  **Sky / Sun glare:** (Background when pointing phone upward).
4.  **Stems / Branches / Bark:** (Plant parts mistakenly photographed instead of leaves).
5.  **Fruits / Flowers / Vegetables:** (Often photographed by farmers wanting disease diagnosis on the fruit itself, which our current leaf-based pipeline cannot handle).
6.  **Wide agricultural scenes:** (Landscapes where individual leaves are just noise).
7.  **Agricultural equipment:** (Tractors, hoes, pipes).
8.  **Green objects:** (Clothes, buckets, paper that confuse basic color-based features).
9.  **Random objects:** (Pockets, jeans, shoes).

---

## 5. Positive Coverage Matrix

We must ensure the V3 dataset covers combinations missing from V2:

| Feature | Covered in V2? | Needed for V3 |
| :--- | :--- | :--- |
| **Healthy Leaves** | Yes (Beans only) | Add Maize, Cassava, Tomato, Apple |
| **Diseased Leaves** | Yes (Beans only) | Add Rust, Blight, Mildew, Necrosis |
| **Disease Severity** | Mild/Medium only | Need dead, heavily necrotic leaves |
| **Lighting** | Lab lighting | Need shadows, golden hour, overcast |
| **Background** | Lab / Plain | Need soil, hands, complex clutter |
| **Camera Distance** | Uniform (Medium) | Need extreme macro and 3-foot wide shots |
| **Orientation** | Flat | Need angled, sideways, upside-down |
| **Occlusion** | None | Need leaves partially hidden by stems |
| **Leaf Damage** | None | Need insect-eaten, torn, folded leaves |

---

## 6. Leakage Prevention Strategy

To guarantee the Test set remains untouched by the training process, follow this exact procedure:

1.  **Downloading & Ingestion:** Download all raw datasets into a staging directory.
2.  **Computing Hashes:** Compute SHA-256 (exact duplicate) and PHash (perceptual/near-duplicate) for every image.
3.  **Removing Exact Duplicates:** Drop images with identical SHA-256 hashes.
4.  **Detecting Near Duplicates:** Group images where PHash distance $< 5$. 
5.  **Grouping by Source (Crucial):** If images are extracted from the same video frame sequence, or identified via EXIF data as being taken on the same device in the same minute, assign them a unified `group_id`.
6.  **Splitting by Group:** Randomly assign `group_id`s (NOT individual images) to Train (70%), Val (15%), or Test (15%). This ensures a plant from an burst-photo sequence cannot have one frame in Train and another in Test.
7.  **Augmentation Isolation:** Save the raw datasets to disk. Data augmentation (rotations, brightness, crops) happens **dynamically in memory** during the PyTorch `DataLoader` phase for the Training split only.

---

## 7. Dataset Manifest Format

A single `manifest.csv` will track the entire V3 dataset to ensure auditability.

| Column | Description |
| :--- | :--- |
| `image_id` | Unique UUID for the image within FieldMind. |
| `source` | Origin dataset (e.g., `plantvillage`, `openimages_tractor`). |
| `source_image_id` | Original filename from the source dataset. |
| `label` | Final assigned class (`PROCESSABLE_LEAF`, `NON_PROCESSABLE_IMAGE`). |
| `review_status` | Status (`AUTO`, `MANUAL_PASS`, `RESOLVED_AMBIGUOUS`). |
| `crop` | (Optional) Plant species if known (e.g., `cassava`). |
| `disease` | (Optional) Disease state if known (e.g., `healthy`, `mosaic_virus`). |
| `capture_environment` | `lab`, `field`, `synthetic`, or `unknown`. |
| `split` | `train`, `val`, or `test`. |
| `hash_sha256` | Exact cryptographic hash. |
| `hash_phash` | Perceptual hash string. |
| `group_id` | Cluster ID for near-duplicates/burst-photos (prevents leakage). |

---

## 8. Quality Control (QA) Procedure

1.  **Double Annotation Subsetting:** 10% of all images sourced from OpenImages or web scraping will be annotated by two independent reviewers.
2.  **Disagreement Resolution:** Any mismatch between Reviewer A and Reviewer B automatically flags the image as `AMBIGUOUS_REVIEW`.
3.  **Ambiguous Sample Review:** A senior ML engineer reviews all `AMBIGUOUS_REVIEW` items. If the engineer cannot confidently decide, the image is **discarded** to prevent injecting noise.
4.  **Class Balance Checks:** Post-split, verify Train/Val/Test maintain roughly a 50/50 balance of Positive vs Negative.
5.  **Source Distribution Checks:** Ensure no single source (e.g., PlantVillage) makes up $>40\%$ of the positive class.
6.  **Train/Test Leakage Checks:** Run a script verifying that no `group_id` or `hash_phash` exists simultaneously in `train` and `test` splits.
