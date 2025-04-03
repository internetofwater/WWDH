# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import functools
import inspect
import os

from com.env import TRACER as GLOBAL_TRACER


def otel_trace():
    """Decorator to automatically set the span name using the file and function name."""

    def decorator(func):
        filename = os.path.splitext(os.path.basename(inspect.getfile(func)))[0]
        span_name = f"{filename}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with GLOBAL_TRACER.start_as_current_span(span_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator
