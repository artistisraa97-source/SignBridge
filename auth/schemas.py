from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=64)
    last_name: str = Field(..., min_length=1, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

    @model_validator(mode='after')
    def validate_passwords(self):
        if self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self


class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    created_at: Optional[datetime]

    model_config = {
        'from_attributes': True
    }


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class ResendRequest(BaseModel):
    email: EmailStr
