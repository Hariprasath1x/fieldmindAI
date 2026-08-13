import os
import logging
import uuid
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
                    logger.warning("No credentials found. Firestore will not be available. Using Mock DB.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin: {e}")

init_firebase()


# --- MOCK FIRESTORE IMPLEMENTATION ---
class MockDocumentSnapshot:
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return self._data or {}

class MockDocumentReference:
    def __init__(self, collection, doc_id):
        self.collection = collection
        self.id = doc_id

    def get(self):
        return MockDocumentSnapshot(self.id, self.collection._data.get(self.id))

    def set(self, data):
        self.collection._data[self.id] = data

    def update(self, data):
        if self.id in self.collection._data:
            self.collection._data[self.id].update(data)

    def delete(self):
        if self.id in self.collection._data:
            del self.collection._data[self.id]

class MockCollection:
    def __init__(self, name):
        self.name = name
        self._data = {}

    def document(self, doc_id):
        return MockDocumentReference(self, doc_id)

    def add(self, data):
        new_id = str(uuid.uuid4())
        self._data[new_id] = data
        return None, MockDocumentReference(self, new_id)

    def stream(self):
        return [MockDocumentSnapshot(k, v) for k, v in self._data.items()]

    def where(self, field, op, value):
        class MockQuery:
            def __init__(self, data, field, op, value):
                self._data = data
                self.field = field
                self.op = op
                self.value = value

            def stream(self):
                result = []
                for k, v in self._data.items():
                    if self.op == "==" and v.get(self.field) == self.value:
                        result.append(MockDocumentSnapshot(k, v))
                return result
        return MockQuery(self._data, field, op, value)

class MockFirestore:
    def __init__(self):
        self.collections = {}

    def collection(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name)
        return self.collections[name]

mock_db = MockFirestore()
# ------------------------------------

def get_db():
    try:
        if not firebase_admin._apps:
            return mock_db
        return firestore.client()
    except Exception as e:
        logger.error(f"Firestore client not available: {e}. Using Mock DB.")
        return mock_db
