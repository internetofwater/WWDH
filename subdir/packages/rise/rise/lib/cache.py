# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import asyncio
import logging
import math
from typing import Optional
from urllib.parse import urlparse
from com.helpers import EDRFieldsMapping, await_
from rise.custom_types import JsonPayload, Url
import aiohttp
from aiohttp import client_exceptions
from datetime import timedelta
from com.cache import RedisCache
from com.env import TRACER
from rise.lib.helpers import merge_pages

HEADERS = {"accept": "application/vnd.api+json"}

LOGGER = logging.getLogger(__name__)


async def fetch_url(url: str) -> dict:
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url, headers=HEADERS) as response:
            try:
                return await response.json()
            except client_exceptions.ContentTypeError as e:
                LOGGER.error(f"{e}: Text: {await response.text()}, URL: {url}")
                raise e


class RISECache(RedisCache):
    """A cache implementation using Redis with ttl support"""

    def __init__(self, ttl: timedelta = timedelta(hours=72)):
        super().__init__(ttl)

    async def get_or_fetch_all_pages(
        self, base_url: str, force_fetch=False
    ) -> dict[Url, JsonPayload]:
        MAX_ITEMS_PER_PAGE: int

        if "data.usbr.gov/rise/api/result" in base_url:
            # there is a special case in RISE where the max number of items per result page is 10000
            # this appears to be different from the other endpoints
            MAX_ITEMS_PER_RESULT_PAGE = 10000
            MAX_ITEMS_PER_PAGE = MAX_ITEMS_PER_RESULT_PAGE
        else:
            MAX_ITEMS_PER_PAGE = 100

        # Get the first response that contains the list of pages
        response = await self.get_or_fetch(base_url)

        NOT_PAGINATED = "meta" not in response
        if NOT_PAGINATED:
            return {base_url: response}

        total_items = response["meta"]["totalItems"]

        pages_to_complete = math.ceil(total_items / MAX_ITEMS_PER_PAGE)

        urls = []

        assert not base_url.endswith("&"), (
            "The base url should not end with an ampersand since it makes it ambiguous to paginate"
        )
        assert not base_url.endswith("?")
        # Construct all the urls for the pages
        #  that we will then fetch in parallel
        # to get all the data for the endpoint
        for page in range(1, int(pages_to_complete) + 1):
            hasQueryParams = bool(urlparse(base_url).query)
            if hasQueryParams:
                urls.append(f"{base_url}&page={page}&itemsPerPage={MAX_ITEMS_PER_PAGE}")
            elif not hasQueryParams:
                urls.append(f"{base_url}?page={page}&itemsPerPage={MAX_ITEMS_PER_PAGE}")

        pages = await self.get_or_fetch_group(urls, force_fetch=force_fetch)
        assert len(pages) == pages_to_complete
        # found = {}
        # for base_url in pages:
        #     for location in pages[base_url]["data"]:
        #         id = location["attributes"]["_id"]

        #         if id in found:
        #             data = found[id]
        #             raise RuntimeError(
        #                 f"{id} previously had {data} but now has {base_url}"
        #             )

        #         found[id] = {
        #             "url": base_url,
        #             "data": location["attributes"]["_id"],
        #         }

        return pages

    async def get_or_fetch_parameters(self, force_fetch=False) -> EDRFieldsMapping:
        fields: EDRFieldsMapping = {}

        pages = await self.get_or_fetch_all_pages(
            "https://data.usbr.gov/rise/api/parameter",
            force_fetch=force_fetch,
        )
        res = merge_pages(pages)

        assert None not in res.values()
        assert None not in res.keys()

        for item in res["data"]:
            param = item["attributes"]
            # TODO check if this should be a string or a number
            fields[str(param["_id"])] = {
                "type": param["parameterUnit"],
                "title": param["parameterName"],
                "description": param["parameterDescription"],
                "x-ogc-unit": param["parameterUnit"],
            }

        return fields

    @TRACER.start_as_current_span("get_or_fetch_all_param_filtered_pages")
    def get_or_fetch_all_param_filtered_pages(
        self,
        properties_to_filter_by: Optional[list[str]] = None,
        only_include_locations_with_data: bool = True,
        force_fetch=False,
    ):
        """Return all locations which contain timeseries data and optionally, also a given list of properties. Will return the associated catalogitems / catalogrecords for joins"""
        base_url = "https://data.usbr.gov/rise/api/location?order[id]=asc&include=catalogRecords.catalogItems"
        hasTimeseriesData = "itemStructureId=1"
        if only_include_locations_with_data:
            base_url += f"&{hasTimeseriesData}"

        if properties_to_filter_by:
            base_url += "&"
            for prop in properties_to_filter_by:
                assert isinstance(prop, str)
                base_url += f"parameterId%5B%5D={prop}&"
            base_url = base_url.removesuffix("&")
        return await_(self.get_or_fetch_all_pages(base_url, force_fetch=force_fetch))

    async def get_or_fetch_all_results(
        self, catalogItemToResultUrl: dict[str, str]
    ) -> dict[str, JsonPayload]:
        """Given a dictionary mapping catalog items to URLs, fetch all pages for each URL in parallel
        and return a dictionary mapping catalog items to their corresponding merged pages."""
        tasks = {
            resultUrl: asyncio.create_task(self.get_or_fetch_all_pages(resultUrl))
            for _, resultUrl in catalogItemToResultUrl.items()
        }

        results = await asyncio.gather(*tasks.values())

        mergedResult = {}

        for resultUrl, result in zip(tasks.keys(), results):
            mergedResult[resultUrl] = merge_pages(result)

        return mergedResult
