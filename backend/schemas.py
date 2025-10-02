

# # /schemas.py
# from pydantic import BaseModel, EmailStr
# from typing import List, Optional
# from datetime import date, datetime

# class VoyageBase(BaseModel):
#     destination: str

# class VoyageCreate(VoyageBase):
#     passport_ids: List[int] = []
    
# class Voyage(VoyageBase):
#     id: int
#     user_id: int
#     class Config:
#         from_attributes = True

# class PassportBase(BaseModel):
#     first_name: str
#     last_name: str
#     birth_date: date
#     expiration_date: date
#     delivery_date: date
#     nationality: str
#     passport_number: str
#     confidence_score: Optional[float] = None

# class PassportCreate(PassportBase):
#     destination: Optional[str] = None

# class Passport(PassportBase):
#     id: int
#     owner_id: int
#     voyages: List[Voyage] = [] # This line is added
#     class Config:
#         from_attributes = True

# class UserBase(BaseModel):
#     first_name: str
#     last_name: str
#     email: EmailStr
#     phone_number: str
#     user_name: str

# class UserCreate(UserBase):
#     password: str

# class UserUpdate(BaseModel):
#     first_name: Optional[str] = None
#     last_name: Optional[str] = None
#     email: Optional[EmailStr] = None
#     phone_number: Optional[str] = None
#     password: Optional[str] = None

# class User(UserBase):
#     id: int
#     role: str
#     passports: List["Passport"] = [] # Added quotes to fix forward reference
#     voyages: List[Voyage] = []
#     class Config:
#         from_attributes = True

# class Token(BaseModel):
#     access_token: str
#     token_type: str

# class TokenData(BaseModel):
#     username: Optional[str] = None

# class InvitationCreate(BaseModel):
#     email: EmailStr

# class Invitation(InvitationCreate):
#     id: int
#     token: str
#     expires_at: datetime
#     is_used: bool
#     class Config:
#         from_attributes = True


# class InvitationUpdate(BaseModel):
#     expires_at: Optional[datetime] = None
#     is_used: Optional[bool] = None


# class OcrFailure(BaseModel):
#     page_number: int
#     detail: str


# class OcrUploadResponse(BaseModel):
#     successes: List[Passport]
#     failures: List[OcrFailure]



# class IdsList(BaseModel):
#     ids: List[int]

# # This line is needed at the end of the file to resolve the forward reference
# User.model_rebuild()






from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date, datetime

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
    expiration_date: date
    delivery_date: date
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


class OcrFailure(BaseModel):
    page_number: int
    detail: str

# NEW: Schema for a successful extraction, linking it to a page number
class OcrSuccess(BaseModel):
    page_number: int
    passport: Passport

class OcrUploadResponse(BaseModel):
    successes: List[OcrSuccess] # CHANGED: Now uses the new OcrSuccess schema
    failures: List[OcrFailure]


class IdsList(BaseModel):
    ids: List[int]

# This line is needed at the end of the file to resolve the forward reference
User.model_rebuild()


