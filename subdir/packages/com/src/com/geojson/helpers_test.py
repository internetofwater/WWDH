# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from com.geojson.helpers import (
    SortDict,
    filter_out_properties_not_selected,
    sort_by_properties_in_place,
)
import geojson_pydantic


def test_sort_by_properties_in_place():
    geojson: list[geojson_pydantic.Feature] = [
        geojson_pydantic.Feature(
            **{
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [1, 2]},
                "properties": {"a": 1, "b": 2},
            }
        ),
        geojson_pydantic.Feature(
            **{
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [3, 4]},
                "properties": {"a": 3, "b": 4},
            }
        ),
        geojson_pydantic.Feature(
            **{
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [5, 6]},
                "properties": {"a": 5, "b": 6},
            }
        ),
    ]

    sortby: list[SortDict] = [{"property": "a", "order": "+"}]

    sort_by_properties_in_place(geojson, sortby)
    assert geojson[0].properties
    assert geojson[0].properties["a"] == 1
    assert geojson[1].properties
    assert geojson[1].properties["a"] == 3
    assert geojson[2].properties
    assert geojson[2].properties["a"] == 5
    sortby = [{"property": "a", "order": "-"}]
    sort_by_properties_in_place(geojson, sortby)
    assert geojson[0].properties
    assert geojson[0].properties["a"] == 5
    assert geojson[1].properties
    assert geojson[1].properties["a"] == 3
    assert geojson[2].properties
    assert geojson[2].properties["a"] == 1


def test_filter_out_properties_not_selected():
    geojson: geojson_pydantic.Feature = geojson_pydantic.Feature(
        **{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [1, 2]},
            "properties": {"a": 1, "b": 2},
        }
    )
    select_properties = ["a", "b"]
    filter_out_properties_not_selected(geojson, select_properties)
    assert geojson.properties
    assert geojson.properties["a"] == 1
    assert geojson.properties["b"] == 2

    geojson: geojson_pydantic.Feature = geojson_pydantic.Feature(
        **{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [1, 2]},
            "properties": {"a": 1, "b": 2, "c": [3], "d": {"e": 4}},
        }
    )
    select_properties = ["a", "b"]
    filter_out_properties_not_selected(geojson, select_properties)
    assert geojson.properties
    assert geojson.properties["a"] == 1
    assert geojson.properties["b"] == 2
    assert "c" not in geojson.properties
