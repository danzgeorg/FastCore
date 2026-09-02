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

from pydantic import BaseModel
from pydantic import EmailStr
from email_validator import EmailNotValidError
from email_validator import validate_email
from fastapi import FastAPI
from fastapi import Form
from fastapi import HTTPException
from fastapi.responses import FileResponse

# create FastAPI app
app = FastAPI()

class LoginRequest(BaseModel):
    """Shape of the JSON request body."""
    email: EmailStr
    password: str

register = "static/register.html"
login = "static/login.html"
users_file = Path("users.json")

def load_users() -> list[dict[str, str]]:
    """Load the users JSON file and return it treating a missing or corrupt file as empty."""
    if users_file.exists():
        try:
            with users_file.open() as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
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
    email: Annotated[str, Form()], password: Annotated[str, Form()], city: Annotated[str, Form()]
) -> dict[str, str]:
    """Register a new user."""
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")

    try:
        validate_email(email)
    except EmailNotValidError:
        raise HTTPException(status_code=400, detail="Invalid email address.") from None

    # load existing users from file
    if users_file.exists():
        try:
            with users_file.open() as f:
                users = json.load(f)
        except json.JSONDecodeError:
            users = []
    else:
        users = []

    # check if email already exists
    for user in users:
        if user["email"].lower() == email.lower():
            raise HTTPException(status_code=409, detail="Email already registered.")

    # hash the password
    salt = secrets.token_bytes(16)
    hashed_password = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    salt_hex = salt.hex()
    hash_hex = hashed_password.hex()

    # save user to file
    new_user = {"email": email, "salt": salt_hex, "hash": hash_hex, "city": city}
    users.append(new_user)
    with users_file.open("w") as f:
        json.dump(users, f, indent=4)

    return {"email": email, "city": city}

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