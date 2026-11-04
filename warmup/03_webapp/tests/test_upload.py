"""Tests for POST /upload: validation, parse errors, 5 MB size limit and the summary it returns."""

import io
from typing import TYPE_CHECKING

from fastapi import HTTPException
from main import CHUNK_SIZE
from main import app
from main import parse_upload
from main import validate_upload
import pandas as pd
import pytest
from starlette.testclient import TestClient

if TYPE_CHECKING:
    from collections.abc import Callable

CSV_BYTES = b"a,b\n1,2\n3,4\n"
MAX_SIZE = 5 * 1024 * 1024
EXE_BYTES = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff"  # start of a Windows executable
ZIP_HEADER_ONLY = b"PK\x03\x04 not really a spreadsheet"


def to_xlsx(frame: pd.DataFrame) -> bytes:
    """Write a DataFrame to a .xlsx file."""
    buffer = io.BytesIO()
    frame.to_excel(buffer, index=False)
    return buffer.getvalue()


def to_csv(frame: pd.DataFrame) -> bytes:
    """Write a DataFrame to a .csv file."""
    return frame.to_csv(index=False).encode()


def make_xlsx() -> bytes:
    """Build a small real .xlsx file in memory."""
    return to_xlsx(pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]}))


def stats(low: float, high: float, total: float, mean: float, not_numeric: int = 0) -> dict[str, float]:
    """Build the expected stats for one number column."""
    return {"min": low, "max": high, "sum": total, "mean": mean, "not_numeric": not_numeric}


@pytest.fixture
def client() -> TestClient:
    """Build a test client. Upload does not use storage, so nothing is overridden."""
    return TestClient(app)


def test_upload_too_large(client: TestClient) -> None:
    """POST /upload rejects files bigger than 5MB."""
    content = b"a" * (MAX_SIZE + 1)
    response = client.post("/upload", files={"file": ("big.csv", content)})
    assert response.status_code == 413
    assert "5MB" in response.json()["detail"]


def test_upload_ok(client: TestClient) -> None:
    """POST /upload accepts a valid CSV of exactly 5MB."""
    header = b"a,b\n"
    row = b"1,2\n"
    content = header + row * ((MAX_SIZE - len(header)) // len(row))
    assert len(content) == MAX_SIZE
    response = client.post("/upload", files={"file": ("ok.csv", content)})
    assert response.status_code == 201


def test_upload_larger_than_one_chunk(client: TestClient) -> None:
    """A file that needs several 64KB reads is put back together correctly."""
    rows = 50_000
    content = b"a,b\n" + b"1,2\n" * rows
    assert len(content) > CHUNK_SIZE * 3
    response = client.post("/upload", files={"file": ("chunks.csv", content)})
    assert response.status_code == 201
    assert response.json()["rows"] == rows


@pytest.mark.parametrize(
    ("filename", "content", "expected_status"),
    [
        ("data.csv", CSV_BYTES, 201),
        ("data.xlsx", make_xlsx(), 201),
        ("DATA.CSV", CSV_BYTES, 201),
        ("notes.txt", CSV_BYTES, 400),
        ("data.pdf", CSV_BYTES, 400),
        ("noextension", CSV_BYTES, 400),
    ],
)
def test_upload_extension(client: TestClient, filename: str, content: bytes, expected_status: int) -> None:
    """Allowed extensions return 201, anything else returns 400."""
    response = client.post("/upload", files={"file": (filename, content)})
    assert response.status_code == expected_status


def test_upload_wrong_extension_names_allowed_ones(client: TestClient) -> None:
    """The 400 message says which endings are allowed."""
    response = client.post("/upload", files={"file": ("notes.txt", CSV_BYTES)})
    detail = response.json()["detail"]
    assert ".csv" in detail
    assert ".xlsx" in detail


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("notes.csv", b"just a sentence\nnot a table at all\n"),
        ("one_column.csv", b"a\n1\n2\n"),
        ("ragged.csv", b"a,b\n1,2,3,4\n5\n"),
        ("empty.csv", b""),
        ("binary.csv", bytes(range(256)) * 4),
        ("renamed_exe.csv", EXE_BYTES),
        ("renamed_exe.xlsx", EXE_BYTES),
        ("zip_header_only.xlsx", ZIP_HEADER_ONLY),
        ("latin1.csv", "a,b\ncafé,2\n".encode("latin-1")),
        ("garbage.xlsx", b"this is not an excel file"),
        ("truncated.xlsx", make_xlsx()[:100]),
        ("empty.xlsx", b""),
    ],
)
def test_upload_unreadable(client: TestClient, filename: str, content: bytes) -> None:
    """A file with an allowed ending but unreadable content returns 422 with a reason, not a traceback."""
    response = client.post("/upload", files={"file": (filename, content)})
    assert response.status_code == 422
    assert response.json()["detail"]
    assert "Traceback" not in response.text


