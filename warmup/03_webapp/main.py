from fastapi import FastAPI
from fastapi import Form
from fastapi import HTTPException
from fastapi.responses import FileResponse
import json
import os
import secrets
import hashlib

app = FastAPI()

website = "static/register.html"

@app.get("/")
def get_website() -> FileResponse:
    return FileResponse(website)

@app.post("/register")
def register_user(email: str = Form(...), password: str = Form(...), city: str = Form(...)):
    email = email.lower()
    if not email or not password:
        return {"error": "Email and password are required."}

    # load existing users from file
    if os.path.exists("users.json"):
        with open("users.json", "r") as users_file:
            users = json.load(users_file)
    else:
        users = []

    # check if email already exists
    for user in users:
        if user["email"] == email:
            raise HTTPException(status_code=409, detail="Email already registered.")

    # hash the password
    salt = secrets.token_bytes(16)
    hashed_password = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    salt_hex = salt.hex()
    hash_hex = hashed_password.hex()

    # save user to file
    new_user = {"email": email, "salt": salt_hex, "hash": hash_hex, "city": city}
    users.append(new_user)
    with open("users.json", "w") as users_file:
        json.dump(users, users_file, indent=4)

    return {"email": email, "city": city}

