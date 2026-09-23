from pydantic import BaseModel, Field
from typing import Optional, List

class UserSyncRequest(BaseModel):
    uid: str
    displayName: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    role: str = "Farmer" # Farmer, Owner, Manager
    language: str = "en"

class EquipmentBase(BaseModel):
    name: str
    category: str
    hourlyPrice: float = Field(ge=0.0)
    dailyPrice: float = Field(ge=0.0)
    location: str
    village: str
    quantity: int = Field(ge=1)
    isAvailable: bool = True
    description: Optional[str] = None
    image: Optional[str] = None

class EquipmentCreate(EquipmentBase):
    ownerId: str
    ownerName: str
    ownerPhone: str

class EquipmentResponse(EquipmentBase):
    id: str
    ownerId: str
    ownerName: str
    ownerPhone: str
    createdAt: str

class WorkerBase(BaseModel):
    name: str
    phone: str
    village: str
    experience: str
    skills: List[str]
    dailyWage: float = Field(ge=0.0)
    hourlyWage: float = Field(ge=0.0)
    availableDays: List[str]
    availableTime: str
    description: Optional[str] = None
    languages: List[str]
    status: str = "Available" # Available, Busy, Offline
    photo: Optional[str] = None

class WorkerCreate(WorkerBase):
    managerId: str

class WorkerResponse(WorkerBase):
    id: str
    managerId: str
    createdAt: str

class BookingCreate(BaseModel):
    type: str # Equipment, Worker
    targetId: str
    targetName: str
    requesterId: str
    ownerId: str
    date: str
    timeSlot: str
    duration: int # e.g. number of days or hours, based on timeSlot

class BookingResponse(BookingCreate):
    id: str
    status: str # Pending, Approved, Rejected, Completed
    totalPrice: float
    createdAt: str
