# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import asyncio
import logging
from typing import Any, Coroutine, Literal, Optional, Tuple, Type, TypedDict
from annotated_types import T
from com.datetime import datetime_from_iso
from com.env import iodh_event_loop
from pydantic import BaseModel
from rise.lib.types.helpers import ZType
import datetime

import shapely
from pygeoapi.provider.base import ProviderQueryError

LOGGER = logging.getLogger(__name__)

OAFFieldsMapping = dict[
    str, dict[Literal["type"], Literal["number", "string", "integer"]]
]


EDRField = TypedDict(
    "EDRField",
    {
        "type": str,
        "title": str,
        "description": str,
        "x-ogc-unit": str,
    },
)

EDRFieldsMapping = dict[str, EDRField]


def await_(coro: Coroutine[Any, Any, T]) -> T:
    """
    await an asyncio coroutine, ensuring it works even if an event loop is already running.
    """
    return asyncio.run_coroutine_threadsafe(coro, loop=iodh_event_loop).result()


def parse_z(z: str) -> Optional[Tuple[ZType, list[int]]]:
    """Parse a z value in the format required by the OGC EDR spec"""
    if not z:
        return None
    if z.startswith("R") and len(z.split("/")) == 3:
        z = z.replace("R", "")
        interval = z.split("/")
        if len(interval) != 3:
            raise ProviderQueryError(f"Invalid z interval: {z}")
        steps = int(interval[0])
        start = int(interval[1])
        step_len = int(interval[2])
        return (
            ZType.ENUMERATED_LIST,
            list(range(start, start + (steps * step_len), step_len)),
        )
    elif "/" in z and len(z.split("/")) == 2:
        start = int(z.split("/")[0])
        stop = int(z.split("/")[1])

        return (ZType.RANGE, [start, stop])
    elif "," in z:
        try:
            return (ZType.ENUMERATED_LIST, list(map(int, z.split(","))))
        # if we can't convert to int, it's invalid
        except ValueError:
            raise ProviderQueryError(f"Invalid z value: {z}")
    else:
        try:
            return (ZType.SINGLE, [int(z)])
        except ValueError:
            raise ProviderQueryError(f"Invalid z value: {z}")


def parse_date(
    datetime_: str,
) -> datetime.datetime | tuple[datetime.datetime, datetime.datetime]:
    """Parses an EDR formatted datetime string into a datetime object"""
    dateRange = datetime_.split("/")

    if len(dateRange) == 2:
        start, end = dateRange

        # python does not accept Z at the end of the datetime even though that is a valid ISO 8601 datetime
        if start.endswith("Z"):
            start = start.replace("Z", "+00:00")

        if end.endswith("Z"):
            end = end.replace("Z", "+00:00")

        start = (
            datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
            if start == ".."
            else datetime_from_iso(start)
        )
        end = (
            datetime.datetime.max.replace(tzinfo=datetime.timezone.utc)
            if end == ".."
            else datetime_from_iso(end)
        )

        if start > end:
            raise ProviderQueryError(
                "Start date must be before end date but got {} and {}".format(
                    start, end
                )
            )

        return (start, end)
    else:
        return datetime_from_iso(datetime_)


def parse_bbox(
    bbox: Optional[list],
) -> Tuple[Optional[shapely.geometry.base.BaseGeometry], Optional[str]]:
    minz, maxz = None, None

    if not bbox:
        return None, None
    else:
        bbox = list(map(float, bbox))

    if len(bbox) == 4:
        minx, miny, maxx, maxy = bbox
        return shapely.geometry.box(minx, miny, maxx, maxy), None
    elif len(bbox) == 6:
        minx, miny, minz, maxx, maxy, maxz = bbox
        return shapely.geometry.box(minx, miny, maxx, maxy), (f"{minz}/{maxz}")
    else:
        raise ProviderQueryError(
            f"Invalid bbox; Expected 4 or 6 points but {len(bbox)} values"
        )


def get_oaf_fields_from_pydantic_model(model: Type[BaseModel]) -> OAFFieldsMapping:
    """Given a pydantic model, return a mapping of the fields to their data types"""
    pydanticFields = model.model_fields
    fields: OAFFieldsMapping = {}
    for fieldName in pydanticFields.keys():
        dataType: Literal["number", "string", "integer"]

        aliasName = pydanticFields[fieldName].alias
        if aliasName:
            name = aliasName
        else:
            name = fieldName

        if "str" in str(pydanticFields[fieldName].annotation):
            dataType = "string"
        elif "int" in str(pydanticFields[fieldName].annotation):
            dataType = "integer"
        elif "float" in str(pydanticFields[fieldName].annotation):
            dataType = "number"
        else:
            LOGGER.warning(
                f"Skipping field '{name}' with unmappable data type {pydanticFields[fieldName].annotation}"
            )
            continue

        fields[name] = {"type": dataType}
    return fields
