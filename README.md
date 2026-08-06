# FieldMind

FieldMind is a simple crop disease detection and crop recommendation demo built with a FastAPI backend and a Streamlit frontend.

It uses your pre-trained model files directly. No training or fine-tuning is included in this project.

## Project Structure

```
fieldmind/
  backend/
    main.py
    services/
      leaf_verifier.py
  frontend/
    app.py
  models/
    class_names.json
    labels.json
    leaf_verifier.onnx
    leaf_verifier_config.json
    yolo_classes.json
    crop_model.pkl
    fieldmind_pest.onnx
    fieldmind_yolo_best.onnx
  requirements.txt
  start.cmd
  start.bat
  start.ps1
```

## Model Files

Place the model assets inside the root `models/` folder:

- `models/class_names.json` - ordered disease labels
- `models/yolo_classes.json` - YOLO label map
- `models/labels.json` - leaf verifier label map
- `models/leaf_verifier.onnx` - ONNX leaf verification model
- `models/leaf_verifier_config.json` - leaf verifier preprocessing and threshold config
- `models/crop_model.pkl` - scikit-learn crop recommendation model
- `models/fieldmind_pest.onnx` - ONNX disease classifier
- `models/fieldmind_yolo_best.onnx` - ONNX YOLO model for severity/pest detection

The backend also supports `models/fieldmind_best.onnx` if you rename or replace the classifier later.

## Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

## How To Run

### Option 1: One-click start on Windows

Double-click `start.bat`.

If you are already in PowerShell, run:

```powershell
.\start.cmd
```

If you prefer to call the script directly, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

This launches:

- FastAPI backend at `http://localhost:8000`
- Streamlit frontend at `http://localhost:8501`

### Option 2: Run manually

Start the backend:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Then start the frontend in a second terminal:

```bash
streamlit run frontend/app.py
```

## What The App Does

### Disease Detection

- Upload a JPG or PNG image of a plant leaf.
- The backend first runs the leaf verification ONNX model.
- Non-leaf uploads are rejected before disease detection or YOLO execution.
- Verified leaf images continue through the existing disease classifier and YOLO severity pipeline.
- If disease confidence is below 0.60, the result is marked as unknown.

### Crop Recommendation

- Enter soil and weather values for `N`, `P`, `K`, temperature, humidity, pH, and rainfall.
- The backend loads `crop_model.pkl` and returns the predicted crop.

## Notes

- The app reads labels from the JSON files in `models/`.
- The backend uses CPU inference through `onnxruntime`.
- No database, auth, Docker, or training pipeline is included.
