# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from typing import Literal, NotRequired, Optional, TypedDict

from com.helpers import OAFFieldsMapping
import geojson_pydantic
from pygeoapi.provider.base import ProviderQueryError
from typing import assert_never


class SortDict(TypedDict):
    """
    This represents the schema of the property sort that a user
    can run in the items/ query
    """

    property: str
    order: Literal["+", "-"]


class GeojsonFeatureDict(TypedDict):
    """
    A dict representation of a single Geojson Feature as returned by
    items/{id}
    """

    type: Literal["Feature"]
    geometry: Optional[dict]
    properties: dict
    id: int | str


class GeojsonFeatureCollectionDict(TypedDict):
    """A dict reprsentation of a GeoJSON FeatureCollection that is returned from OAF items/ queries"""

    type: Literal["FeatureCollection"]
    features: list[GeojsonFeatureDict]
    # numberMatched is not required because it is only returned when resulttype=hits
    numberMatched: NotRequired[int]


def sort_by_properties_in_place(
    geojson_features: list[geojson_pydantic.Feature], sortby: list[SortDict]
) -> None:
    """
    Sort a GeojsonFeatureCollectionDict by the given keys
    """
    if len(geojson_features) <= 1 or not sortby:
        return

    for sort_criterion in reversed(sortby):
        sort_prop = sort_criterion["property"]
        sort_order = sort_criterion["order"]
        reverse_sort = sort_order == "-"

        # Define a key function that places None values at the end for ascending order
        # and at the beginning for descending order.
        def sort_key(f):
            value = (f.properties or {}).get(sort_prop, None)
            return (
                (value is None, value)
                if not reverse_sort
                else (value is not None, value)
            )

        # Sort in-place using the key function
        geojson_features.sort(key=sort_key, reverse=reverse_sort)


def all_properties_found_in_feature(
    location_feature: geojson_pydantic.Feature,
    properties_to_look_for: list[tuple[str, str]],
    fields_mapping: OAFFieldsMapping,
) -> bool:
    """Check if all properties to look for are found in the geojson feature. Use the
    field mapper to determine the type of each property when deserializing
    """
    # We rely on fields_mapping to know how to cast each property
    if not fields_mapping:
        raise ProviderQueryError(
            "You must supply a `fields_mapping` if you want to filter by properties"
        )
    assert location_feature.properties

    found_list: list[bool] = []
    for prop_name, prop_value in properties_to_look_for:
        datatype = fields_mapping.get(prop_name)
        if not datatype:
            raise ProviderQueryError(
                f"Could not find a property '{prop_name}' in {fields_mapping} and thus we cannot deserialize it"
            )

        # Convert the string passed in the query to the correct Python type
        match datatype["type"]:
            case "number":
                prop_value = float(prop_value)
            case "integer":
                prop_value = int(prop_value)
            case "string":
                prop_value = str(prop_value)
            case _:
                assert_never(datatype)

        found_list.append(location_feature.properties.get(prop_name) == prop_value)

    # If *all* requested property-value pairs match, keep the feature
    return all(found_list)


def filter_out_properties_not_selected(
    serialized_feature: geojson_pydantic.Feature, select_properties: list[str]
):
    """Given a a geojson feature, remove any properties that are not in the list of selected properties"""
    thingsToRemove = set()
    assert serialized_feature.properties
    for p in serialized_feature.properties:
        if p not in select_properties:
            thingsToRemove.add(p)

    for i in sorted(thingsToRemove, reverse=True):
        del serialized_feature.properties[i]
