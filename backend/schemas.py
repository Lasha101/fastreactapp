# backend/schemas.py

from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any
from datetime import date, datetime

# --- NEW: Schemas for Asynchronous Task Handling ---

class AsyncTaskCreateResponse(BaseModel):
    """Response for a single task creation."""
    task_id: str
    filename: str

class MultiAsyncTaskResponse(BaseModel):
    """Response when multiple background tasks are created."""
    tasks: List[AsyncTaskCreateResponse]

class AsyncTaskStatus(BaseModel):
    """Response when checking the status of a background task."""
    task_id: str
    status: str # e.g., PENDING, PROGRESS, SUCCESS, FAILURE, CANCELLED
    progress: Optional[dict] = None # e.g., {"status": "Uploading..."}
    result: Optional[Any] = None # Will contain the final result on SUCCESS/FAILURE


# --- EXISTING SCHEMAS ---

class VoyageBase(BaseModel):
    destination: str

class VoyageCreate(VoyageBase):
    passport_ids: List[int] = []

class Voyage(VoyageBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True

class PassportBase(BaseModel):
    first_name: str
    last_name: str
    birth_date: date
    expiration_date: Optional[date] = None
    delivery_date: Optional[date] = None
    nationality: str
    passport_number: str
    confidence_score: Optional[float] = None

class PassportCreate(PassportBase):
    destination: Optional[str] = None

class Passport(PassportBase):
    id: int
    owner_id: int
    voyages: List[Voyage] = []
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    user_name: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    role: str
    passports: List["Passport"] = []
    voyages: List[Voyage] = []
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class InvitationCreate(BaseModel):
    email: EmailStr

class Invitation(InvitationCreate):
    id: int
    token: str
    expires_at: datetime
    is_used: bool
    class Config:
        from_attributes = True

class InvitationUpdate(BaseModel):
    expires_at: Optional[datetime] = None
    is_used: Optional[bool] = None

class IdsList(BaseModel):
    ids: List[int]

User.model_rebuild()