# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from com.helpers import await_
from pytest import FixtureRequest
import pytest
from rise.lib.cache import RISECache
from rise.lib.helpers import merge_pages
from rise.lib.location import LocationResponse
from rise.rise import RiseProvider
from rise.rise_edr import RiseEDRProvider
from pygeoapi.provider.base import ProviderItemNotFoundError


def test_get_all_pages_for_items():
    cache = RISECache()
    all_location_responses = await_(
        cache.get_or_fetch_all_pages(RiseEDRProvider.LOCATION_API)
    )
    merged_response = merge_pages(all_location_responses)
    response = LocationResponse(**merged_response)
    assert response


@pytest.fixture()
def oaf_config(request: type[FixtureRequest]):
    config = {
        "name": "RISE_EDR_Provider",
        "type": "feature",
        "title_field": "name",
        "cache": "redis",
        "data": "https://data.usbr.gov/rise/api/",
    }
    return config


def test_item(oaf_config: dict):
    """Test what happens if we request one item; make sure the geojson is valid"""
    p = RiseProvider(oaf_config)
    out = p.items(itemId="1")
    assert out["type"] == "Feature"
    assert out["id"] == 1

    with pytest.raises(Exception):
        out = p.items(itemId="__INVALID")

    out = p.items(limit=10)
    assert out["type"] == "FeatureCollection"
    assert len(out["features"]) == 10


def test_item_that_doesnt_exist(oaf_config: dict):
    p = RiseProvider(oaf_config)
    with pytest.raises(ProviderItemNotFoundError):
        p.items(itemId="9999999999999999999999999")


def test_offset(oaf_config: dict):
    p = RiseProvider(oaf_config)
    out1 = p.items(offset=1, limit=10)
    assert out1["type"] == "FeatureCollection"
    assert len(out1["features"]) == 10
    out2 = p.items(offset=0, limit=10)
    assert out2["type"] == "FeatureCollection"
    assert len(out2["features"]) == 10
    assert out1["features"] != out2["features"]
    assert out1["features"][0] == out2["features"][1]


def test_select_properties(oaf_config: dict):
    """Make sure select properties returns features but filters out which properties are returned in the requested features"""
    p = RiseProvider(oaf_config)
    id1Full = p.items(itemId="1")
    assert id1Full["type"] == "Feature"
    id1WithDummyProperties = p.items(itemId="1", select_properties=["DUMMY_PROPERTY"])
    assert id1WithDummyProperties["type"] == "Feature"
    assert id1Full["geometry"] == id1WithDummyProperties["geometry"]
    assert id1Full["id"] == id1WithDummyProperties["id"]
    assert id1Full["properties"] != id1WithDummyProperties["properties"]
    assert id1WithDummyProperties["properties"] == {}, (
        "If we select a property that doesn't exist, it should return an empty dict"
    )

    assert "locationName" in p._fields, "fields were not set properly"
    outWithSelection = p.items(
        select_properties=["locationName"], properties=[("_id", "1")]
    )
    assert outWithSelection["type"] == "FeatureCollection"
    out = p.items(itemId="1")
    assert out["type"] == "Feature"
    assert (
        outWithSelection["features"][0]["properties"]["locationName"]
        == out["properties"]["locationName"]
    )
    assert len(outWithSelection["features"][0]["properties"]) == 1

    # make sure that we can select multiple properties where one exists and one doesn't
    propertyThatIsNullInLocation1 = "locationParentId"
    propertyThatExistsInLocation1 = "locationDescription"
    outWithSelection = p.items(
        select_properties=[
            propertyThatIsNullInLocation1,
            propertyThatExistsInLocation1,
        ],
        properties=[("_id", "1")],
    )
    assert outWithSelection["type"] == "FeatureCollection"
    assert (
        propertyThatExistsInLocation1 in outWithSelection["features"][0]["properties"]
    )


def test_properties_key_value_mapping(oaf_config: dict):
    p = RiseProvider(oaf_config)
    out = p.items(
        properties=[("locationName", "DUMMY"), ("locationDescription", "DUMMY")],
    )
    assert out["type"] == "FeatureCollection"
    assert len(out["features"]) == 0

    out = p.items(
        properties=[("_id", "1"), ("locationDescription", "DUMMY")],
    )
    assert out["type"] == "FeatureCollection"
    assert len(out["features"]) == 0, (
        "If one property is invalid but one is valid, the entire feature should still be filtered out"
    )

    with pytest.raises(AssertionError):
        _ = p.items(
            itemId="1",
            properties=[("_id", "1"), ("locationName", "DUMMY")],
        )

    featureCollectionJustID1 = p.items(properties=[("_id", "1")])
    assert featureCollectionJustID1["type"] == "FeatureCollection"
    assert len(featureCollectionJustID1["features"]) == 1
    assert featureCollectionJustID1["features"][0] == p.items(
        itemId="1",
    ), "Filtering by a property 'id' should be the same as filtering by the item id"


def test_sortby(oaf_config: dict):
    p = RiseProvider(oaf_config)
    out = p.items(sortby=[{"property": "locationName", "order": "+"}])
    assert out["type"] == "FeatureCollection"

    for i, feature in enumerate(out["features"], start=1):
        prev = out["features"][i - 1]
        curr = feature
        assert prev["properties"]["locationName"] <= curr["properties"]["locationName"]

    # by selecting locationDescription, we know that the value is never None
    # and thus we can always compare to verify order
    out = p.items(
        select_properties=["locationDescription"],
        sortby=[{"property": "locationDescription", "order": "-"}],
    )
    assert out["type"] == "FeatureCollection"
    for i, feature in enumerate(out["features"], start=1):
        prev = out["features"][i - 1]
        curr = feature
        currDescription, prevDescription = (
            curr["properties"]["locationDescription"],
            prev["properties"]["locationDescription"],
        )
        if (
            not currDescription or not prevDescription
        ):  # it could be null which in that case we can't compare them
            continue
        assert (
            prev["properties"]["locationDescription"]
            >= curr["properties"]["locationDescription"]
        )
        assert len(curr["properties"]) == 1


def test_resulttype_hits(oaf_config: dict):
    p = RiseProvider(oaf_config)
    out = p.items(resulttype="hits")
    assert out["type"] == "FeatureCollection"
    assert len(out["features"]) == 0
    assert out["type"] == "FeatureCollection"
    # make sure numberMatched is greater than 0
    # we can't compare against a constant because it could
    # change but it should always be greater than 0
    assert "numberMatched" in out
    assert out["numberMatched"] > 0


def test_skip_geometry(oaf_config: dict):
    p = RiseProvider(oaf_config)
    out = p.items(itemId="1", skip_geometry=True)
    assert out["type"] == "Feature"
    assert out["geometry"] is None
    outWithoutSkip = p.items(itemId="1")
    assert outWithoutSkip["type"] == "Feature"
    assert outWithoutSkip["geometry"]


def test_getting_a_feature_without_timeseries(oaf_config: dict):
    """Make sure that itemStructureId=1 is not applied; make sure we can get features even if they don't have timeseries data"""
    p = RiseProvider(oaf_config)
    out = p.items(itemId="7165")
    assert out["type"] == "Feature"
