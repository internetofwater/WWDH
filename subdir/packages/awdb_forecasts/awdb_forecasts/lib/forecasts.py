# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from typing import Optional
from com.cache import RedisCache
from com.helpers import await_
from awdb_com.types import ForecastDataDTO


class ForecastResultCollection:
    """
    A helper class for fetching results and processing them

    In snotel results are called `data`
    """

    def __init__(
        self,
    ):
        self.cache = RedisCache()

    def fetch_all_data(
        self,
        station_triplets: list[str],
        element_code: str = "*",
        force_fetch: bool = False,
        datetime_filter: Optional[str] = None,
    ) -> dict[str, list[ForecastDataDTO]]:
        """
        Given a list of station triples, fetch all associated data for them
        """

        assert station_triplets, "No station triplets provided"
        station_triplets_comma_separated = ",".join(station_triplets)
        assert element_code
        url = f"https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/forecasts?elements={element_code}&stationTriplets={station_triplets_comma_separated}"
        result = await_(self.cache.get_or_fetch(url))
        assert "error" not in result, result

        assert result
        tripletToForecast: dict[str, list[ForecastDataDTO]] = {}
        for res in result:
            tripletToForecast[res.get("stationTriplet")] = [
                ForecastDataDTO.model_validate(item) for item in res["data"]
            ]
        return tripletToForecast
