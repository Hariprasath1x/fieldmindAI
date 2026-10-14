# FieldMind: Intelligent Agricultural Platform
*B.Tech Project Presentation Content Outline*

## 1. Project Title
**FieldMind: An Intelligent Agricultural Web Application for Crop Disease Diagnosis, Recommendation, and Marketplace Integration**

## 2. Problem Statement
Farmers face significant challenges in accurately identifying crop diseases and determining the most suitable crops for their specific land conditions. Furthermore, there is a lack of localized platforms for farmers to efficiently rent agricultural equipment and hire farm labor, leading to resource inefficiencies.

## 3. Motivation
Agricultural productivity heavily relies on timely disease intervention and proper crop selection. Small-scale farmers often lack access to expert agronomists. By leveraging machine learning directly in a web platform, we can democratize access to agricultural intelligence and create a peer-to-peer ecosystem for resource sharing.

## 4. Existing Problem
- Existing ML agricultural tools often suffer from "garbage in, garbage out" (e.g., predicting a plant disease on a picture of a shoe).
- Tools are often fragmented (one app for disease, another for weather, no marketplace).
- Many platforms lack rigorous image validation, returning confident but incorrect predictions on blurry or irrelevant images.

## 5. Proposed Solution
FieldMind is a comprehensive, full-stack platform that combines:
1.  A robust, multi-stage Machine Learning pipeline for disease detection that actively rejects poor-quality or non-plant images to save compute and prevent misleading results.
2.  A data-driven crop recommendation engine based on soil and weather parameters.
3.  An integrated peer-to-peer agricultural marketplace for equipment rental and labor hiring.

## 6. Objectives
- Develop an asynchronous ML pipeline using ONNX Runtime.
- Implement a "Fail-Fast" architecture via blur detection and a dedicated Leaf Verification model.
- Provide crop recommendations based on NPK, pH, and weather data.
- Build a seamless web marketplace using React and Firebase.

## 7. System Architecture & Technology Stack
- **Frontend:** React 19 (Vite), Tailwind CSS v4, Framer Motion for UI/UX.
- **Backend:** FastAPI (Python), Uvicorn, asynchronous request handling.
- **Database & Auth:** Firebase Auth, Firestore (NoSQL database).
- **ML Engine:** ONNX Runtime (CPU), Scikit-Learn, Pillow/OpenCV for image processing.

## 8. ML Pipeline (The Core Innovation)
Our diagnosis pipeline uses a sequential, resource-efficient flow:
1.  **Image Validation:** Checks image format and uses `cv2.Laplacian` variance to reject blurry images instantly.
2.  **LeafVerifier (V2):** A lightweight ONNX classifier that determines if the image is actually a leaf. If not, the pipeline aborts ("Fail-Fast").
3.  **Disease Classifier:** An EfficientNet-based ONNX model that categorizes the disease across 22 supported crop/disease classes.
4.  **Confidence Categorization:** Logits are passed through a Softmax function. Results are categorized as HIGH (>= 0.75), MEDIUM (>= 0.45), or LOW (< 0.45), generating tailored user recommendations.
5.  **YOLO Severity:** If confidence is HIGH/MEDIUM, a YOLO object detection model draws bounding boxes around the affected areas.

## 9. Experimental Work (LeafVerifier V3)
During our project, we audited the production LeafVerifier (V2) and found it occasionally struggled with highly ambiguous images. To demonstrate the ML engineering lifecycle, we designed an experimental **LeafVerifier V3**. We collected a strict binary dataset (Leaf vs. Non-Leaf), drafted an annotation policy, and successfully trained a PyTorch EfficientNet-B0 model (achieving ~97.8% test accuracy on the local dataset). While V2 remains in production for stability, V3 proves our capability to iterate and improve the dataset engineering process.

## 10. Key Features
- **Disease Diagnosis:** With built-in safeguards against bad data.
- **Crop Recommendation:** Auto-fetches environmental data based on geolocation.
- **Agricultural Marketplace:** Peer-to-peer equipment and worker booking lifecycle (Pending -> Approved -> Completed).
- **User Dashboard:** Unified history of diagnoses and marketplace interactions.

## 11. Testing Results
- **Backend Reliability:** 99/99 automated pytest cases pass, confirming robust API endpoints and Firebase integration.
- **End-to-End ML Tests:** Verified that the pipeline successfully aborts on blurry or non-leaf images, protecting the disease classifier from bad data.

## 12. Limitations
- **Disease Classifier Baseline:** The disease classifier model is currently a proof-of-concept. We lack a large, verified ground-truth dataset for the 22 classes to calculate exact real-world accuracy, precision, and recall.
- **Forced Choice Model:** The disease classifier lacks an explicit "Unknown" class, relying entirely on the LeafVerifier and confidence thresholds to filter bad predictions.
- **YOLO Misalignment:** The YOLO severity boxes operate independently of the disease classifier, which can occasionally lead to mismatched labels.

## 13. Future Work
- Establish a rigorous evaluation dataset for the 22 disease classes to measure actual performance.
- Integrate the experimental LeafVerifier V3 into production.
- Train a unified model that predicts both the disease and the bounding boxes simultaneously to avoid label misalignment.

## 14. Conclusion
FieldMind successfully demonstrates the integration of complex ML workflows into a modern web application. By implementing fail-fast validations and a multi-model pipeline, we created a more resilient diagnostic tool, complemented by practical marketplace and recommendation features tailored for the agricultural sector.
