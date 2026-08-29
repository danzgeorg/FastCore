"""Generator warmup: reading a CSV lazily with yield, generator exhaustion, and list vs generator expressions."""

import csv
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator

path = "../../warmup-data/people.csv"


def read_csv(filename: str) -> Generator[list[str]]:
    """Yield each row of the csv file."""
    with Path(filename).open() as f:
        reader = csv.reader(f)
        yield from reader


# Task 1:
print(f"Task 1: {list(read_csv(path))}\n")

# Task 2: call the generator without looping
gen = read_csv(path)
print(f"Task 2: {gen}\n")

# Task 3: loop over the generator twice
print("Task 3:")
print("First loop: ")
for row in gen:
    print(f"{row}")
print("\nSecond loop: ")
for row in gen:
    print(f"{row}")

# Second loop outputs nothing because the generator is exhausted after the
# first loop, but no error is raised.

# Task 4: Compare list comprehension and generator
print("\nTask 4:")
with Path(path).open() as f:
    line_list = [line for line in f]
    print(f"List comprehension: {line_list}")

with Path(path).open() as f:
    line_gen = (line for line in f)
    print(f"Generator: {line_gen}")