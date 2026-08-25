"""
Context manager warmup: a Timer implemented 2 ways (class with __enter__ and __exit__ and a function with
@contextlib.contextmanager), both printing the elapsed time even when the wrapped block raises an exception."""

import contextlib
import time
from typing import Any, Generator


# Using a class
class Timer:
    """A context manager that prints the elapsed time with 2 decimal places when exiting the context.

    Attributes:
        start (float): The time when the context was entered.
        exc_type (type): The type of the exception that caused the context to exit.
        exc_val (exception): The exception instance that caused the context to exit.
        traceback (traceback): The traceback object associated with the exception.
    """

    def __enter__(self):
        self.start = time.time()
        return self  # I can do "with Timer() as t: (I will not do with Timer() because the rest of my code will be unreachable)

    def __exit__(self, exc_type, exc_val, traceback):
        elapsed = time.time() - self.start
        print(f"Elapsed time: {elapsed:.2f} seconds")


# Using a function
@contextlib.contextmanager
def timer() -> Generator[None, Any, None]:
    try:
        start = time.time()
        yield
    finally:
        elapsed = time.time() - start
        print(f"Elapsed time: {elapsed:.2f} seconds")


with timer():
    time.sleep(1)
    raise Exception("Something bad happened")
