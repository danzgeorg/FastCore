"""Pydantic models for user data: what comes in and what goes out."""

import hashlib
import uuid
import secrets

from pydantic import BaseModel
from pydantic import EmailStr

class RegisterRequest(BaseModel):
    """Shape of the registration body."""

    email: EmailStr
    password: str
    city: str


class LoginRequest(BaseModel):
    """Shape of the login body."""

    email: EmailStr
    password: str

class UserCreate(BaseModel):
    """Shape of the user object that gets created."""
    email: EmailStr
    password: str
    city: str

class UserUpdate(BaseModel):
    """Shape of the user object that gets updated. All optional since an update could be a partial update."""
    email: EmailStr | None = None
    password: str | None = None
    city: str | None = None

class UserPublic(BaseModel):
    """Shape of the user object that gets returned to the user."""
    id: str
    email: EmailStr
    city: str


class User:
    """Represents a registered user with a salted password hash.

    Not a pydantic BaseModel. By the time a user is created, its data has already been validated (UserCreate/RegisterRequest).
    This class is the object built from the validated data (generating the id and computing the salted password hash, not
    validating input)."""

    def __init__(self, email: EmailStr, city: str, password: str) -> None:
        self.id = str(uuid.uuid4())
        self.email = email
        self.city = city

        salt = secrets.token_bytes(16)
        hashed_password = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
        self.salt = salt.hex()
        self.hash = hashed_password.hex()