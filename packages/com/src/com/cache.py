# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import asyncio
import logging
from typing import Optional
import redis.asyncio as redis
import aiohttp
from aiohttp import client_exceptions
from datetime import timedelta
from com.env import REDIS_HOST, REDIS_PORT, TRACER
import orjson

HEADERS = {"accept": "application/vnd.api+json, application/json"}

LOGGER = logging.getLogger(__name__)


async def fetch_url(
    url: str, headers=HEADERS, custom_mimetype: Optional[str] = None
) -> dict:
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, headers=headers) as response:
            try:
                response.raise_for_status()
                if custom_mimetype:
                    return await response.json(content_type=custom_mimetype)
                return await response.json()
            except client_exceptions.ContentTypeError as e:
                LOGGER.error(f"{e}: Text: {await response.text()}, URL: {url}")
                raise e


async def fetch_url_text(url: str, headers=HEADERS) -> str:
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, headers=headers) as response:
            return await response.text()


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

    async def set_text(self, url: str, text_data: str):
        await self.db.set(name=url, value=text_data)
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

    async def get_text(self, url: str) -> str:
        data = await self.db.get(url)
        if data is None:
            raise KeyError(f"{url} not found in cache")
        return data

    async def get_or_fetch_json(self, url, force_fetch=False, headers=HEADERS) -> dict:
        """Send a get request or grab it locally if it already exists in the cache"""

        if not await self.contains(url) or force_fetch:
            res = await fetch_url(url, headers=headers)
            await self.set(url, res)
            return res

        else:
            LOGGER.debug(f"Got {url} from cache")
            return await self.get(url)

    async def get_or_fetch_response_text(self, url, force_fetch=False, headers=HEADERS):
        if not await self.contains(url) or force_fetch:
            res = await fetch_url_text(url, headers=headers)
            await self.set_text(url, res)
            return res
        else:
            LOGGER.debug(f"Got {url} from cache")
            return await self.get_text(url)

    async def get_or_fetch_group(
        self, urls: list[str], force_fetch=False, custom_mimetype: Optional[str] = None
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
        urls_not_in_cache_coroutine = self._fetch_and_set_url_group(
            urls_not_in_cache, custom_mimetype
        )

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
        custom_mimetype: Optional[str] = None,
    ):
        results = await asyncio.gather(
            *(fetch_url(url, custom_mimetype=custom_mimetype) for url in urls)
        )

        for url, result in zip(urls, results):
            await self.set(url, result)

        return dict(zip(urls, results))
