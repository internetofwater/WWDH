# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from typing import Literal, TypedDict


class ParameterDict(TypedDict):
    type: str
    description: dict[str, str]
    unit: dict
    observedProperty: dict


class CoverageRangeDict(TypedDict):
    type: Literal["NdArray"]
    dataType: Literal["float"]
    axisNames: list[str]
    shape: list[int]
    values: list[float | None]


class CoverageDict(TypedDict):
    type: Literal["Coverage"]
    domain: dict
    ranges: dict[str, CoverageRangeDict]
    domainType: Literal["PolygonSeries", "PointSeries"]


class CoverageCollectionDict(TypedDict):
    type: str
    parameters: dict[str, ParameterDict]
    referencing: list
    coverages: list[CoverageDict]
