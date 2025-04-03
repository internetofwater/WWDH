# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from snotel.snotel import SnotelProvider


conf = {
    "name": "snotel",
    "title": "Snotel",
    "description": "Snotel",
    "type": "edr",
    "data": "https://wcc.sc.egov.usda.gov/awdbRestApi/swagger-ui/index.html",
}


def test_snotel_select_properties():
    p = SnotelProvider(conf)
    out = p.items(select_properties=["name", "networkCode"])
    assert out["type"] == "FeatureCollection"
    for item in out["features"]:
        assert "name" in item["properties"]
        assert "networkCode" in item["properties"]
        assert len(item["properties"]) == 2


def test_snotel_filter_by_property_value():
    p = SnotelProvider(conf)
    out = p.items(properties=[("networkCode", "DUMMY")])
    assert out["type"] == "FeatureCollection"
    assert len(out["features"]) == 0
    out = p.items(properties=[("networkCode", "SNTL")])
    assert out["type"] == "FeatureCollection"
    assert len(out["features"]) > 0


def test_snotel_filter_by_multiple_property_values():
    p = SnotelProvider(conf)
    # make sure if we filter by a bad value it returns nothing
    out = p.items(properties=[("networkCode", "DUMMY"), ("networkCode", "SNTL")])
    assert out["type"] == "FeatureCollection"
    assert len(out["features"]) == 0
    # make sure order of properties doesn't matter
    out = p.items(properties=[("networkCode", "SNTL"), ("networkCode", "DUMMY")])
    assert out["type"] == "FeatureCollection"
    assert len(out["features"]) == 0
    # make sure we can filter by multiple properties
    out = p.items(properties=[("networkCode", "SNTL"), ("name", "Albro Lake")])
    assert out["type"] == "FeatureCollection"
    assert len(out["features"]) == 1


def test_filter_by_property_is_same_as_filter_by_id():
    p = SnotelProvider(conf)
    idForAdinMtnInCalifornia = 301
    out1 = p.items(itemId=f"{idForAdinMtnInCalifornia}")
    assert out1["type"] == "Feature"
    out2 = p.items(properties=[("stationId", f"{idForAdinMtnInCalifornia}")])
    assert out2["type"] == "FeatureCollection"
    assert len(out2["features"]) == 1
    assert out1 == out2["features"][0]


def test_filter_by_property_and_itemid_at_once():
    p = SnotelProvider(conf)
    idForAdinMtnInCalifornia = 301
    out1 = p.items(
        itemId=f"{idForAdinMtnInCalifornia}", properties=[("networkCode", "SNTL")]
    )
    assert out1["type"] == "Feature"
    assert out1["properties"]["networkCode"] == "SNTL"
    assert out1["properties"]["stationId"] == str(idForAdinMtnInCalifornia)
