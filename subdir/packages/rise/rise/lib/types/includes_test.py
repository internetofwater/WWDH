# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import pytest
import requests
from rise.lib.location import LocationResponse, LocationResponseWithIncluded


@pytest.fixture
def locationRespFixture():
    url = "https://data.usbr.gov/rise/api/location/1?include=catalogRecords.catalogItems&page=1&itemsPerPage=5"
    resp = requests.get(url, headers={"accept": "application/vnd.api+json"})
    assert resp.ok, resp.text
    return resp.json()


def test_location_parse(locationRespFixture: dict):
    serializedLocation = LocationResponse.model_validate(locationRespFixture)
    assert serializedLocation

    serializedWithIncluded = LocationResponseWithIncluded.model_validate(
        locationRespFixture
    )
    assert serializedWithIncluded
