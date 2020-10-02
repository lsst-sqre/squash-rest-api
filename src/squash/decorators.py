"""Implement the time_this decorator."""

__all__ = ["time_this"]

import time
from functools import wraps

from flask import current_app as app


def time_this(func):
    """Time function or method execution."""

    @wraps(func)
    def wrapper(*args):
        start = time.time()
        result = func(*args)
        end = time.time()
        app.logger.debug(
            "Time for {}: {:.4f}s".format(func.__name__, end - start)
        )

        return result

    return wrapper
