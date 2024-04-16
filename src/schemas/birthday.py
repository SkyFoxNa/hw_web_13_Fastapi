from typing import Optional

from pydantic import BaseModel, EmailStr, Field, constr
from datetime import date


class BirthdayResponse(BaseModel):
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

    class Config:
        from_attributes = True