"""Pydantic models for user data: what comes in and what goes out."""

import hashlib
import secrets
import uuid

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

    password: str | None = None
    city: str | None = None


class UserPublic(BaseModel):
    """Shape of the user object that gets returned to the user."""

    id: str
    email: EmailStr
    city: str


class User:
    """Represents a registered user with a salted password hash.

    Not a pydantic BaseModel.

    By the time a user is created, its data has already been validated (UserCreate/RegisterRequest).

    This class is the object built from the validated data (generating the id and
    computing the salted password hash, not validating input).
    """

    def __init__(self, email: EmailStr, city: str, password: str) -> None:
        self.id = str(uuid.uuid4())
        self.email = email
        self.city = city

        salt = secrets.token_bytes(16)
        self.salt = salt.hex()
        self.hash = User.hash_password(password, salt).hex()

    @staticmethod
    def hash_password(password: str, salt: bytes) -> bytes:
        """Hash a password against a given salt. Shared by registration and login."""
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
