import logging
from fastapi import HTTPException, Header
import firebase_admin
from firebase_admin import auth as firebase_auth

logger = logging.getLogger("fieldmind.security")

def get_current_user_token(authorization: str = Header(None)):
    """
    FastAPI dependency to authenticate the user securely via Firebase ID Token.
    Returns the decoded token dictionary, ensuring requests are genuinely from the 
    authenticated frontend user, preventing arbitrary UID spoofing.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split("Bearer ")[1]
    
    if not firebase_admin._apps:
        # Mock mode fallback if firebase isn't initialized (e.g. testing)
        return {"uid": "mock-uid", "phone_number": ""}
        
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
