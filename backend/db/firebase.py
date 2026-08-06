import os
import logging
import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger("fieldmind.firebase")

def init_firebase():
    if not firebase_admin._apps:
        try:
            # Path to the service account key (user needs to provide this)
            cred_path = os.path.join(os.path.dirname(__file__), "..", "firebase_service_account.json")
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin initialized with service account.")
            else:
                logger.warning("firebase_service_account.json not found.")
                if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                    firebase_admin.initialize_app()
                else:
                    logger.warning("No credentials found. Firestore will not be available.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin: {e}")

init_firebase()

def get_db():
    try:
        return firestore.client()
    except Exception as e:
        logger.error(f"Firestore client not available: {e}")
        return None
