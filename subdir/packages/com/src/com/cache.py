# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import asyncio
import logging
import redis.asyncio as redis
import aiohttp
from aiohttp import client_exceptions
from datetime import timedelta
from com.env import REDIS_HOST, REDIS_PORT, TRACER
import orjson

HEADERS = {"accept": "application/vnd.api+json, application/json"}

LOGGER = logging.getLogger(__name__)


async def fetch_url(url: str) -> dict:
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url, headers=HEADERS) as response:
            try:
                return await response.json()
            except client_exceptions.ContentTypeError as e:
                LOGGER.error(f"{e}: Text: {await response.text()}, URL: {url}")
                raise e


class RedisCache:
    """A cache implementation using Redis with ttl support"""

    def __init__(self, ttl: timedelta = timedelta(hours=72)):
        self.db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=False)
        self.ttl = ttl

    async def set(self, url: str, json_data: dict):
        """Associate a url key with json data in the cache"""
        # Serialize the data before storing it in Redis
        await self.db.set(name=url, value=orjson.dumps(json_data))
        await self.db.expire(name=url, time=self.ttl)

    async def reset(self):
        """Delete all keys in the current Redis database"""
        await self.db.flushdb()

    async def clear(self, url: str):
        """Delete a specific key in the redis db"""
        await self.db.delete(url)

    async def contains(self, url: str) -> bool:
        # Check if the key exists in Redis
        return await self.db.exists(url) == 1

    async def get(self, url: str) -> dict:
        """Get an individual item in the redis db"""
        with TRACER.start_span("cache_retrieval") as s:
            s.set_attribute("cache_retrieval.url", url)

            # Deserialize the data after retrieving it from Redis
            data = await self.db.get(url)
            if data is None:
                raise KeyError(f"{url} not found in cache")
            return orjson.loads(data)

    async def get_or_fetch(self, url, force_fetch=False) -> dict:
        """Send a get request or grab it locally if it already exists in the cache"""

        if not await self.contains(url) or force_fetch:
            res = await fetch_url(url)
            await self.set(url, res)
            return res

        else:
            LOGGER.debug(f"Got {url} from cache")
            return await self.get(url)

    async def get_or_fetch_group(
        self, urls: list[str], force_fetch=False
    ) -> dict[str, dict]:
        """Send a GET request to all URLs or grab it locally if it already exists in the cache."""

        urls_not_in_cache, urls_in_cache = [], []
        for url in urls:
            if not await self.contains(url) or force_fetch:
                urls_not_in_cache.append(url)
            else:
                urls_in_cache.append(url)

        assert set(urls_in_cache).isdisjoint(set(urls_not_in_cache))

        # Fetch from remote API
        urls_not_in_cache_coroutine = self._fetch_and_set_url_group(urls_not_in_cache)

        # Fetch from local cache
        with TRACER.start_span("mget") as span:
            span.set_attribute("mget.urls", urls_in_cache)
            cache_fetch = self.db.mget(urls_in_cache)
            cache_results = await cache_fetch
            urlToResult = {}
            for url, data in zip(urls_in_cache, cache_results):
                urlToResult[url] = orjson.loads(data)

        remote_results = await urls_not_in_cache_coroutine
        urlToResult.update(remote_results)
        return urlToResult

    async def _fetch_and_set_url_group(
        self,
        urls: list[str],
    ):
        tasks = [asyncio.create_task(fetch_url(url)) for url in urls]

        results = {url: {} for url in urls}

        for coroutine, url in zip(asyncio.as_completed(tasks), urls):
            result = await coroutine
            results[url] = result
            await self.set(url, result)

        return results
