"""
FastAPI Webapp: registration and login, and full user CRUD.

Passwords are hashed and salted before saving to file. The password, salt and hash are not returned in any response.

This file Contains no file I/O.
"""

import csv
import hmac
import io
import logging
import math
from pathlib import Path
import time
from typing import TYPE_CHECKING
from typing import Annotated
import zipfile

from fastapi import Depends
from fastapi import FastAPI
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import Request
from fastapi import UploadFile
from fastapi.responses import FileResponse
from models import LoginRequest
from models import NumberStats
from models import RegisterRequest
from models import UploadSummary
from models import User
from models import UserCreate
from models import UserPublic
from models import UserUpdate
import pandas as pd
from storage import UserStorage
from storage import get_storage

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from collections.abc import Callable

    from starlette.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# create FastAPI app
app = FastAPI()

register = "static/register.html"
login = "static/login.html"
index = "static/index.html"

ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
FIVE_MB = 5 * 1024 * 1024  # 5MB
CHUNK_SIZE = 64 * 1024  # 64KB
MIN_CSV_COLUMNS = 2
NUMBER_DTYPE_KINDS = frozenset("iufO")  # int, unsigned int, float, and text/object columns that may hold numbers


@app.middleware("http")
async def log_requests(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Log all requests."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000

    logger.info(
        "%s %s %s %.2fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


def create_new_user(email: str, password: str, city: str, storage: UserStorage) -> User:
    """Create a new user. Raise 409 if email is taken."""
    users = storage.load_users()

    if storage.email_exists(users, email):
        raise HTTPException(status_code=409, detail="Email already registered.")

    new_user = User(email=email, city=city, password=password)
    users.append(new_user.__dict__)
    storage.save_users(users)

    return new_user


def get_user_or_404(user_id: str, users: list[dict[str, str]], storage: UserStorage) -> dict[str, str]:
    """Get a user by id, or raise 404 if not found."""
    user = storage.find_user_by_id(users, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User not found with id {user_id}.")
    return user


async def read_file(file: UploadFile) -> bytes:
    """Read a file in chunks. Raise 413 if it is over 5MB."""
    data = bytearray()
    total = 0
    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > FIVE_MB:
            raise HTTPException(status_code=413, detail="File too large. Max 5MB.")
        data.extend(chunk)
    return bytes(data)


def validate_csv(content: bytes) -> None:
    """Raise 422 unless content is UTF-8 text with 2+ columns and the same field count on every row."""
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="CSV file is not valid UTF-8.") from exc

    reader = csv.reader(io.StringIO(text))
    header = next(reader, [])
    if len(header) < MIN_CSV_COLUMNS:
        raise HTTPException(status_code=422, detail="CSV needs a header row with at least 2 columns.")

    for row in reader:
        if row and len(row) != len(header):
            raise HTTPException(
                status_code=422, detail=f"CSV line {reader.line_num} has {len(row)} fields, expected {len(header)}."
            )


def parse_upload(content: bytes, extension: str) -> pd.DataFrame:
    """Read an uploaded .csv or .xlsx into a DataFrame. Raise 422 if it cannot be read."""
    buffer = io.BytesIO(content)
    try:
        if extension == ".csv":
            validate_csv(content)
            data = pd.read_csv(buffer)
        else:
            data = pd.read_excel(buffer)
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        pd.errors.OptionError,
        zipfile.BadZipFile,
        ValueError,
    ) as exc:
        raise HTTPException(status_code=422, detail=f"Could not read file: {exc}") from exc
    return data


def number_stats(numbers: list[float], non_empty_count: int) -> NumberStats | None:
    """Return stats for a column that mostly holds numbers, or None if it does not or the result is not finite."""
    if not numbers or len(numbers) < non_empty_count * 0.5:
        return None

    minimum = min(numbers)
    maximum = max(numbers)
    total = sum(numbers)
    mean = total / len(numbers)

    if not all(math.isfinite(value) for value in (minimum, maximum, total, mean)):
        return None

    return NumberStats(
        min=round(minimum, 2),
        max=round(maximum, 2),
        sum=round(total, 2),
        mean=round(mean, 2),
        not_numeric=non_empty_count - len(numbers),
    )


def summarise(data: pd.DataFrame, filename: str) -> UploadSummary:
    """Summarise the converted copies of the columns."""
    stats: dict[str, NumberStats] = {}

    for name, column in data.items():
        if column.dtype.kind not in NUMBER_DTYPE_KINDS:
            continue
        non_empty = column.dropna()
        converted = pd.to_numeric(non_empty, errors="coerce").replace([math.inf, -math.inf], math.nan).dropna()
        column_stats = number_stats(converted.tolist(), len(non_empty))
        if column_stats is not None:
            stats[str(name)] = column_stats

    return UploadSummary(
        filename=filename,
        rows=len(data),
        columns=[str(name) for name in data.columns],
        empty_count={str(name): int(count) for name, count in data.isna().sum().items()},
        number_stats=stats,
    )


@app.get("/")
def get_register() -> FileResponse:
    """Serve the registration form."""
    return FileResponse(register)


@app.get("/login")
def get_login() -> FileResponse:
    """Serve the login form."""
    return FileResponse(login)


@app.get("/upload-page")
def get_upload_page() -> FileResponse:
    """Serve the upload page form."""
    return FileResponse(index)


@app.post("/register")
def register_user(
    payload: Annotated[RegisterRequest, Form()], storage: Annotated[UserStorage, Depends(get_storage)]
) -> dict[str, str]:
    """Register a new user."""
    try:
        new_user = create_new_user(payload.email, payload.password, payload.city, storage)
        logger.info("User %s was registered successfully.", payload.email)
    except HTTPException as exc:
        logger.info("Could not register user %s: %s", payload.email, exc.detail)
        raise
    return {"email": new_user.email, "city": new_user.city}


@app.post("/login")
def login_user(payload: LoginRequest, storage: Annotated[UserStorage, Depends(get_storage)]) -> dict[str, str]:
    """Log user in."""
    users = storage.load_users()
    user = storage.find_user_by_email(users, payload.email)

    if user is not None:
        salt = bytes.fromhex(user["salt"])
        expected_hash = bytes.fromhex(user["hash"])
        actual_hash = User.hash_password(payload.password, salt)

        if hmac.compare_digest(expected_hash, actual_hash):
            logger.info("User %s was logged successfully.", payload.email)
            return {"email": payload.email, "city": user["city"]}

    # Vague logging prevents a potential hacker from using the response
    logger.warning("Failed to login user: %s", payload.email)
    raise HTTPException(status_code=401, detail="Invalid email or password.")


@app.post("/users", response_model=UserPublic, status_code=201)
def create_user(payload: UserCreate, storage: Annotated[UserStorage, Depends(get_storage)]) -> UserPublic:
    """Create a new user with JSON."""
    try:
        new_user = create_new_user(payload.email, payload.password, payload.city, storage)
        logger.info("User %s was created successfully.", payload.email)
    except HTTPException as exc:
        logger.info("Could not create user %s: %s", payload.email, exc.detail)
        raise
    return UserPublic(**new_user.__dict__)


@app.post("/upload", status_code=201)
async def upload_file(file: Annotated[UploadFile, File()]) -> UploadSummary:
    """Upload a file."""
    filename = file.filename
    allowed = ",".join(sorted(ALLOWED_EXTENSIONS))
    if filename is None:
        raise HTTPException(status_code=400, detail="No filename provided.")
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file extension. Allowed: {allowed}")
    content = await read_file(file)
    data = parse_upload(content, extension)
    logger.info("Uploaded file successfully %s", filename)
    return summarise(data, filename)


@app.get("/users", response_model=list[UserPublic])
def get_users(storage: Annotated[UserStorage, Depends(get_storage)]) -> list[UserPublic]:
    """Get all users."""
    users = storage.load_users()
    return [UserPublic(**user) for user in users]


@app.get("/users/{user_id}", response_model=UserPublic)
def get_user(user_id: str, storage: Annotated[UserStorage, Depends(get_storage)]) -> UserPublic:
    """Get a single user."""
    users = storage.load_users()
    user = get_user_or_404(user_id, users, storage)
    return UserPublic(**user)


@app.put("/users/{user_id}", response_model=UserPublic)
def update_user(user_id: str, payload: UserUpdate, storage: Annotated[UserStorage, Depends(get_storage)]) -> UserPublic:
    """Update a single user's city and/or password. Unknown id gives 404."""
    users = storage.load_users()
    user = get_user_or_404(user_id, users, storage)

    if payload.city is not None:
        user["city"] = payload.city
    if payload.password is not None:
        updated = User(email=user["email"], city=user["city"], password=payload.password)
        user["salt"] = updated.salt
        user["hash"] = updated.hash

    storage.save_users(users)
    logger.info("Updated user %s.", user["email"])
    return UserPublic(**user)


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str, storage: Annotated[UserStorage, Depends(get_storage)]) -> None:
    """Delete a single user using their id. Returns 204. Unknown id gives 404."""
    users = storage.load_users()
    user = get_user_or_404(user_id, users, storage)

    users.remove(user)
    storage.save_users(users)
    logger.info("Deleted user %s.", user["email"])
