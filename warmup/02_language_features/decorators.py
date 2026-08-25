"""Decorator warmup: @timer (prints runtime) and @retry(times=3), retries on exceptions, raising after all attempts
fail), stacked as @retry above @timer on a function that fails 2 times before succeeding - used to show that decorator
order changes what @timer measures."""

import functools
import time
from typing import Callable


def retry(times: int = 3) -> Callable:
    """Retry a function if it raises an exception. If all attempts fail, raise an exception.
    @params times: number of times to retry the function before raising an exception"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Callable:
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(
                        f"Retrying {func.__name__} due to {e}. Attempt {i + 1} of {times}."
                    )
            raise Exception(f"All {times} attempts failed.")

        return wrapper

    return decorator


def timer(func: Callable) -> Callable:
    """Print the runtime of the decorated function"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
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
def part4():
    """Part 4 of the decorator task. I use a list to keep track of the state between calls of part4(). attempts = 0
    won't work because Python would treat it as a variable and not a list (I'm mutating the list contents, not
    reassigning it)."""
    global attempts
    attempts += 1
    print(f"Attempt {attempts}")
    if attempts < 3:
        time.sleep(1)
        raise ValueError(f"Attempt {attempts} failed")
    return "success"


result = part4()
print("Result:", result)
