from __future__ import annotations

from io import BytesIO

import requests
import streamlit as st
from PIL import Image


BACKEND_URL = "http://localhost:8000"


st.set_page_config(page_title="FieldMind", layout="centered")
st.title("FieldMind")
st.write("Upload a leaf image for disease detection or enter crop soil data for a recommendation.")

tab_disease, tab_crop = st.tabs(["Disease Detection", "Crop Recommendation"])


with tab_disease:
    uploaded_file = st.file_uploader("Upload a plant leaf image", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(BytesIO(uploaded_file.getvalue()))
        st.image(image, caption="Uploaded image", use_container_width=True)

        if st.button("Analyze", key="analyze_disease"):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/predict/disease",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "image/jpeg")},
                    timeout=60,
                )
                response.raise_for_status()
                result = response.json()

                pipeline = result.get("pipeline", {})

                if not pipeline.get("allow_processing", True):
                    st.warning(result.get("message", "Upload a clearer plant leaf image."))
                elif result.get("status") == "unknown":
                    st.warning(result.get("message", "Upload a clearer plant leaf image."))
                else:
                    st.success(f"Predicted disease: {result.get('disease', 'Unknown')}")
                    confidence = float(result.get("confidence", 0.0))
                    st.write(f"Confidence: {confidence:.2%}")

                    detections = result.get("severity_detections", [])
                    if detections:
                        st.subheader("Severity / pest detections")
                        st.table(
                            [
                                {
                                    "label": detection.get("label", ""),
                                    "confidence": f"{float(detection.get('confidence', 0.0)):.2%}",
                                    "box": detection.get("box", []),
                                }
                                for detection in detections
                            ]
                        )
                    else:
                        st.info("No severity or pest boxes were returned for this image.")
            except requests.RequestException as exc:
                st.error(f"Backend request failed: {exc}")


with tab_crop:
    with st.form("crop_recommendation_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            nitrogen = st.number_input("N", value=90.0)
            potassium = st.number_input("K", value=42.0)
            humidity = st.number_input("Humidity", value=80.0)
        with col2:
            phosphorus = st.number_input("P", value=42.0)
            temperature = st.number_input("Temperature", value=25.0)
            rainfall = st.number_input("Rainfall", value=200.0)
        with col3:
            ph = st.number_input("pH", value=6.5)

        submitted = st.form_submit_button("Recommend")

    if submitted:
        payload = {
            "N": nitrogen,
            "P": phosphorus,
            "K": potassium,
            "temperature": temperature,
            "humidity": humidity,
            "pH": ph,
            "rainfall": rainfall,
        }

        try:
            response = requests.post(f"{BACKEND_URL}/predict/crop", json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            st.success(f"Recommended crop: {result.get('recommended_crop', 'Unknown')}")
        except requests.RequestException as exc:
            st.error(f"Backend request failed: {exc}")
