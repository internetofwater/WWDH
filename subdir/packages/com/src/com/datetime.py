# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from datetime import datetime, timezone


def datetime_from_iso(date_string: str) -> datetime:
    """
    Read in an ISO date string and return a datetime with a timezone; if no timezone is provided, assume UTC
    """

    serialized = datetime.fromisoformat(date_string)
    if serialized.tzinfo is None:
        serialized = serialized.replace(tzinfo=timezone.utc)
    return serialized
