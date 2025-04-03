# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import requests
import pytest

from rise.lib.helpers import merge_pages
from rise.lib.location import LocationResponseWithIncluded
from rise.rise_edr import RiseEDRProvider
import datetime
from pygeoapi.provider.base import ProviderQueryError


@pytest.fixture()
def edr_config():
    config = {
        "name": "RISE_EDR_Provider",
        "type": "edr",
        "cache": "redis",
        "url": "https://data.usbr.gov/rise/api/",
    }
    return config


def test_location_locationId(edr_config: dict):
    includedItems = requests.get(
        "https://data.usbr.gov/rise/api/location/1?include=catalogRecords.catalogItems"
    ).json()["included"]
    catalogItems = len(
        [item["id"] for item in includedItems if item["type"] == "CatalogItem"]
    )

    p = RiseEDRProvider()
    out = p.locations(location_id="1", format_="covjson")
    assert "coverages" in out
    assert len(out["coverages"]) == catalogItems, (
        "There must be the same number of catalogItems as there are coverages"
    )

    geojson_out = p.locations(location_id="1", format_="geojson")
    assert geojson_out["type"] == "Feature"
    assert "id" in geojson_out
    assert geojson_out["id"] == 1


def test_invalid_location_id(edr_config: dict):
    p = RiseEDRProvider()
    with pytest.raises(ProviderQueryError):
        p.locations(location_id="__INVALID", format_="geojson")


def test_get_fields(edr_config: dict):
    p = RiseEDRProvider()
    fields = p.get_fields()

    # test to make sure a particular field is there
    assert fields["2"]["title"] == "Lake/Reservoir Elevation"

    assert requests.get(
        "https://data.usbr.gov/rise/api/parameter?page=1&itemsPerPage=25",
        headers={"accept": "application/vnd.api+json"},
    ).json()["meta"]["totalItems"] == len(fields)


def test_get_or_fetch_all_param_filtered_pages(edr_config: dict):
    p = RiseEDRProvider()
    params = ["812", "6"]
    bothparams = p.cache.get_or_fetch_all_param_filtered_pages(params)
    merge_resp = merge_pages(bothparams)
    assert len(merge_resp["data"]) == 10 + 13

    params = ["6"]
    oneparam = p.cache.get_or_fetch_all_param_filtered_pages(params)
    one_resp = merge_pages(oneparam)
    assert len(one_resp["data"]) == 13

    assert len(merge_resp["data"]) > len(one_resp["data"]), (
        "both params should have more data than one param"
    )

    allparams = p.cache.get_or_fetch_all_param_filtered_pages()
    model = LocationResponseWithIncluded.from_api_pages(allparams)
    seenData = set()
    for loc in model.data:
        assert loc.attributes.id not in seenData, (
            f"Got a duplicate location with id {loc.attributes.id} and name {loc.attributes.locationName} after scanning {len(seenData)} out of {len(model.data)} locations in total"
        )
        seenData.add(loc.attributes.id)


def test_location_select_properties(edr_config: dict):
    """Make sure that we can filter locations based on their associated property IDs"""
    # Currently in pygeoapi we use the word "select_properties" as the
    # keyword argument. This is hold over from OAF it seems.
    p = RiseEDRProvider()
    lakeReservoirStorage = "3"
    texasID291 = "291"
    out = p.locations(location_id=texasID291, select_properties=[lakeReservoirStorage])
    assert "coverages" in out
    # with select properties you drop any coverages that don't have that property and since there is only one coverage with that property, we should only get one
    # and the others should be dropped
    assert len(out["coverages"]) == 1, (
        "We expect to have only lake reservoir storage for this location since we selected that property"
    )

    outAsGeojson = p.locations(select_properties=[lakeReservoirStorage])
    found = False
    for feature in outAsGeojson["features"]:  # type: ignore
        if feature["id"] == int(texasID291):
            found = True
    assert found


def test_location_select_properties_with_id_filter(edr_config: dict):
    p = RiseEDRProvider()
    out = p.locations(location_id="1", select_properties=["3"], format_="geojson")
    assert out["type"] == "Feature"


def test_location_datetime(edr_config: dict):
    p = RiseEDRProvider()

    out = p.locations(location_id="1536", datetime_="2017-01-01/2018-01-01")

    start = datetime.datetime.fromisoformat("2017-01-01T00:00:00+00:00")
    end = datetime.datetime.fromisoformat("2018-01-01T00:00:00+00:00")
    assert "coverages" in out
    for param in out["coverages"]:
        for time_val in param["domain"]["axes"]["t"]["values"]:
            assert start <= datetime.datetime.fromisoformat(time_val) <= end


def test_area(edr_config: dict):
    p = RiseEDRProvider()

    secondQueryForQeorgeWestTexasID291 = "POLYGON ((-99.717407 28.637568, -97.124634 28.608637, -97.020264 27.210671, -100.184326 26.980829, -101.392822 28.139816, -99.717407 28.637568)))"
    response = p.area(
        wkt=secondQueryForQeorgeWestTexasID291,
    )
    coverages = response["coverages"]
    assert len(coverages) == 2
    for coverage in coverages:
        assert coverage["domain"]["axes"]["x"]["values"][0] == -98.1667, (
            "Both coverages should have the same x value since they are on the same location"
        )
        assert coverage["domain"]["axes"]["y"]["values"][0] == 28.4667
    assert len(response["coverages"]) == 2, (
        "There should be 2 coverages unless an additional location was added"
    )
    assert response["coverages"][0]["ranges"]["Lake/Reservoir Storage"]
    assert response["coverages"][1]["ranges"]["Lake/Reservoir Elevation"]

    # make sure that we can get the same data with a different geospatial query as long as the same data is in the bbox
    secondQueryForQeorgeWestTexasID291 = "POLYGON ((-98.66272 28.062286, -97.756348 28.062286, -97.756348 28.688178, -98.66272 28.688178, -98.66272 28.062286))"
    response2 = p.area(
        wkt=secondQueryForQeorgeWestTexasID291,
    )

    assert response2 == response

    areaInMontanaWithDataID424 = "POLYGON ((-109.204102 47.010226, -104.655762 47.010226, -104.655762 49.267805, -109.204102 49.267805, -109.204102 47.010226))"

    response = p.area(
        wkt=areaInMontanaWithDataID424,
    )
    assert len(response["coverages"]) == 4, (
        "Expected to return 1 location with 4 datastreams and thus 4 coverages"
    )

    dummyAreaInTheOcean = "POLYGON ((-44.296875 27.059126, -23.203125 27.059126, -23.203125 40.84706, -44.296875 40.84706, -44.296875 27.059126))"

    response = p.area(
        wkt=dummyAreaInTheOcean,
    )
    assert len(response["coverages"]) == 0, (
        "Since the area is in the ocean, no data should be returned"
    )


def test_cube(edr_config: dict):
    p = RiseEDRProvider()
    bboxCoveringTexasID291 = [-98.5, 26.5, -95.5, 29.5]
    result = p.cube(bbox=bboxCoveringTexasID291)
    assert (
        len(result["coverages"]) == 2
    )  # there are 2 coverages since location/291 has 2 datastreams

    result = p.cube(bbox=[0, 0, 0, 0])
    assert len(result["coverages"]) == 0


def test_polygon_output(edr_config: dict):
    """make sure that a location which has a polygon in it doesn't throw an error"""
    # location id 3526 is a polygon
    p = RiseEDRProvider()

    out = p.locations(location_id="3526", format_="covjson")
    assert out["type"] == "CoverageCollection"
