import contextlib
import time


# Using a class
class Timer:
    def __init__(self):
        pass
    def __enter__(self):
        self.start = time.time()
        return self #I can do "with Timer() as t: (I will not do with Timer() because the rest of my code will be unreachable)
    def __exit__(self, exc_type, exc_val, traceback):
        elapsed = time.time() - self.start
        print(f"Elapsed time: {elapsed:.2f} seconds")

# Using a function
@contextlib.contextmanager
def timer():
    try:
        start = time.time()
        yield
    finally:
        elapsed = time.time() - start
        print(f"Elapsed time: {elapsed:.2f} seconds")

with timer():
    time.sleep(1)
    raise Exception("Something bad happened")
