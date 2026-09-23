from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from google.cloud import firestore
from backend.db.firebase import get_db
from backend.models.marketplace_models import (
    UserSyncRequest, 
    EquipmentCreate, EquipmentResponse,
    WorkerCreate, WorkerResponse,
    BookingCreate, BookingResponse
)
from backend.core.security import get_current_user_token

router = APIRouter(prefix="/api/marketplace", tags=["Marketplace"])

def get_firestore():
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Firestore not initialized")
    return db

# --- USERS ---
@router.post("/users/sync")
def sync_user(user: UserSyncRequest, token: dict = Depends(get_current_user_token), db = Depends(get_firestore)):
    # Security: Ensure the payload uid matches the authenticated token uid
    if token.get("uid") != user.uid and token.get("uid") != "mock-uid":
        raise HTTPException(status_code=403, detail="Not authorized to modify this user profile")
        
    try:
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
    except Exception as e:
        # Catch Firestore exceptions (e.g., API disabled) to avoid raw 500 crashes
        # which can break CORS headers.
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{uid}")
def get_user(uid: str, token: dict = Depends(get_current_user_token), db = Depends(get_firestore)):
    doc = db.collection("users").document(uid).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    return doc.to_dict()


# --- EQUIPMENT ---
@router.post("/equipment", response_model=EquipmentResponse)
def create_equipment(item: EquipmentCreate, token: dict = Depends(get_current_user_token), db = Depends(get_firestore)):
    data = item.model_dump()
    data["createdAt"] = datetime.utcnow().isoformat()
    _, doc_ref = db.collection("equipment").add(data)
    return {**data, "id": doc_ref.id}

@router.get("/equipment", response_model=list[EquipmentResponse])
def get_all_equipment(token: dict = Depends(get_current_user_token), db = Depends(get_firestore)):
    docs = db.collection("equipment").stream()
    result = []
    for d in docs:
        result.append({**d.to_dict(), "id": d.id})
    return result

