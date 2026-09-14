"""All reading and writing of users.json.
main.py will not open a file directly."""

import json
from pathlib import Path
from typing import cast

users_file = Path("users.json")

def load_users() -> list[dict[str, str]]:
    """Load the user's JSON file and return it treating a missing or corrupt file as empty."""
    if users_file.exists():
        try:
            with users_file.open() as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return []
        return cast("list[dict[str, str]]", data)
    return []

def save_users(users: list[dict[str, str]]) -> None:
    """Save the user's JSON file."""
    with users_file.open("w") as f:
        json.dump(users, f, indent=4)