# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import pytest
import requests

from rise.lib.cache import RISECache
from rise.lib.location import LocationResponseWithIncluded
from rise.lib.add_results import LocationResultBuilder


@pytest.fixture
def locationRespFixture():
    url = "https://data.usbr.gov/rise/api/location/1?include=catalogRecords.catalogItems&page=1&itemsPerPage=5"
    resp = requests.get(url, headers={"accept": "application/vnd.api+json"})
    assert resp.ok, resp.text
    return resp.json()


def test_add_results_to_location(locationRespFixture: dict):
    model = LocationResponseWithIncluded.model_validate(locationRespFixture)
    resultBuilder = LocationResultBuilder(cache=RISECache(), base_response=model)
    resultBuilder.load_results()
