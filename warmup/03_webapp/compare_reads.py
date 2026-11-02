"""Compare two ways of counting the rows in a CSV: all at once, and in chunks.

Run it with `python compare_reads.py`. It reads `warmup-data/people.csv`, then a made up CSV with 1 million rows that
is created in a temp folder and deleted afterwards. Peak memory comes from `tracemalloc`.

Results on my machine:

      people.csv, 17 rows:
          whole file: 17 rows, peak 0.41 MB |
          chunked:    17 rows, peak 0.39 MB
      generated big.csv, 1 million rows, 23.53 MB on disk:
          whole file: 1 million rows, peak 114.48 MB |
          chunked:    1 million rows, peak 1.47 MB

Both ways count the same number of rows. On `people.csv` there is only 1 chunk, so there isn't a big difference. On the
big file the whole file read used about 80 times more peak memory. The memory grows with the size of the file, while
the chunked read only ever holds `CHUNK_ROWS` rows.

Exact numbers change a little between different machines.
"""

import csv
from pathlib import Path
import sys
import tempfile
import tracemalloc
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from collections.abc import Callable

PEOPLE_CSV = Path(__file__).resolve().parents[2] / "warmup-data" / "people.csv"
CHUNK_ROWS = 1000
BIG_FILE_ROWS = 1_000_000
BYTES_PER_MB = 1024 * 1024


def count_rows_whole(path: Path) -> int:
    """Count the rows by loading the whole file into one DataFrame."""
    return len(pd.read_csv(path))


def count_rows_chunked(path: Path) -> int:
    """Count the rows by chunk, so only CHUNK_ROWS rows are in memory at once."""
    return sum(len(chunk) for chunk in pd.read_csv(path, chunksize=CHUNK_ROWS))


def measure(count_rows: Callable[[Path], int], path: Path) -> tuple[int, float]:
    """Run count_rows on path and return its row count and the peak memory it allocated in MB."""
    tracemalloc.start()
    try:
        rows = count_rows(path)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return rows, peak / BYTES_PER_MB


def write_big_csv(path: Path) -> None:
    """Write a made up CSV with BIG_FILE_ROWS rows."""
    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "name", "score"])
        writer.writerows((number, f"person {number}", number % 100) for number in range(BIG_FILE_ROWS))


def report(label: str, path: Path) -> None:
    """Print the row count and peak memory of both ways of reading path."""
    whole_rows, whole_mb = measure(count_rows_whole, path)
    chunked_rows, chunked_mb = measure(count_rows_chunked, path)
    sys.stdout.write(f"{label} {path.stat().st_size / BYTES_PER_MB:.2f} MB\n")
    sys.stdout.write(f" whole file: {whole_rows} rows, peak {whole_mb:.2f} MB\n")
    sys.stdout.write(f" chunked: {chunked_rows} rows, peak {chunked_mb:.2f} MB\n")
    sys.stdout.write(f" row counts match: {whole_rows == chunked_rows}\n")


def main() -> None:
    """Compare both ways on people.csv then on a big generated file that is deleted afterwards."""
    report("people.csv", PEOPLE_CSV)
    with tempfile.TemporaryDirectory() as folder:
        big_file = Path(folder) / "big.csv"
        write_big_csv(big_file)
        report("big.csv", big_file)


if __name__ == "__main__":
    main()
