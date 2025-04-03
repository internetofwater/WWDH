# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from com.helpers import await_
import pytest
import requests
import shapely.wkt
import shapely.geometry

from rise.lib.cache import RISECache
from rise.lib.helpers import merge_pages
from rise.lib.location import LocationResponseWithIncluded

"""This file is solely for sanity checks on the upstream repo or underlying libs to make sure that queries are performing as our understanding expects"""


@pytest.mark.upstream
def test_rise_include_parameter_order_matters():
    """
    RISE has odd behavior where the order of the include parameters matters
    """
    url1 = "https://data.usbr.gov/rise/api/location?include=catalogRecords.catalogItems&page=1&itemsPerPage=5"
    resp1 = requests.get(url1, headers={"accept": "application/vnd.api+json"})
    url1 = "https://data.usbr.gov/rise/api/location?include=catalogItems.catalogRecords&page=1&itemsPerPage=5"
    resp2 = requests.get(url1, headers={"accept": "application/vnd.api+json"})
    assert "included" in resp1.json().keys()
    assert "included" not in resp2.json().keys()


def test_rise_filter_by_param_list():
    """Make sure that rise is actually filtering by parameters correctly"""
    out812 = requests.get(
        "https://data.usbr.gov/rise/api/location?page=1&itemsPerPage=25&parameterId%5B%5D=812",
        headers={"accept": "application/vnd.api+json"},
    ).json()
    assert out812["meta"]["totalItems"] == 10
    assert len(out812["data"]) == out812["meta"]["totalItems"]

    out6 = requests.get(
        "https://data.usbr.gov/rise/api/location?page=1&itemsPerPage=25&parameterId%5B%5D=6",
        headers={"accept": "application/vnd.api+json"},
    ).json()
    assert out6["meta"]["totalItems"] == 13

    out_812_and_6 = requests.get(
        "https://data.usbr.gov/rise/api/location?page=1&itemsPerPage=25&parameterId%5B%5D=812&parameterId%5B%5D=6",
        headers={"accept": "application/vnd.api+json"},
    ).json()

    assert (
        out_812_and_6["meta"]["totalItems"]
        == out812["meta"]["totalItems"] + out6["meta"]["totalItems"]
    )


@pytest.mark.upstream
def test_rise_fetch_result_by_catalogItem():
    """Make sure that we can fetch a catalog item and get the associated result for it"""
    catalogItemUrl = "https://data.usbr.gov/rise/api/catalog-item/6811"
    response = requests.get(
        catalogItemUrl, headers={"accept": "application/vnd.api+json"}
    )
    assert response.ok, response.text
    assert response.json()["data"]
    resultUrl = "https://data.usbr.gov/rise/api/result/6811"
    response = requests.get(resultUrl, headers={"accept": "application/vnd.api+json"})
    assert response.ok, response.text
    assert response.json()["data"]["attributes"]


@pytest.mark.upstream
def test_rise_filter_result_by_date():
    """NOTE: Rise appears to do the datetime filter before the items per page filter so if you request a very long date range it will be very long, even with a small subset of items per page"""
    url = "https://data.usbr.gov/rise/api/result?page=1&itemsPerPage=25&dateTime%5Bbefore%5D=2017-01-02&dateTime%5Bafter%5D=2017-01-01"

    response = requests.get(url, headers={"accept": "application/vnd.api+json"})
    date: str = response.json()["data"][0]["attributes"]["dateTime"]
    assert date.startswith("2017-01-01")


@pytest.mark.upstream
def test_rise_filter_invalid_returns_nothing():
    invalid = "https://data.usbr.gov/rise/api/result?page=1&itemsPerPage=25&dateTime%5Bbefore%5D=2016-01-01&dateTime%5Bafter%5D=2017-01-01"

    response = requests.get(invalid, headers={"accept": "application/vnd.api+json"})
    assert response.json()["meta"]["totalItems"] == 0
    assert len(response.json()["data"]) == 0


@pytest.mark.upstream
def test_rise_filter_by_same_start_and_end():
    """Make sure that if we set the same start and end, we get all the dates matching the start of the iso timestamp"""
    url = "https://data.usbr.gov/rise/api/result?page=1&itemsPerPage=25&dateTime%5Bbefore%5D=2017-01-01&dateTime%5Bafter%5D=2017-01-01"

    response = requests.get(url, headers={"accept": "application/vnd.api+json"})
    assert response.json()["meta"]["totalItems"] != 0
    assert len(response.json()["data"]) != 0


@pytest.mark.upstream
def test_rise_can_include_catalog_items_in_location():
    url = "https://data.usbr.gov/rise/api/location/1?include=catalogRecords.catalogItems&page=1&itemsPerPage=5"
    response = requests.get(url, headers={"accept": "application/vnd.api+json"})

    resp = response.json()
    assert "included" in resp
    resp = resp["included"]
    assert len(resp) > 1
    resp = resp[0]
    assert "relationships" in resp
    resp = resp["relationships"]
    assert "catalogItems" in resp
    assert "location" in resp


@pytest.mark.upstream
def test_shapely_sanity_check():
    geo: dict = {
        "type": "Point",
        "coordinates": [-104.855255, 39.651378],
    }

    result = shapely.geometry.shape(geo)

    wkt = "POLYGON((-79 40,-79 38,-75 38,-75 41,-79 40))"

    wkt_parsed = shapely.wkt.loads(wkt)
    assert not wkt_parsed.contains(result)

    assert int(float("4530.000000")) == 4530
    location_6902_geom = {
        "type": "Polygon",
        "coordinates": [
            [
                [-111.49544, 36.94029],
                [-111.49544, 36.99597],
                [-111.47861, 36.99597],
                [-111.47861, 36.94029],
                [-111.49544, 36.94029],
            ]
        ],
    }

    point_inside = "POINT(-111.48 36.95)"
    point_inside = shapely.wkt.loads(point_inside)

    assert shapely.geometry.shape(location_6902_geom).contains(point_inside)

    point_outside = "POINT(-111.5 46.95)"
    point_outside = shapely.wkt.loads(point_outside)

    assert not shapely.geometry.shape(location_6902_geom).contains(point_outside)


@pytest.mark.upstream
def test_separate_pages_have_distinct_data():
    cache = RISECache()
    url1 = "https://data.usbr.gov/rise/api/location?include=catalogRecords.catalogItems?page=1&itemsPerPage=100"
    url2 = "https://data.usbr.gov/rise/api/location?include=catalogRecords.catalogItems&page=2&itemsPerPage=100"
    resp1 = cache.get_or_fetch(url1)
    resp2 = cache.get_or_fetch(url2)
    resp1 = await_(resp1)
    resp2 = await_(resp2)

    model1 = LocationResponseWithIncluded.model_validate(resp1)
    model2 = LocationResponseWithIncluded.model_validate(resp2)

    model2Ids = {location.attributes.id for location in model2.data}

    for location in model1.data:
        assert location.attributes.id not in model2Ids

    all_resp = merge_pages({url1: resp1, url2: resp2})

    model = LocationResponseWithIncluded.model_validate(all_resp)
    seenData = set()
    for loc in model.data:
        if loc.attributes.id in seenData:
            assert False, (
                f"Got a duplicate location with id {loc.attributes.id} and name {loc.attributes.locationName} after scanning {len(seenData)} out of {len(model.data)} locations in total"
            )
        seenData.add(loc.attributes.id)

    # this is used just to test that a particular location is in the data that was giving s issues; in the future it might not be here anymore
    assert 6811 in seenData