@pytest.mark.parametrize(
    ("filename", "to_bytes"),
    [("people.csv", to_csv), ("people.xlsx", to_xlsx)],
)
def test_summary_csv_and_xlsx_match(
    client: TestClient, filename: str, to_bytes: Callable[[pd.DataFrame], bytes]
) -> None:
    """The same data gives the same summary whether it was uploaded as .csv or .xlsx."""
    frame = pd.DataFrame({"name": ["Ana", "Ben", None], "age": [10, 20, 30]})
    response = client.post("/upload", files={"file": (filename, to_bytes(frame))})
    assert response.status_code == 201
    assert response.json() == {
        "filename": filename,
        "rows": 3,
        "columns": ["name", "age"],
        "empty_count": {"name": 1, "age": 0},
        "number_stats": {"age": stats(10, 30, 60, 20)},
    }


def test_summary_counts_empty_values_per_column(client: TestClient) -> None:
    """Every column gets its own count of empty cells."""
    frame = pd.DataFrame({"a": [1, None, 3], "b": [None, None, "x"], "c": [1, 2, 3]})
    response = client.post("/upload", files={"file": ("gaps.csv", to_csv(frame))})
    assert response.json()["empty_count"] == {"a": 1, "b": 2, "c": 0}


def test_summary_rounds_to_two_decimals(client: TestClient) -> None:
    """Stats are rounded to 2 decimals: the mean of 1, 2 and 2 is 1.67."""
    frame = pd.DataFrame({"n": [1, 2, 2], "label": ["x", "y", "z"]})
    response = client.post("/upload", files={"file": ("round.csv", to_csv(frame))})
    assert response.json()["number_stats"] == {"n": stats(1, 2, 5, 1.67)}


def test_summary_text_in_number_column_is_counted(client: TestClient) -> None:
    """A mostly-numeric column with one bad value still gets stats, and the bad value is counted."""
    frame = pd.DataFrame({"age": ["10", "abc", "30"], "label": ["x", "y", "z"]})
    response = client.post("/upload", files={"file": ("dirty.csv", to_csv(frame))})
    assert response.json()["number_stats"] == {"age": stats(10, 30, 40, 20, not_numeric=1)}


def test_summary_text_column_has_no_stats(client: TestClient) -> None:
    """A column of words gets no number stats."""
    frame = pd.DataFrame({"city": ["London", "Leeds", "Bristol"], "label": ["x", "y", "z"]})
    response = client.post("/upload", files={"file": ("words.csv", to_csv(frame))})
    assert response.json()["number_stats"] == {}


def test_summary_mostly_text_column_has_no_stats(client: TestClient) -> None:
    """A column where fewer than half the values are numbers is treated as text."""
    frame = pd.DataFrame({"code": ["a", "b", "c", "1"], "label": ["w", "x", "y", "z"]})
    response = client.post("/upload", files={"file": ("codes.csv", to_csv(frame))})
    assert response.json()["number_stats"] == {}


def test_summary_overflowing_sum_gives_no_stats(client: TestClient) -> None:
    """Numbers whose sum is too big for a float are left out, not returned as infinity, and nothing crashes."""
    frame = pd.DataFrame({"n": [1e308, 1e308], "label": ["x", "y"]})
    response = client.post("/upload", files={"file": ("huge.csv", to_csv(frame))})
    assert response.status_code == 201
    assert response.json()["number_stats"] == {}


def test_summary_text_in_number_column_xlsx(client: TestClient) -> None:
    """The same dirty column as the .csv test, but through Excel, which gives pandas a different column type."""
    frame = pd.DataFrame({"age": [10, "abc", 30], "label": ["x", "y", "z"]})
    response = client.post("/upload", files={"file": ("dirty.xlsx", to_xlsx(frame))})
    assert response.status_code == 201
    assert response.json()["number_stats"] == {"age": stats(10, 30, 40, 20, not_numeric=1)}


def test_summary_header_only_file(client: TestClient) -> None:
    """A CSV with a header and no rows has 0 rows, its columns, no empty values and no stats."""
    response = client.post("/upload", files={"file": ("header.csv", b"a,b\n")})
    assert response.status_code == 201
    assert response.json() == {
        "filename": "header.csv",
        "rows": 0,
        "columns": ["a", "b"],
        "empty_count": {"a": 0, "b": 0},
        "number_stats": {},
    }


