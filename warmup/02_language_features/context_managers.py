"""Context manager warmup.

A Timer implemented two ways: a class with __enter__ and __exit__, and a function
with @contextlib.contextmanager. Both print the elapsed time even when the wrapped
block raises an exception.

"""

import contextlib
import time
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from collections.abc import Generator


class Timer:
    """Context manager that measures how long the wrapped block takes to execute.

    Attributes
    ----------
    start : float
        The time when the context was entered.
    """

    def __enter__(self) -> Self:
        """Record the start time when the context is entered.

        Returns
        -------
        Timer
            self, so it can be used as "with Timer() as t".
        """
        self.start = time.time()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Print the elapsed time when the context is exited.

        Parameters
        ----------
        exc_type : type[BaseException] | None
            The exception type, if one was raised.
        exc_val : BaseException | None
            The exception value, if one was raised.
        """
        elapsed = time.time() - self.start
        print(f"Elapsed time: {elapsed:.2f} seconds")


@contextlib.contextmanager
def timer() -> Generator[None]:
    """Measure how long the wrapped block takes to execute.

    Yields
    ------
    None
        There is nothing after the yield, so this cannot be used as
        "with timer() as t": - unlike the class, there is no object to bind.
    """
    try:
        start = time.time()
        yield
    finally:
        elapsed = time.time() - start
        print(f"Elapsed time: {elapsed:.2f} seconds")


class Example(Exception):
    """Raised to prove that clean-up still runs when the with block fails."""

    def __init__(self) -> None:
        super().__init__("Something bad happened")


with timer():
    time.sleep(1)
    raise Example()
