# FieldMind - Project Scan Report

## Overview
**FieldMind** is an intelligent agricultural web application that helps farmers with crop disease detection, crop recommendation, and a built-in marketplace for renting equipment and hiring workers.

---

## Available Features

### 1. Crop Disease Detection
- **Image Verification**: Validates whether the uploaded image is actually a plant leaf before processing.
- **Disease Classification**: Identifies the exact crop disease from the leaf using a pre-trained ONNX classification model.
- **Severity Analysis (YOLO)**: If disease confidence is high (>60%), it uses a YOLO object detection model to draw bounding boxes around the affected (pest/disease) areas on the leaf.
- **Treatment Recommendation**: Provides actionable advice on how to handle the detected disease.

### 2. Crop Recommendation
- **Data-Driven Suggestions**: Suggests the top 3 best-suited crops based on soil nutrients (Nitrogen, Phosphorus, Potassium), pH levels, and weather data (temperature, humidity, rainfall).
- **Automated Parameter Estimation**: Ability to automatically estimate NPK values and fetch weather/soil details using the user's geographic coordinates (Latitude/Longitude).
- **Detailed Crop Metadata**: For each recommended crop, it provides planting seasons, water requirements, difficulty levels, and reasoning behind the recommendation.

### 3. Agricultural Marketplace
- **Equipment Sharing**: Farmers can list agricultural equipment for rent or find machinery to hire.
- **Worker Hiring**: Farm laborers can list their availability, and farm owners can hire them for agricultural tasks.
- **Booking Management**: Complete lifecycle for bookings (Pending -> Approved/Rejected -> Completed) linking Requesters (Farmers) and Owners.

---

## System Workflows

### Disease Diagnosis Workflow
1. User uploads a plant leaf image (JPG/PNG).
2. Backend passes the image to the **Leaf Verifier**. Non-leaf images are immediately rejected to save compute.
3. The image goes to the **Disease Classifier** to identify the disease type and confidence score.
4. If confidence > 60%, the image is passed to the **YOLO severity model** to extract bounding boxes of the infected areas.
5. The system returns the predicted disease, severity bounding boxes, and recommended next steps to the user.

### Crop Recommendation Workflow
1. User either manually enters soil (N, P, K, pH) and weather parameters OR provides their location (Lat/Lon) to auto-fill data using external APIs.
2. The parameters are fed into the Scikit-Learn `crop_model.pkl`.
3. The model predicts probabilities and returns the top 3 recommended crops.
4. The system enriches the response with static metadata (water range, season) and dynamically generated reasons for the recommendation.

### Marketplace Workflow
1. User authenticates via Firebase Auth, and their profile is synced to the Firestore `users` collection.
2. A user lists a piece of equipment or registers as a worker.
3. Another user finds the equipment/worker and initiates a **Booking**.
4. The owner receives the booking request and updates the status (`Approved` or `Rejected`).
5. Once the job/rental is done, the status is marked as `Completed`.

---

## Tech Stack

### Frontend Architecture
- **Framework**: React 19 powered by Vite.
- **Styling**: Tailwind CSS v4.
- **Animations**: Framer Motion.
- **Routing & State**: React Router DOM, React Hook Form.
- **Icons**: Lucide React.
- **API Client**: Axios.
- **Auth/Backend-as-a-Service**: Firebase SDK.

### Backend Architecture
- **Framework**: FastAPI (Python) running on Uvicorn.
- **Database**: Firebase Firestore (via `firebase-admin`).
- **File Parsing**: `python-multipart` for handling image uploads.
- **CORS Handling**: Native FastAPI CORS Middleware enabled for frontend communication.

### Machine Learning & AI
- **Inference Engine**: ONNX Runtime (`onnxruntime` executing on CPU).
- **Traditional ML**: Scikit-Learn & Joblib (for crop recommendation).
- **Image Processing**: Pillow (PIL) and Numpy.
- **Models**:
  - `leaf_verifier.onnx` (Leaf validation)
  - `fieldmind_best.onnx` / `fieldmind_pest.onnx` (Disease classifier)
  - `fieldmind_yolo_best.onnx` (Pest/Severity bounding boxes)
  - `crop_model.pkl` (Tabular ML crop predictor)

---

*Report generated automatically by FieldMind Assistant.*
