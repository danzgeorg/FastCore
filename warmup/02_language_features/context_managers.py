"""
Context manager warmup: a Timer implemented 2 ways (class with __enter__ and __exit__ and a function with
@contextlib.contextmanager), both printing the elapsed time even when the wrapped block raises an exception."""

import contextlib
import time
from typing import Any, Generator


# Using a class
class Timer:
    """Context manager that measures how long the wrapped block takes to execute.

    Attributes:
        start (float): The time when the context was entered.
    """

    def __enter__(self):
        """Records the start time when the context is entered.

        Returns:
            Timer: self, so it can be used as "with Timer() as t"."""
        self.start = time.time()
        return self  # I can do "with Timer() as t:" (I will not do with Timer() because the rest of my code will be unreachable)

    def __exit__(self, exc_type, exc_val, traceback):
        """Prints the elapsed time when the context is exited.
        Parameters:
            exc_type: The exception type
            exc_val: The exception value
            traceback: The traceback object"""
        elapsed = time.time() - self.start
        print(f"Elapsed time: {elapsed:.2f} seconds")


# Using a function
@contextlib.contextmanager
def timer() -> Generator[None, Any, None]:
    """Context manager that measures how long the wrapped block takes to execute.
    Yields:
        None: there is nothing after the yield, so this cannot be used as "with timer() as t": unlike the class,
        there is no object to bind.
    """
    try:
        start = time.time()
        yield
    finally:
        elapsed = time.time() - start
        print(f"Elapsed time: {elapsed:.2f} seconds")


with timer():
    time.sleep(1)
    raise Exception("Something bad happened")
