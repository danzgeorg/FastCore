"""
FastAPI Webapp: registration and login, and full user CRUD.

Passwords are hashed and salted before saving to file. The password, salt and hash are not returned in any response.

This file Contains no file I/O.
"""

import hmac
from typing import Annotated

from fastapi import FastAPI
from fastapi import Form
from fastapi import HTTPException
from fastapi.responses import FileResponse
from models import LoginRequest
from models import RegisterRequest
from models import User
from models import UserCreate
from models import UserPublic
from models import UserUpdate
from storage import email_exists
from storage import find_user_by_email
from storage import find_user_by_id
from storage import load_users
from storage import save_users

# create FastAPI app
app = FastAPI()

register = "static/register.html"
login = "static/login.html"


def create_new_user(email: str, password: str, city: str) -> User:
    """Create a new user. Raise 409 if email is taken."""
    users = load_users()

    if email_exists(users, email):
        raise HTTPException(status_code=409, detail="Email already registered.")

    new_user = User(email=email, city=city, password=password)
    users.append(new_user.__dict__)
    save_users(users)

    return new_user


def get_user_or_404(user_id: str, users: list[dict[str, str]]) -> dict[str, str]:
    """Get a user by id, or raise 404 if not found."""
    user = find_user_by_id(users, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User not found with id {user_id}.")
    return user


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
    new_user = create_new_user(payload.email, payload.password, payload.city)
    return {"email": new_user.email, "city": new_user.city}


@app.post("/login")
def login_user(payload: LoginRequest) -> dict[str, str]:
    """Log user in."""
    users = load_users()
    user = find_user_by_email(users, payload.email)

    if user is not None:
        salt = bytes.fromhex(user["salt"])
        expected_hash = bytes.fromhex(user["hash"])
        actual_hash = User.hash_password(payload.password, salt)

        if hmac.compare_digest(expected_hash, actual_hash):
            return {"email": payload.email, "city": user["city"]}

    raise HTTPException(status_code=401, detail="Invalid email or password.")


@app.post("/users", response_model=UserPublic)
def create_user(payload: UserCreate) -> UserPublic:
    """Create a new user with JSON."""
    new_user = create_new_user(payload.email, payload.password, payload.city)
    return UserPublic(**new_user.__dict__)


@app.get("/users", response_model=list[UserPublic])
def get_users() -> list[UserPublic]:
    """Get all users."""
    users = load_users()
    return [UserPublic(**user) for user in users]


@app.get("/users/{user_id}", response_model=UserPublic)
def get_user(user_id: str) -> UserPublic:
    """Get a single user."""
    users = load_users()
    user = get_user_or_404(user_id, users)
    return UserPublic(**user)


@app.put("/users/{user_id}", response_model=UserPublic)
def update_user(user_id: str, payload: UserUpdate) -> UserPublic:
    """Update a single user's city and/or password. Unknown id gives 404."""
    users = load_users()
    user = get_user_or_404(user_id, users)

    if payload.city is not None:
        user["city"] = payload.city
    if payload.password is not None:
        updated = User(email=user["email"], city=user["city"], password=payload.password)
        user["salt"] = updated.salt
        user["hash"] = updated.hash

    save_users(users)
    return UserPublic(**user)


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str) -> None:
    """Delete a single user using their id. Returns 204. Unknown id gives 404."""
    users = load_users()
    user = get_user_or_404(user_id, users)

    users.remove(user)
    save_users(users)
