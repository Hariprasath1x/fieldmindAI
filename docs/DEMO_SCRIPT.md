# FieldMind: Live Demo Script (5-10 Minutes)

*Before the demo, ensure the backend (`./start.sh`) and frontend are running. Have the `tests/ml/test_images/` folder open and easily accessible.*

## 1. Introduction (0:00 - 1:00)
**Action:** Open the FieldMind homepage.
**Say:** "Welcome to FieldMind, an intelligent agricultural platform. Our goal is to consolidate crop disease detection, crop recommendation, and a resource-sharing marketplace into a single, seamless web application. Let's start by logging in."
**Action:** Log in with an existing demo account (or create one).
**Point Out:** "We use Firebase for secure authentication. Our session is now active, and a JWT token is being passed to our FastAPI backend for secure requests."

## 2. Crop Recommendation (1:00 - 2:30)
**Action:** Navigate to the **Crop Recommendation** tab.
**Say:** "First, let's look at crop recommendation. Instead of relying on guesswork, farmers can input their soil's Nitrogen, Phosphorus, Potassium, and pH levels. For weather, they can manually enter data or use geolocation to auto-fill."
**Action:** Enter sample NPK data (e.g., N: 90, P: 42, K: 43, pH: 6.5, Temp: 20, Humidity: 82, Rain: 200). Click **Predict**.
**Point Out:** "Our Scikit-Learn model running on the backend predicts the top 3 best-suited crops. Notice how the UI also explains *why* the crop was recommended based on its water and season requirements."

## 3. Disease Detection - Success Flow (2:30 - 4:30)
**Action:** Navigate to the **Disease Detection** tab.
**Say:** "Now, let's test the core ML feature. I will upload a clear image of a diseased plant leaf."
**Action:** Upload `tests/ml/test_images/A_clear_leaf.jpg`. Wait for the result.
**Say:** "The request was sent asynchronously to our backend. The ONNX model successfully classified the disease."
**Point Out:** "Notice the result: It identified Cassava Brown Spot. If confidence is high enough, our secondary YOLO model draws bounding boxes around the affected severity areas. The system also provides immediate treatment recommendations."

## 4. The Fail-Fast Architecture - Rejection Flow (4:30 - 6:30)
**Action:** Stay on the Disease Detection tab.
**Say:** "A major problem with ML apps is they try to predict diseases on images that aren't even plants. We built a 'Fail-Fast' architecture to prevent this."
**Action:** Upload `tests/ml/test_images/D_non_leaf_object.jpg`.
**Point Out:** "The pipeline instantly rejected it. Our `LeafVerifier` model detected with high confidence that this is not a leaf. It aborted the pipeline, saving backend compute and preventing a misleading disease prediction."
**Action:** Upload `tests/ml/test_images/G_blurry_leaf.jpg` (or `I_partial_leaf.jpg`).
**Say:** "Similarly, if we upload a very blurry image..."
**Point Out:** "An initial OpenCV blur-detection algorithm catches it before it even reaches the ML models. This guarantees only high-quality data is processed."

## 5. Marketplace & Dashboard (6:30 - 8:30)
**Action:** Navigate to the **Marketplace** tab.
**Say:** "FieldMind also features a peer-to-peer marketplace. Farmers can list tractors or tools they aren't using, and local workers can list their availability."
**Action:** Click on an equipment listing and show the "Request Booking" flow.
**Say:** "Users can request a booking. The owner receives the request and can Approve or Reject it, creating a complete transactional lifecycle backed by Firestore."
**Action:** Navigate to the **Dashboard**.
**Point Out:** "Finally, the Dashboard provides a unified view. The user can see their past disease diagnosis history and the status of their active marketplace bookings all in one place."

## 6. Conclusion & Limitations (8:30 - 10:00)
**Say:** "In conclusion, FieldMind integrates robust ML workflows with modern web architecture. 
As for limitations, our disease classifier is currently a proof-of-concept. We noted in our documentation that we require a much larger, verified ground-truth dataset before we can claim specific accuracy percentages. However, we did successfully complete an ML lifecycle experiment (our LeafVerifier V3) to prove we can engineer datasets and train better models locally when data is available. 
Thank you!"

---
*Emergency Handling: If the ML prediction outputs something unexpected (e.g., mislabels the leaf), say: "Because this model acts as a proof-of-concept and lacks a fully localized training dataset, edge-case misclassifications can occur. This highlights exactly why we designed the architecture to be modular, so models can be swapped seamlessly as better datasets become available."*
