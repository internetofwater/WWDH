# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from typing import Optional
from urllib.parse import urlparse
from com.helpers import await_
from pydantic import BaseModel
from rise.lib.cache import RISECache
from rise.lib.helpers import merge_pages


def test_merge_pages():
    fetched_mock = {
        "https://data.usbr.gov/rise/api/location2": {
            "data": [
                {"id": "https://data.usbr.gov/rise/api/catalog-item/128564"},
                {"id": "https://data.usbr.gov/rise/api/catalog-item/128565"},
            ]
        },
        "https://data.usbr.gov/rise/api/location1": {
            "data": [
                {"id": "https://data.usbr.gov/rise/api/catalog-item/128562"},
                {"id": "https://data.usbr.gov/rise/api/catalog-item/128563"},
            ]
        },
    }

    merged = merge_pages(fetched_mock)
    assert merged["data"] == [
        {"id": "https://data.usbr.gov/rise/api/catalog-item/128564"},
        {"id": "https://data.usbr.gov/rise/api/catalog-item/128565"},
        {"id": "https://data.usbr.gov/rise/api/catalog-item/128562"},
        {"id": "https://data.usbr.gov/rise/api/catalog-item/128563"},
    ]


def test_integration_merge_pages():
    url = "https://data.usbr.gov/rise/api/location?itemStructureId=1"
    cache = RISECache()
    totalitems = await_(cache.get_or_fetch(url))["meta"]["totalItems"]
    pages = await_(cache.get_or_fetch_all_pages(url))
    merged = merge_pages(pages)
    assert merged is not None
    assert "data" in merged
    assert merged["data"], merged
    assert len(merged["data"]) == totalitems, merged["data"]


def test_parse_query_params():
    url = "https://example.com?param1=value1&param2=value2"
    parsed_url = urlparse(url)
    assert bool(parsed_url.query)
    url2 = "https://example.com"
    parsed_url2 = urlparse(url2)
    assert not bool(parsed_url2.query)

    url3 = "https://example.com?"
    parsed_url3 = urlparse(url3)
    assert not bool(parsed_url3.query)


def test_dump_none():
    class DummyNestedModel(BaseModel):
        a: Optional[int] = None
        b: Optional[str] = None

    class DummyModel(BaseModel):
        a: int
        b: DummyNestedModel

    model = DummyModel(a=1, b=DummyNestedModel(a=1, b=None))
    assert model.model_dump() == {"a": 1, "b": {"a": 1, "b": None}}
    assert model.model_dump(exclude_none=True) == {"a": 1, "b": {"a": 1}}
