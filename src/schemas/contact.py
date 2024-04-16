from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from src.schemas.user import UserResponse


class ContactSchema(BaseModel):
    first_name: str = Field(min_length=3, max_length=50)
    last_name: str = Field(min_length=3, max_length=50)
    email: EmailStr
    phone_number: str = Field(min_length=3, max_length=20)
    birthday: date
    address: str = Field(min_length=3, max_length=250)
    notes: str = Field(min_length=3, max_length=250)
    interests: str = Field(min_length=3, max_length=250)
    is_active: Optional[bool] = False


class ContactUpdateSchema(ContactSchema):
    is_active: bool


class ContactResponse(BaseModel):
    id: int = 1
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: date
    address: str
    notes: str
    interests: str
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None
    user: UserResponse | None

    class Config:
        from_attributes = True
