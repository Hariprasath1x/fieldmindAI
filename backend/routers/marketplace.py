from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from backend.db.firebase import get_db
from backend.models.marketplace_models import (
    UserSyncRequest, 
    EquipmentCreate, EquipmentResponse,
    WorkerCreate, WorkerResponse,
    BookingCreate, BookingResponse
)

router = APIRouter(prefix="/api/marketplace", tags=["Marketplace"])

def get_firestore():
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Firestore not initialized")
    return db

# --- USERS ---
@router.post("/users/sync")
def sync_user(user: UserSyncRequest, db = Depends(get_firestore)):
    doc_ref = db.collection("users").document(user.uid)
    doc = doc_ref.get()
    
    if not doc.exists:
        # Create new
        data = user.model_dump()
        data["createdAt"] = datetime.utcnow().isoformat()
        doc_ref.set(data)
        return {"status": "created", "data": data}
    else:
        # Update existing fields if provided
        update_data = {k: v for k, v in user.model_dump().items() if v is not None}
        if update_data:
            doc_ref.update(update_data)
        return {"status": "updated"}

@router.get("/users/{uid}")
def get_user(uid: str, db = Depends(get_firestore)):
    doc = db.collection("users").document(uid).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    return doc.to_dict()


# --- EQUIPMENT ---
@router.post("/equipment", response_model=EquipmentResponse)
def create_equipment(item: EquipmentCreate, db = Depends(get_firestore)):
    data = item.model_dump()
    data["createdAt"] = datetime.utcnow().isoformat()
    _, doc_ref = db.collection("equipment").add(data)
    return {**data, "id": doc_ref.id}

@router.get("/equipment", response_model=list[EquipmentResponse])
def get_all_equipment(db = Depends(get_firestore)):
    docs = db.collection("equipment").stream()
    result = []
    for d in docs:
        result.append({**d.to_dict(), "id": d.id})
    return result

@router.delete("/equipment/{item_id}")
def delete_equipment(item_id: str, db = Depends(get_firestore)):
    db.collection("equipment").document(item_id).delete()
    return {"status": "deleted"}


# --- WORKERS ---
@router.post("/workers", response_model=WorkerResponse)
def create_worker(worker: WorkerCreate, db = Depends(get_firestore)):
    data = worker.model_dump()
    data["createdAt"] = datetime.utcnow().isoformat()
    _, doc_ref = db.collection("workers").add(data)
    return {**data, "id": doc_ref.id}

@router.get("/workers", response_model=list[WorkerResponse])
def get_all_workers(db = Depends(get_firestore)):
    docs = db.collection("workers").stream()
    result = []
    for d in docs:
        result.append({**d.to_dict(), "id": d.id})
    return result

@router.delete("/workers/{worker_id}")
def delete_worker(worker_id: str, db = Depends(get_firestore)):
    db.collection("workers").document(worker_id).delete()
    return {"status": "deleted"}


# --- BOOKINGS ---
@router.post("/bookings", response_model=BookingResponse)
def create_booking(booking: BookingCreate, db = Depends(get_firestore)):
    data = booking.model_dump()
    data["status"] = "Pending"
    data["createdAt"] = datetime.utcnow().isoformat()
    _, doc_ref = db.collection("bookings").add(data)
    return {**data, "id": doc_ref.id}

@router.get("/bookings/farmer/{uid}")
def get_farmer_bookings(uid: str, db = Depends(get_firestore)):
    docs = db.collection("bookings").where("requesterId", "==", uid).stream()
    return [{**d.to_dict(), "id": d.id} for d in docs]

@router.get("/bookings/owner/{uid}")
def get_owner_bookings(uid: str, db = Depends(get_firestore)):
    docs = db.collection("bookings").where("ownerId", "==", uid).stream()
    return [{**d.to_dict(), "id": d.id} for d in docs]

@router.put("/bookings/{booking_id}/status")
def update_booking_status(booking_id: str, status: str, db = Depends(get_firestore)):
    if status not in ["Pending", "Approved", "Rejected", "Completed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    doc_ref = db.collection("bookings").document(booking_id)
    if not doc_ref.get().exists:
         raise HTTPException(status_code=404, detail="Booking not found")
         
    doc_ref.update({"status": status})
    return {"status": "updated", "new_status": status}
