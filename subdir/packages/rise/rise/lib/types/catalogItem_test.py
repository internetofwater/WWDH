# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import pytest
import requests

from rise.lib.types.catalogItem import CatalogItemResponse


@pytest.fixture
def catalogItemRespFixture():
    url = "https://data.usbr.gov/rise/api/catalog-item/4222 "
    resp = requests.get(url, headers={"accept": "application/vnd.api+json"})
    assert resp.ok, resp.text
    return resp.json()


def test_catalogitem_parse(catalogItemRespFixture: dict):
    model = CatalogItemResponse.model_validate(catalogItemRespFixture)
    assert model
