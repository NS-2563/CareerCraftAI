from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# User schemas
class UserBase(BaseModel):
    email: str
    username: str = Field(..., min_length=3, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None


class UserResponse(UserBase):
    id: int
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserInDB(UserResponse):
    hashed_password: str

    model_config = {"from_attributes": True}


# Auth schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(UserCreate):
    pass


# Google OAuth (placeholder)
class GoogleOAuthRequest(BaseModel):
    code: str


class GoogleOAuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse