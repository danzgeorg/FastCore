"""
Static HTML registration form with FastAPI POST endpoint.

Passwords are hashed and a random salt before saving to file. The password is never returned in the response. Duplicate
emails are rejected with 409 and message. No validation is done yet.
"""

import hashlib
import hmac
import json
from pathlib import Path
import secrets
from typing import Annotated
from typing import cast

from fastapi import FastAPI
from fastapi import Form
from fastapi import HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pydantic import EmailStr

# create FastAPI app
app = FastAPI()

class RegisterRequest(BaseModel):
    """Shape of the registration body."""

    email: EmailStr
    password: str
    city: str

class LoginRequest(BaseModel):
    """Shape of the login body."""

    email: EmailStr
    password: str

class User:
    """Represents a registered user with a salted password hash."""

    def __init__(self, email: EmailStr, city: str, password: str) -> None:
        self.email = email
        self.city = city

        salt = secrets.token_bytes(16)
        hashed_password = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
        self.salt = salt.hex()
        self.hash = hashed_password.hex()

register = "static/register.html"
login = "static/login.html"
users_file = Path("users.json")

def load_users() -> list[dict[str, str]]:
    """Load the users JSON file and return it treating a missing or corrupt file as empty."""
    if users_file.exists():
        try:
            with users_file.open() as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return []
        return cast("list[dict[str, str]]", data)
    return []


@app.get("/")
def get_register() -> FileResponse:
    """Serve the registration form."""
    return FileResponse(register)


@app.get("/login")
def get_login() -> FileResponse:
    """Serve the login form."""
    return FileResponse(login)


@app.post("/register")
def register_user(
    payload: Annotated[RegisterRequest, Form()],
) -> dict[str, str]:
    """Register a new user."""
    users = load_users()

    for user in users:
        if user["email"].lower() == payload.email.lower():
            raise HTTPException(status_code=409, detail="Email already registered.")

    new_user = User(email=payload.email, city=payload.city, password=payload.password)
    users.append(new_user.__dict__)

    with users_file.open("w") as f:
        json.dump(users, f, indent=4)

    return {"email": payload.email, "city": payload.city}


@app.post("/login")
def login_user(payload: LoginRequest) -> dict[str, str]:
    """Log user in."""
    users = load_users()

    for user in users:
        if user["email"].lower() == payload.email.lower():
            salt = bytes.fromhex(user["salt"])
            expected_hash = bytes.fromhex(user["hash"])
            given_hash = hashlib.pbkdf2_hmac("sha256", payload.password.encode(), salt, 100_000)

            if hmac.compare_digest(given_hash, expected_hash):
                return {"email": user["email"], "city": user["city"]}
    raise HTTPException(status_code=401, detail="Incorrect email or password.")
