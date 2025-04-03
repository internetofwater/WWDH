# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from typing import Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat


class PageLinks(BaseModel):
    first: Optional[str] = None
    last: Optional[str] = None
    self: str
    next: Optional[str] = None
    prev: Optional[str] = None


class PointCoordinates(BaseModel):
    type: Literal["Point"]
    coordinates: tuple[
        FiniteFloat, FiniteFloat
    ]  # Expecting exactly two values: [longitude, latitude]


class PolygonCoordinates(BaseModel):
    type: Literal["Polygon"]
    coordinates: list[
        list[list[FiniteFloat]]
    ]  # A list of linear rings (each ring is a list of [longitude, latitude] pairs)


class LineStringCoordinates(BaseModel):
    type: Literal["LineString"]
    coordinates: list[list[FiniteFloat]]


class LocationDataAttributes(BaseModel):
    """
    The `attributes:` key within each `data:` key for location/
    Thus, located at the following nesting:
        data:
            attributes:
    """

    model_config = ConfigDict(extra="forbid")

    # We use an alias here to map the _id field to the id field since the _ in the name causes issues
    # https://stackoverflow.com/questions/59562997/how-to-parse-and-read-id-field-from-and-to-a-pydantic-model
    id: int = Field(..., alias="_id")

    locationParentId: Optional[int]
    locationName: str
    locationDescription: Optional[str]
    locationStatusId: int

    # the "type" field tells us whether to validate as a Point or a Polygon
    locationCoordinates: Union[
        PointCoordinates, PolygonCoordinates, LineStringCoordinates
    ] = Field(discriminator="type")
    elevation: Optional[float] = None
    createDate: str
    updateDate: str
    horizontalDatum: dict
    locationGeometry: dict
    timezone: Optional[str] = None
    verticalDatum: Optional[dict]
    locationTags: list[dict]
    relatedLocationIds: Optional[list[int]]
    projectNames: list[str]
    locationTypeName: str
    timezoneName: Optional[str] = None
    timezoneOffset: Optional[float] = None
    locationRegionNames: list[str]
    locationUnifiedRegionNames: list[str]


class LocationData(BaseModel):
    """the `data:` key of the location response"""

    id: str
    type: Literal["Location"]
    attributes: LocationDataAttributes
