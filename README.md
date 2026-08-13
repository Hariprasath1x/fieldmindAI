# FieldMind

An intelligent agricultural platform with machine learning inference for disease detection, crop recommendation, and an integrated marketplace.

## Architecture

* **Frontend**: React + Vite + Tailwind CSS
* **Backend**: FastAPI + Python 3.10
* **Machine Learning**: ONNX Runtime + Scikit-learn
* **Database & Auth**: Firebase / Firestore (with Local Mock fallback)
* **Background Processing**: Redis + RQ (with thread-pool sync fallback)

## Running the Application

### 1. Backend

Install requirements:
```bash
pip install -r requirements.txt
```

Run the backend server (FastAPI):
```bash
uvicorn backend.main:app --reload
```

Run the inference background worker (optional, requires Redis):
```bash
python -m backend.worker.inference_worker
```

### 2. Frontend

Install dependencies:
```bash
cd frontend
npm install
```

Start the development server:
```bash
npm run dev
```

## Features

1. **Disease Detection (Asynchronous Pipeline)**
   - Image Validation (blur, size, corruption checks)
   - Leaf Verification
   - Disease Classification
   - Severity & Bounding Box Localization

2. **Marketplace**
   - Equipment Rental Booking Lifecycle
   - Farm Workforce Directory

3. **Observability & Health**
   - Offline ML Evaluation Dashboard
   - Real-time User Feedback Tracking
   - Health and Readiness Probes (`/health`, `/ready`)

## Testing

Run the full test suite (API, ML pipelines, Integration, Unit):
```bash
pytest tests/ -v
```

## Docker

Build and run with docker-compose:
```bash
docker-compose up --build
```
This will start the FastAPI backend, the RQ background worker, and a Redis instance.