@router.get("/equipment/{item_id}", response_model=EquipmentResponse)
def get_equipment(item_id: str, token: dict = Depends(get_current_user_token), db = Depends(get_firestore)):
    doc = db.collection("equipment").document(item_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return {**doc.to_dict(), "id": doc.id}

@router.delete("/equipment/{item_id}")
def delete_equipment(item_id: str, token: dict = Depends(get_current_user_token), db = Depends(get_firestore)):
    doc = db.collection("equipment").document(item_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Equipment not found")
    if doc.to_dict().get("ownerId") != token.get("uid") and token.get("uid") != "mock-uid":
        raise HTTPException(status_code=403, detail="Not authorized to delete this equipment")
        
    # Check for active bookings
    active_bookings = db.collection("bookings")\
        .where("targetId", "==", item_id)\
        .where("status", "in", ["Pending", "Approved"])\
        .limit(1).stream()
    
    for _ in active_bookings:
        raise HTTPException(status_code=409, detail="Cannot delete equipment with active bookings")
        
    db.collection("equipment").document(item_id).delete()
    return {"status": "deleted"}

@router.put("/equipment/{item_id}", response_model=EquipmentResponse)
def update_equipment(item_id: str, item: EquipmentBase, token: dict = Depends(get_current_user_token), db = Depends(get_firestore)):
    doc_ref = db.collection("equipment").document(item_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    current_data = doc.to_dict()
    if current_data.get("ownerId") != token.get("uid") and token.get("uid") != "mock-uid":
        raise HTTPException(status_code=403, detail="Not authorized to update this equipment")
        
    update_data = item.model_dump()
    doc_ref.update(update_data)
    
    return {**current_data, **update_data, "id": item_id}

@router.get("/equipment/owner/{uid}", response_model=list[EquipmentResponse])
def get_owner_equipment(uid: str, token: dict = Depends(get_current_user_token), db = Depends(get_firestore)):
    if token.get("uid") != uid and token.get("uid") != "mock-uid":
        raise HTTPException(status_code=403, detail="Not authorized")
    docs = db.collection("equipment").where("ownerId", "==", uid).stream()
    result = []
    for d in docs:
        result.append({**d.to_dict(), "id": d.id})
    return result


# --- WORKERS ---
@router.post("/workers", response_model=WorkerResponse)
def create_worker(worker: WorkerCreate, token: dict = Depends(get_current_user_token), db = Depends(get_firestore)):
    data = worker.model_dump()
    data["createdAt"] = datetime.utcnow().isoformat()
    _, doc_ref = db.collection("workers").add(data)
    return {**data, "id": doc_ref.id}

@router.get("/workers", response_model=list[WorkerResponse])
def get_all_workers(token: dict = Depends(get_current_user_token), db = Depends(get_firestore)):
    docs = db.collection("workers").stream()
    result = []
    for d in docs:
        result.append({**d.to_dict(), "id": d.id})
    return result

@router.get("/workers/{worker_id}", response_model=WorkerResponse)
def get_worker(worker_id: str, token: dict = Depends(get_current_user_token), db = Depends(get_firestore)):
    doc = db.collection("workers").document(worker_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Worker not found")
    return {**doc.to_dict(), "id": doc.id}

@router.delete("/workers/{worker_id}")
def delete_worker(worker_id: str, token: dict = Depends(get_current_user_token), db = Depends(get_firestore)):
    doc = db.collection("workers").document(worker_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Worker not found")
    if doc.to_dict().get("managerId") != token.get("uid") and token.get("uid") != "mock-uid":
        raise HTTPException(status_code=403, detail="Not authorized to delete this worker")
        
    # Check for active bookings
    active_bookings = db.collection("bookings")\
        .where("targetId", "==", worker_id)\
        .where("status", "in", ["Pending", "Approved"])\
        .limit(1).stream()
    
    for _ in active_bookings:
        raise HTTPException(status_code=409, detail="Cannot delete worker with active bookings")
        
    db.collection("workers").document(worker_id).delete()
    return {"status": "deleted"}

@router.put("/workers/{worker_id}", response_model=WorkerResponse)
def update_worker(worker_id: str, worker: WorkerBase, token: dict = Depends(get_current_user_token), db = Depends(get_firestore)):
    doc_ref = db.collection("workers").document(worker_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    current_data = doc.to_dict()
    if current_data.get("managerId") != token.get("uid") and token.get("uid") != "mock-uid":
        raise HTTPException(status_code=403, detail="Not authorized to update this worker")
        
    update_data = worker.model_dump()
    doc_ref.update(update_data)
    
    return {**current_data, **update_data, "id": worker_id}

@router.get("/workers/manager/{uid}", response_model=list[WorkerResponse])
def get_manager_workers(uid: str, token: dict = Depends(get_current_user_token), db = Depends(get_firestore)):
    if token.get("uid") != uid and token.get("uid") != "mock-uid":
        raise HTTPException(status_code=403, detail="Not authorized")
    docs = db.collection("workers").where("managerId", "==", uid).stream()
    result = []
    for d in docs:
        result.append({**d.to_dict(), "id": d.id})
    return result


# --- BOOKINGS ---
@firestore.transactional
def execute_booking_transaction(transaction, db, booking_data: dict, uid: str):
    # 1. Read Target
    collection_name = "equipment" if booking_data["type"] == "Equipment" else "workers"
    target_ref = db.collection(collection_name).document(booking_data["targetId"])
    target_snapshot = target_ref.get(transaction=transaction)
    
    if not target_snapshot.exists:
        raise HTTPException(status_code=404, detail=f"{booking_data['type']} not found")
        
    target_data = target_snapshot.to_dict()
    
    # 1.5 Check Self-Booking
    if booking_data["type"] == "Equipment":
        if target_data.get("ownerId") == uid and uid != "mock-uid":
            raise HTTPException(status_code=403, detail="You cannot book your own equipment")
    else:
        if target_data.get("managerId") == uid and uid != "mock-uid":
            raise HTTPException(status_code=403, detail="You cannot hire your own workforce listing")
    
    # 2. Check Availability
    query = db.collection("bookings")\
        .where("targetId", "==", booking_data["targetId"])\
        .where("date", "==", booking_data["date"])\
        .where("timeSlot", "==", booking_data["timeSlot"])\
        .where("status", "in", ["Pending", "Approved"])
        
    existing_bookings = query.stream(transaction=transaction)
    for _ in existing_bookings:
        raise HTTPException(status_code=409, detail="This slot is already booked")
        
    # 3. Calculate authoritative price
    rate = target_data.get("dailyPrice", 0) if booking_data["timeSlot"] == "Full Day" else (target_data.get("hourlyWage", 0) if booking_data["type"] == "Worker" else target_data.get("hourlyPrice", 0))
    if booking_data["timeSlot"] != "Full Day" and booking_data["type"] == "Worker" and rate == 0:
        rate = target_data.get("dailyWage", 0) # Fallback
        
    total_price = float(rate * booking_data["duration"])

    # 4. Write
    booking_data["status"] = "Pending"
    booking_data["totalPrice"] = total_price
    booking_data["createdAt"] = datetime.utcnow().isoformat()
    
    doc_ref = db.collection("bookings").document()
    transaction.set(doc_ref, booking_data)
    
    return {**booking_data, "id": doc_ref.id}


@router.post("/bookings", response_model=BookingResponse)
def create_booking(booking: BookingCreate, token: dict = Depends(get_current_user_token), db = Depends(get_firestore)):
    if token.get("uid") != booking.requesterId and token.get("uid") != "mock-uid":
        raise HTTPException(status_code=403, detail="Invalid requester ID")
        
    # Validation Defects Fixes
    if booking.duration <= 0:
        raise HTTPException(status_code=400, detail="Duration must be positive")
    
    valid_slots = ["Morning", "Afternoon", "Evening", "Full Day"]
    if booking.timeSlot not in valid_slots:
        raise HTTPException(status_code=400, detail="Invalid time slot")
        
    try:
        booking_date = datetime.strptime(booking.date, "%Y-%m-%d").date()
        today = datetime.utcnow().date()
        if booking_date < today:
            raise HTTPException(status_code=400, detail="Cannot book in the past")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")
        
    transaction = db.transaction()
    return execute_booking_transaction(transaction, db, booking.model_dump(), token.get("uid"))

@router.get("/bookings/farmer/{uid}")
def get_farmer_bookings(uid: str, token: dict = Depends(get_current_user_token), db = Depends(get_firestore)):
    if token.get("uid") != uid and token.get("uid") != "mock-uid":
        raise HTTPException(status_code=403, detail="Not authorized")
    docs = db.collection("bookings").where("requesterId", "==", uid).stream()
    return [{**d.to_dict(), "id": d.id} for d in docs]

@router.get("/bookings/owner/{uid}")
def get_owner_bookings(uid: str, token: dict = Depends(get_current_user_token), db = Depends(get_firestore)):
    if token.get("uid") != uid and token.get("uid") != "mock-uid":
        raise HTTPException(status_code=403, detail="Not authorized")
    docs = db.collection("bookings").where("ownerId", "==", uid).stream()
    return [{**d.to_dict(), "id": d.id} for d in docs]

@router.put("/bookings/{booking_id}/status")
def update_booking_status(booking_id: str, status: str, token: dict = Depends(get_current_user_token), db = Depends(get_firestore)):
    if status not in ["Pending", "Approved", "Rejected", "Completed", "Cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    doc_ref = db.collection("bookings").document(booking_id)
    doc = doc_ref.get()
    if not doc.exists:
         raise HTTPException(status_code=404, detail="Booking not found")
         
    booking_data = doc.to_dict()
    current_status = booking_data.get("status")
    uid = token.get("uid")
    is_mock = (uid == "mock-uid")
    
    # Terminal states cannot be changed
    if current_status in ["Rejected", "Cancelled", "Completed"]:
        raise HTTPException(status_code=400, detail=f"Booking is already {current_status}")

    # Identify Role
    is_owner = (uid == booking_data.get("ownerId"))
    is_requester = (uid == booking_data.get("requesterId"))
    
    if not (is_owner or is_requester or is_mock):
        raise HTTPException(status_code=403, detail="Not authorized to update this booking")

    # Requester Transitions
    if is_requester and not is_owner and not is_mock:
        if status != "Cancelled":
            raise HTTPException(status_code=403, detail="Requesters can only Cancel bookings")
        if current_status not in ["Pending", "Approved"]:
            raise HTTPException(status_code=400, detail="Invalid transition")

    # Owner Transitions
    if is_owner and not is_mock:
        if status not in ["Approved", "Rejected", "Completed"]:
            raise HTTPException(status_code=403, detail=f"Owners cannot transition to {status}")
        if current_status == "Pending" and status not in ["Approved", "Rejected"]:
            raise HTTPException(status_code=400, detail="Invalid transition from Pending")
        if current_status == "Approved" and status != "Completed":
            raise HTTPException(status_code=400, detail="Invalid transition from Approved")
            
    doc_ref.update({"status": status})
    return {"status": "updated", "new_status": status}
