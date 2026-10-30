"""Tests for POST /upload: extension check and 5 MB size limit."""

from main import app
import pytest
from starlette.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """Build a test client. Upload does not use storage, so nothing is overridden."""
    return TestClient(app)


def test_upload_too_large(client: TestClient) -> None:
    """POST /upload rejects files bigger than 5MB."""
    content = b"a" * (5 * 1024 * 1024 + 1)
    response = client.post("/upload", files={"file": ("big.csv", content)})
    assert response.status_code == 413


def test_upload_ok(client: TestClient) -> None:
    """POST /upload accepts files smaller than 5MB."""
    content = b"a" * (5 * 1024 * 1024)
    response = client.post("/upload", files={"file": ("ok.csv", content)})
    assert response.status_code == 201


@pytest.mark.parametrize(
    ("filename", "expected_status"),
    [
        ("data.csv", 201),
        ("data.xlsx", 201),
        ("DATA.CSV", 201),
        ("notes.txt", 400),
        ("data.pdf", 400),
        ("noextension", 400),
    ],
)
def test_upload_extension(client: TestClient, filename: str, expected_status: int) -> None:
    """Allowed extensions return 201, anything else returns 400."""
    response = client.post("/upload", files={"file": (filename, b"a,b\n1,2")})
    assert response.status_code == expected_status
