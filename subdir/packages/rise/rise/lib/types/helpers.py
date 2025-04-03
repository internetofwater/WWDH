# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from enum import Enum, auto


class ZType(Enum):
    """An enum for representing elevation values as allowed by the EDR spec"""

    SINGLE = auto()
    # Every value between two values
    RANGE = auto()
    # An enumerated list that the value must be in
    ENUMERATED_LIST = auto()
