"""Tests for user CRUD, using a temporary UserStorage instead of the real users.json."""



from typing import TYPE_CHECKING
from typing import cast

from main import app
import pytest
from starlette.testclient import TestClient
from storage import UserStorage
from storage import get_storage

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    import httpx


@pytest.fixture
def client(tmp_path: Path) -> Generator[TestClient]:
    """Build a test client with a UserStorage pointed at a temp file, not the real JSON."""
    test_storage = UserStorage(tmp_path / "test_users.json")
    app.dependency_overrides[get_storage] = lambda: test_storage

    yield TestClient(app)

    app.dependency_overrides.clear()

def create_test_user(
        client: TestClient,
        email: str = "ana@example.com",
        password: str = "pw1",
        city: str = "London"
) -> httpx.Response:
    """Create a user via POST /users and return the response."""
    response = client.post("/users", json={"email": email, "password": password, "city": city})
    return cast("httpx.Response", response)


def assert_no_secrets(body: dict[str, str]) -> None:
    """Assert that no secrets are present in a user response body."""
    assert "salt" not in body
    assert "hash" not in body

def test_create_user(client: TestClient)-> None:
    """POST /users should return a 201 status code with the new user's public fields."""
    response = create_test_user(client, password="correct-password")
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ana@example.com"
    assert body["city"] == "London"
    assert_no_secrets(body)


def test_get_invalid_id(client: TestClient) -> None:
    """GET /users{user_id} should return a 404 status code if using an invalid id."""
    response = client.get("/users/does-not-exist")

    assert response.status_code == 404

def test_login_with_wrong_password(client: TestClient) -> None:
    """Login with wrong password should return a 401 status code."""
    create_test_user(client, password="correct-password")

    response = client.post(
        "/login",
        json={"email": "ana@example.com", "password": "wrong-password"}
    )

    assert response.status_code == 401


def test_list_users_returns_all(client: TestClient) -> None:
    """GET /users should return a list of all users."""
    create_test_user(client, email="ana@example.com", city="London")
    create_test_user(client, email="ben@example.com", password="pw2", city="Leeds")

    response = client.get("/users")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    emails = {user["email"] for user in body}
    assert emails == {"ana@example.com", "ben@example.com"}


def test_get_user_by_id(client: TestClient) -> None:
    """GET /users/{user_id} returns user's public fields."""
    created = create_test_user(client).json()

    response = client.get(f"/users/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["email"] == "ana@example.com"

def test_create_user_duplicate_email(client: TestClient) -> None:
    """POST /users should return a 409 status code if a user with that email already exists."""
    create_test_user(client,email="ana@example.com")

    response = create_test_user(client, email="ana@example.com", password="pw2",city="Leeds")

    assert response.status_code == 409
    all_users = client.get("/users").json()
    assert len(all_users) == 1

def test_delete_user(client: TestClient) -> None:
    """DELETE /users/{user_id} should return a 204 status code and the user is actually removed."""
    created = create_test_user(client).json()

    response = client.delete(f"/users/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""

    follow_up = client.get(f"/users/{created['id']}")
    assert follow_up.status_code == 404


def test_delete_invalid_id(client: TestClient) -> None:
    """DELETE /users/{user_id} should return a 404 status code if the id is invalid."""
    response = client.delete("/users/does-not-exist")

    assert response.status_code == 404


def test_response_never_contains_salt_hash(client: TestClient) -> None:
    """No response should contain a salt or hash."""
    created = create_test_user(client).json()
    assert_no_secrets(created)

    listed = client.get("/users").json()[0]
    assert_no_secrets(listed)

    fetched = client.get(f"/users/{created['id']}").json()
    assert_no_secrets(fetched)

    updated = client.put(f"/users/{created['id']}", json={"city": "Leeds"}).json()
    assert_no_secrets(updated)

def test_update_user_password(client: TestClient) -> None:
    """PUT /users/{user_id} with a new password lets the user log in with it, and old stops working."""
    created = create_test_user(client, password="old-password").json()

    client.put(f"/users/{created['id']}",json={"password": "new-password"})

    old_login = client.post("/login", json={"email": "ana@example.com", "password": "old-password"})
    new_login = client.post("/login", json={"email": "ana@example.com", "password": "new-password"})

    assert old_login.status_code == 401
    assert new_login.status_code == 200
