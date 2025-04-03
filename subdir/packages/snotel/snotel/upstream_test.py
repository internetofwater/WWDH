# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from com.cache import RedisCache
import pytest


"""
According to upstream swagger docs

'The list of stations will be filtered to only those that contain at least one of the elements specified and the list of stations elements will be filter to only those that have these elements.'
"""


@pytest.mark.upstream
@pytest.mark.asyncio
async def test_element_filter():
    """
    It appears that in some cases, filtering by elements does not do anything

    This is unusual behavior and might be a sign something is wrong upstream
    """
    cache = RedisCache()

    baseUrl = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations?activeOnly=true&stationTriplets=*:*:SNTL"

    response = await cache.get_or_fetch(baseUrl)

    """
    According to upstream swagger docs

    'The list of stations will be filtered to only those that contain at least one of the elements specified and the list of stations elements will be filter to only those that have these elements.'
    """

    urlWithFilter = f"{baseUrl}&elements=SNRR"

    responseWithFilter = await cache.get_or_fetch(urlWithFilter)

    assert len(response) != len(responseWithFilter)


@pytest.mark.upstream
@pytest.mark.asyncio
async def test_some_filters_do_nothing():
    """
    It appears that in some cases, filtering by elements does not do anything

    Presume that this is since some elements are on all stations
    """

    baseUrl = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations?activeOnly=true&stationTriplets=*:*:SNTL"

    response = await RedisCache().get_or_fetch(baseUrl)

    urlWithFilter = f"{baseUrl}&elements=TAVG"

    responseWithFilter = await RedisCache().get_or_fetch(urlWithFilter)

    assert len(response) == len(responseWithFilter)
