"""Decorator warmup: @timer (prints runtime) and @retry(times=3), retries on exceptions, raising after all attempts
fail), stacked as @retry above @timer on a function that fails 2 times before succeeding - used to show that decorator
order changes what @timer measures."""

import functools
import time

attempts = [0]

def retry(times=3):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Retrying {func.__name__} due to {e}. Attempt {i + 1} of {times}.")
            raise Exception(f"All {times} attempts failed.")
        return wrapper
    return decorator

def timer(func):
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

@retry(times=3)
@timer
def part4():
    """Part 4 of the decorator task. I use a list to keep track of the state between calls of part4(). attempts = 0
    won't work because Python would treat it as a variable and not a list (I'm mutating the list contents, not
    reassigning it)."""
    attempts[0] += 1
    print(f"Attempt {attempts[0]}")
    if attempts[0] < 3:
        time.sleep(1)
        raise ValueError(f"Attempt {attempts[0]} failed")
    return "success"

result = part4()
print("Result:", result)