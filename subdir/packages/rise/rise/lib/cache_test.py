# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import asyncio
import json
import time

from com.helpers import await_
import pytest
from rise.lib.cache import RISECache


@pytest.mark.asyncio
async def test_simple_redis_serialization():
    cache = RISECache()
    data = json.loads('{"test": 1}')
    await cache.set("test_url_location", data)  # noqa: F821
    # our interface does not export an atomic set operation, so we need to just block heuristically
    time.sleep(0.2)
    val = await cache.get("test_url_location")
    assert val == data


@pytest.mark.asyncio
async def test_redis_wrapper():
    cache = RISECache()
    await cache.clear("test_url_catalog_item")
    await cache.set("test_url_catalog_item", {})
    assert await cache.get("test_url_catalog_item") == {}
    time.sleep(1)
    with pytest.raises(KeyError):
        await cache.get("DUMMY_KEY")


@pytest.mark.asyncio
async def test_get_or_fetch_group():
    cache = RISECache()
    urls = [
        "https://data.usbr.gov/rise/api/catalog-item/128562",
        "https://data.usbr.gov/rise/api/catalog-item/128563",
    ]
    group = await cache.get_or_fetch_group(urls)
    assert len(group) == 2
    assert group[urls[0]] != group[urls[1]] != {}


class TestFnsWithCaching:
    def test_fetch_group(self):
        urls = [
            "https://data.usbr.gov/rise/api/catalog-item/128562",
            "https://data.usbr.gov/rise/api/catalog-item/128563",
            "https://data.usbr.gov/rise/api/catalog-item/128564",
        ]
        cache = RISECache()
        resp = await_(cache._fetch_and_set_url_group(urls))
        assert len(resp) == 3
        assert None not in resp

    @pytest.mark.asyncio
    async def test_fetch_all_pages(self):
        url = "https://data.usbr.gov/rise/api/location"
        cache = RISECache()
        pages = await cache.get_or_fetch_all_pages(url)

        # this is at least 7 since in the future the api could change
        assert len(pages) >= 7, "Expected at least 7 pages"
        for url, resp in pages.items():
            # 100 is the max number of items you can query
            # so we should get 100 items per page
            assert resp["meta"]["itemsPerPage"] == 100

    @pytest.mark.asyncio
    async def test_fields_are_unique(self):
        cache = RISECache()
        field_ids = (await cache.get_or_fetch_parameters()).keys()
        length = len(field_ids)
        assert length == len(set(field_ids))

    @pytest.mark.asyncio
    async def test_cache(self):
        url = "https://data.usbr.gov/rise/api/item-structure/1"

        cache = RISECache()
        await cache.clear(url)
        remote_res = await cache.get_or_fetch(url)

        assert await cache.contains(url)
        await cache.clear(url)
        assert not await cache.contains(url)
        disk_res = await cache.get_or_fetch(url)
        assert disk_res
        assert remote_res == disk_res


def test_safe_async():
    # Create an event loop without running anything on it
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Check that the event loop is running by calling run_async
    await_(asyncio.sleep(0.1))

    # Close the event loop after the test
    loop.close()


@pytest.mark.asyncio
async def test_fetch_all_results():
    result_base_url = "https://data.usbr.gov/rise/api/result?itemId=1"
    cache = RISECache()
    results = await cache.get_or_fetch_all_results(
        {
            "1": result_base_url,
        }
    )
    assert len(results) == 1
    assert len(results[result_base_url]["data"]) > 1000
