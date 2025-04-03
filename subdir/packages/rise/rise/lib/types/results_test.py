# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import pytest
import requests
from rise.lib.types.results import ResultResponse


@pytest.fixture
def resultRespFixture():
    url = "https://data.usbr.gov/rise/api/result?page=1&itemsPerPage=5&locationId%5B%5D=1&locationId%5B%5D=2&order%5Bid%5D="
    resp = requests.get(url, headers={"accept": "application/vnd.api+json"})
    assert resp.ok, resp.text
    return resp.json()


def test_location_parse(resultRespFixture: dict):
    serializedResp = ResultResponse.model_validate(resultRespFixture)
    assert serializedResp.get_results()
    assert serializedResp.get_dates()
    assert serializedResp.get_parameter_id() == "3"