def test_summary_numeric_headers_become_text(client: TestClient) -> None:
    """Excel headers like 2024 come back as the strings "2024", because JSON keys must be text."""
    frame = pd.DataFrame({2024: [1, 2], 2025: [3, 4]})
    response = client.post("/upload", files={"file": ("years.xlsx", to_xlsx(frame))})
    assert response.status_code == 201
    body = response.json()
    assert body["columns"] == ["2024", "2025"]
    assert body["number_stats"] == {"2024": stats(1, 2, 3, 1.5), "2025": stats(3, 4, 7, 3.5)}


def test_validate_accepts_csv_with_more_than_two_columns() -> None:
    """A CSV with 3 columns is fine. Only fewer than 2 is rejected."""
    validate_upload("wide.csv", b"a,b,c\n1,2,3\n")


def test_validate_accepts_real_xlsx() -> None:
    """A real .xlsx passes the signature check."""
    validate_upload("data.xlsx", make_xlsx())


def test_validate_rejects_missing_filename() -> None:
    """No filename gives 400."""
    with pytest.raises(HTTPException) as error:
        validate_upload(None, CSV_BYTES)
    assert error.value.status_code == 400


def test_validate_rejects_bad_extension() -> None:
    """A disallowed extension gives 400, even if the bytes look fine."""
    with pytest.raises(HTTPException) as error:
        validate_upload("data.exe", CSV_BYTES)
    assert error.value.status_code == 400


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("data.csv", EXE_BYTES),
        ("data.csv", "a,b\ncafé,2\n".encode("latin-1")),
        ("data.csv", b"a\n1\n"),
        ("data.csv", b"a,b\n1,2,3\n"),
        ("data.csv", b"a,b,c\n1,2\n"),
        ("data.xlsx", EXE_BYTES),
        ("data.xlsx", b"plain text"),
    ],
)
def test_validate_rejects_bad_content(filename: str, content: bytes) -> None:
    """Wrong bytes, bad encoding, one column or a ragged row give 422."""
    with pytest.raises(HTTPException) as error:
        validate_upload(filename, content)
    assert error.value.status_code == 422


def test_validate_names_the_ragged_line() -> None:
    """The 422 message points at the line with the wrong number of fields."""
    with pytest.raises(HTTPException) as error:
        validate_upload("ragged.csv", b"a,b\n1,2\n3,4,5\n")
    assert "line 3" in error.value.detail


def test_parse_empty_csv_says_no_data() -> None:
    """An empty CSV is a 422 with its own message."""
    with pytest.raises(HTTPException) as error:
        parse_upload(b"", ".csv")
    assert error.value.status_code == 422
    assert "no data" in error.value.detail


def test_parse_malformed_csv_gives_422() -> None:
    """A later row with extra fields is a pandas ParserError, which becomes a 422."""
    with pytest.raises(HTTPException) as error:
        parse_upload(b"a,b\n1,2\n3,4,5\n", ".csv")
    assert error.value.status_code == 422
    assert "CSV parsing failed" in error.value.detail


def test_parse_corrupt_xlsx_gives_422() -> None:
    """A file with the zip header but a broken archive is a BadZipFile, which becomes a 422."""
    with pytest.raises(HTTPException) as error:
        parse_upload(ZIP_HEADER_ONLY, ".xlsx")
    assert error.value.status_code == 422


def test_parse_value_error_gives_422(monkeypatch: pytest.MonkeyPatch) -> None:
    """A ValueError from pandas is a 422 and the raw error text is not sent to the client."""

    def fail(*_args: object, **_kwargs: object) -> pd.DataFrame:
        message = "secret internal detail"
        raise ValueError(message)

    monkeypatch.setattr(pd, "read_csv", fail)
    with pytest.raises(HTTPException) as error:
        parse_upload(CSV_BYTES, ".csv")
    assert error.value.status_code == 422
    assert "secret" not in error.value.detail


def test_parse_unexpected_error_gives_500(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    """Anything unexpected is a 500 with a fixed message, and the real error is logged."""

    def crash(*_args: object, **_kwargs: object) -> pd.DataFrame:
        message = "boom"
        raise RuntimeError(message)

    monkeypatch.setattr(pd, "read_csv", crash)
    with pytest.raises(HTTPException) as error:
        parse_upload(CSV_BYTES, ".csv")
    assert error.value.status_code == 500
    assert "boom" not in error.value.detail
    assert "boom" in caplog.text
