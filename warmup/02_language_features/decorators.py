"""Decorator warmup.

@timer prints a function's runtime, and @retry(times=3) retries a failing function,
raising once all attempts are exhausted. Both are stacked as @retry above @timer on
a function that fails twice before succeeding, to show that the decorator order changes
what @timer actually measures.
"""

import functools
import time
from typing import Callable, Any

REQUIRED_SUCCESS_ATTEMPT = 3


def retry(times: int = 3) -> Callable:
    """Retry a function up to `times` times if it raises an exception.

    Parameters
    ----------
    times : int
        Number of attempts before giving up and raising RetryError.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> Any | None:
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(
                        f"Retrying {func.__name__} due to {e}. Attempt {i + 1} of {times}."
                    )
            return None

        return wrapper

    return decorator


def timer(func: Callable) -> Callable:
    """Print the runtime of the decorated function."""

    @functools.wraps(func)
    def wrapper(*args: object, **kwargs: object) -> Callable:
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        print(f"Finished {func.__name__}() in {run_time:.4f} secs")
        return value

    return wrapper


attempts = 0


@timer
@retry(times=3)
def part4() -> str:
    """Fail twice, then succeed on the third attempt.

    Uses a module-level `attempts` counter (declared global here) to track
    state across the repeated calls made by @retry.
    """
    global attempts
    attempts += 1
    print(f"Attempt {attempts}")
    if attempts < REQUIRED_SUCCESS_ATTEMPT:
        error_message = f"Attempt {attempts} failed"
        raise ValueError(error_message)
    return "success"


result = part4()
print("Result:", result)
