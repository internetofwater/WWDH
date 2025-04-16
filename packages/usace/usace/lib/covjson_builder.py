# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from com.protocols.covjson import CovjsonBuilderProtocol
from usace.lib.locations_collection import LocationCollection


class CovjsonBuilder(CovjsonBuilderProtocol):
    def __init__(self, locationCollection: LocationCollection, datetime_: str): ...

    def render(self) -> dict: ...
