"""All reading and writing of users.json.

main.py will not open a file directly.
"""

import json
from pathlib import Path
from typing import cast


class UserStorage:
    """Reads and writes users to a JSON file."""

    def __init__(self, path: Path) -> None:
        self.path = path



    def load_users(self) -> list[dict[str, str]]:
       """Load the user's JSON file and return it treating a missing or corrupt file as empty."""
       if self.path.exists():
           try:
               with self.path.open() as f:
                   data = json.load(f)
           except json.JSONDecodeError:
               return []
           return cast("list[dict[str, str]]", data)
       return []


    def save_users(self,users: list[dict[str, str]]) -> None:
        """Save the user's JSON file."""
        with self.path.open("w") as f:
           json.dump(users, f, indent=4)


    def find_user_by_id(self, users: list[dict[str, str]], user_id: str) -> dict[str, str] | None:
        """Find a user by their id."""
        for user in users:
            if user.get("id") == user_id:
                return user
        return None


    def find_user_by_email(self, users: list[dict[str, str]], email: str) -> dict[str, str] | None:
        """Find a user by their email."""
        email_lower = email.lower()
        for user in users:
            if user.get("email", "").lower() == email_lower:
                return user
        return None


    def email_exists(self, users: list[dict[str, str]], email: str) -> bool:
        """Check if a user with a given email already exists."""
        return self.find_user_by_email(users, email) is not None

def get_storage() -> UserStorage:
    """Get a UserStorage instance."""
    return UserStorage(Path("users.json"))
