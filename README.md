# FieldMind 🌾

**AI-Powered Agricultural Assistance Platform**

FieldMind is a full-stack web application that integrates Deep Learning, Computer Vision, and modern web technologies to provide crop disease detection, intelligent crop recommendations, and a peer-to-peer agricultural marketplace.

Built as a B.Tech Computer Science final-year project demonstrating:
- End-to-end AI/ML integration in a production-style web application
- PyTorch model training → ONNX export → FastAPI inference deployment
- React + FastAPI full-stack development
- Firebase authentication and Firestore database

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg?logo=react)](https://react.dev/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C.svg?logo=pytorch)](https://pytorch.org/)
[![ONNX](https://img.shields.io/badge/ONNX-Runtime-005CED.svg)](https://onnxruntime.ai/)
[![Firebase](https://img.shields.io/badge/Firebase-Auth%20%7C%20Firestore-FFCA28.svg?logo=firebase)](https://firebase.google.com/)

---

## Table of Contents
- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [ML Pipeline](#ml-pipeline)
- [Technology Stack](#technology-stack)
- [Setup & Running Locally](#setup--running-locally)
- [Example Workflow](#example-workflow)
- [Known Limitations](#known-limitations)

---

## Project Overview

FieldMind solves two real challenges for smallholder farmers:

1. **Disease Diagnosis**: A computer vision pipeline that accepts a leaf photograph and returns a disease classification, severity localisation (bounding boxes via YOLO), and a treatment recommendation — all within ~1 second.

2. **Resource Management**: A transactional peer-to-peer marketplace for renting farming equipment and hiring agricultural workers, with booking lifecycle management and Firestore ACID transaction guarantees.

---

## Key Features

### AI / Agriculture
- **Crop Disease Detection** — Upload a leaf photo → disease classification + severity heatmap + treatment recommendation
- **Leaf Verification** — Pre-processing ONNX gate that rejects obvious non-leaf images before running expensive inference
- **Crop Recommendation** — Soil N-P-K, pH, temperature, humidity, and rainfall → ranked seasonal crop suggestions
- **Diagnosis History** — Per-user history of all past diagnoses with progression tracking
- **Location-Aware Recommendations** — Auto-fill soil and weather parameters from user's GPS location

### Marketplace
- **Equipment Rental** — Browse, list, and book farm machinery (tractors, harvesters, etc.)
- **Farm Workforce** — Directory and booking for skilled agricultural labourers
- **Full Booking Lifecycle** — Pending → Approved/Rejected → Completed/Cancelled with owner-gated transitions
- **Conflict Detection** — Transactional double-booking prevention

### Platform
- **Firebase Authentication** — Google Sign-In and Email/Password
- **ML Dashboard** — Offline model evaluation metrics and real-time user feedback tracking
- **Async Inference** — Redis + RQ worker queue for non-blocking ML inference (graceful sync fallback)
- **Multilingual Support** — i18n infrastructure (English / தமிழ் scaffold)

---

## Architecture

```
React Frontend (Vite + Tailwind)
        │
        │  REST API + Firebase Bearer Token
        ▼
FastAPI Backend (Python)
        │
        ├── Marketplace Endpoints   ──▶  Firestore (ACID Transactions)
        │
        └── Inference Endpoint
                │
                ├── [Sync]  run_inference_job() directly
                └── [Async] Redis Queue → RQ Worker
                                │
                                ▼
                    ┌─────────────────────────┐
                    │     ML Pipeline          │
                    │  1. Image Validation     │
                    │  2. Leaf Verification    │  ← ONNX MobileNetV3
                    │  3. Disease Classify     │  ← ONNX EfficientNet
                    │  4. Severity Detection   │  ← YOLOv8 ONNX
                    │  5. Recommendation       │  ← Rule-based
                    │  6. Persist to Firestore │
                    └─────────────────────────┘
```

---

## ML Pipeline

The disease detection pipeline consists of six sequential stages:

| Stage | Component | Model | Output |
|-------|-----------|-------|--------|
| 1 | Image Validation | OpenCV Laplacian | Pass / Reject (blur, size) |
| 2 | Leaf Verification | MobileNetV3-Small (ONNX) | leaf / non\_leaf |
| 3 | Disease Classification | EfficientNet (ONNX) | disease label + confidence |
| 4 | Severity Detection | YOLOv8 (ONNX) | bounding boxes + labels |
| 5 | Area Estimation | Geometric (bbox union) | affected area % |
| 6 | Recommendation | Rule-based | treatment text |

**Training:** Models were trained in PyTorch on PlantVillage and domain-augmented datasets, then exported to ONNX for lightweight, framework-agnostic inference via ONNX Runtime.

**Supported classes (examples):** `cashew_anthracnose`, `cassava_brown_spot`, `tomato_septoria_leaf_spot`, `maize_streak_virus`, and 20+ others.

---

## Technology Stack

### Frontend
| Tool | Purpose |
|------|---------|
| React 19 + Vite | SPA framework and dev server |
| Tailwind CSS | Utility-first styling |
| Framer Motion | Animations |
| React Hook Form | Form state management |
| Axios | HTTP client with auth interceptors |

### Backend
| Tool | Purpose |
|------|---------|
| FastAPI | ASGI API framework |
| Pydantic | Request/response validation |
| ONNX Runtime | Cross-platform ML inference |
| OpenCV + Pillow | Image processing |
| Joblib + Scikit-learn | Crop recommendation model |
| Redis + RQ | Async ML job queue |

### ML / AI
| Tool | Purpose |
|------|---------|
| PyTorch | Model training |
| ONNX | Model export and deployment |
| MobileNetV3-Small | Leaf verification |
| EfficientNet | Disease classification |
| YOLOv8 | Severity/region detection |
| RandomForest | Crop recommendation |

### Infrastructure
| Tool | Purpose |
|------|---------|
| Firebase Auth | User authentication |
| Google Firestore | NoSQL database |
| Firebase Admin SDK | Server-side Firestore access |
| Docker + Compose | Container orchestration |

---

## Setup & Running Locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- A Firebase project with **Authentication** and **Firestore** enabled
- A Firebase Admin SDK service account JSON

### 1. Clone & Setup Backend

```bash
git clone https://github.com/your-username/fieldmind.git
cd fieldmind

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Place Firebase Admin SDK key
cp /path/to/firebase_service_account.json ./firebase_service_account.json

# Start FastAPI backend
uvicorn backend.main:app --reload --port 8002
```

### 2. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure Firebase Web credentials
# Copy .env.example to .env and fill in your Firebase config:
cp ../.env.example .env
# Edit .env with your VITE_FIREBASE_* values

# Start Vite dev server
npm run dev
```

### 3. (Optional) Async Worker

For background ML processing:
```bash
# Requires Redis running locally
redis-server

# In a separate terminal:
rq worker inference
```

### 4. Docker Compose (Full Stack)

```bash
docker-compose up --build
```

This starts the FastAPI backend, Redis, and RQ worker together.

---

## Example Workflow

1. **Open** `http://localhost:5174` (or whichever Vite port)
2. **Sign in** with Google or Email/Password
3. **Navigate** to Disease Detection in the sidebar
4. **Upload** a clear photo of a plant leaf showing disease symptoms
5. **Click** "Start Analysis" — watch the pipeline timeline progress
6. **Review** the diagnosis card showing:
   - Possible disease with confidence score
   - Visual findings (detected symptom regions)
   - Treatment recommendation
   - AI disclaimer
7. **Provide feedback** (Correct / Incorrect) to help improve the model
8. **View history** in Diagnosis History

For crop recommendations:
1. Go to Crop Recommendation
2. Click "Use My Location" to auto-fill environmental data, or enter manually
3. Review ranked crop suggestions with seasonal suitability and reasons

---

## Known Limitations

- **Crop identity is uncertain.** The disease classifier outputs labels like `tomato_septoria_leaf_spot` — the crop prefix is part of the training label and may not correctly identify the actual crop in the uploaded photo.
- **Visual disease patterns, not agricultural ground truth.** The model detects visual symptoms that correlate with known diseases. Real-world confirmation by a qualified agronomist is always required.
- **Domain shift.** Models trained primarily on controlled/lab-style PlantVillage images may have lower accuracy on real-world smartphone field photographs with complex backgrounds.
- **20+ disease classes only.** The classifier cannot detect diseases outside its training classes. Unfamiliar inputs may return the nearest matching class with low confidence.
- **YOLO bounding boxes are approximations.** Affected area percentage is computed from bounding box geometry, which overestimates true affected leaf tissue area.
- **No real-time model updates.** The ML layer is frozen for this student project. Feedback data is collected but model retraining is not automated.

---

## Project Structure

```
fieldmind/
├── frontend/                  # React + Vite SPA
│   ├── src/
│   │   ├── components/        # Navbar, Sidebar, UploadBox, Timeline, forms
│   │   ├── hooks/             # useAuth, useLanguage
│   │   ├── pages/             # DiseaseDetection, Dashboard, Marketplace, etc.
│   │   └── services/          # Axios API clients + Firebase config
│   └── package.json
├── backend/                   # FastAPI application
│   ├── core/                  # Config, logging, security, request ID
│   ├── db/                    # Firebase Admin SDK init
│   ├── models/                # Pydantic schemas
│   │   ├── leaf_verifier.onnx
│   │   ├── fieldmind_pest.onnx
│   │   ├── fieldmind_yolo_best.onnx
│   │   └── crop_model.pkl
│   ├── routers/               # API endpoints
│   ├── services/              # ML inference, leaf verifier, image validation
│   ├── worker/                # Async inference worker (RQ)
│   └── main.py                # ASGI entrypoint
├── tests/                     # Integration tests
├── docker-compose.yml
├── requirements.txt
└── start.sh                   # Convenience startup script
```

---

*FieldMind — Demonstrating AI-powered precision agriculture through full-stack engineering.*
