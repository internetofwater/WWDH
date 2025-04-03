# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import logging
from typing import Any, Literal, Optional, Tuple

from com.helpers import await_
from pydantic import BaseModel

from com.env import TRACER
from rise.lib.cache import RISECache
from rise.lib.helpers import flatten_values, getResultUrlFromCatalogUrl
from rise.lib.location import LocationResponseWithIncluded
from rise.lib.types.results import ResultResponse

LOGGER = logging.getLogger(__name__)

"""
This file represents all code that is used to add the results to the location response
This is essentially used to prepare the location response to covjson output
"""


class ParameterWithResults(BaseModel):
    catalogItemId: str
    parameterId: str

    # We allow None since each coverage could have different length but they share the same x-axis
    # length; thus if a coverage is missing data, it needs to be explicitly filled in with None
    # unless the entire coverage is missing whereupon it will be entirely skipped
    timeseriesResults: list[float | None]
    timeseriesDates: list[str | None]


class DataNeededForCovjson(BaseModel):
    """
    This class represents the smallest amount of data needed for making covjson
    from rise. We pass around a small class in an effort to make the ETL cleaner and simpler
    """

    location: str
    locationType: Literal["Point", "Polygon", "LineString"]
    geometry: list[Any] | Tuple[float, float]
    parameters: list[ParameterWithResults]


class LocationResultBuilder:
    """
    Helper class for associating a location/ response from RISE
    with its associated timeseries data results
    """

    def __init__(self, cache: RISECache, base_response: LocationResponseWithIncluded):
        self.cache = cache
        self.base_response = base_response
        self.locationToCatalogItemUrls = self.base_response.get_catalogItemURLs()
        self.catalogItemToLocationId = {}
        for location, catalogItems in self.locationToCatalogItemUrls.items():
            for catalogItem in catalogItems:
                self.catalogItemToLocationId[catalogItem] = location

    def _get_all_timeseries_data(self, time_filter: Optional[str] = None):
        # Make a dictionary from an existing response
        catalogItemUrls = flatten_values(self.locationToCatalogItemUrls)

        resultUrls = {
            url: getResultUrlFromCatalogUrl(url, time_filter) for url in catalogItemUrls
        }

        if len(resultUrls) != len(set(resultUrls)):
            raise RuntimeError(
                "Got duplicate result urls when loading timeseries data:",
                set([x for x in resultUrls if list(resultUrls.keys()).count(x) > 1]),
            )

        LOGGER.debug(f"Fetching {resultUrls}; {len(resultUrls)} in total")
        return await_(self.cache.get_or_fetch_all_results(resultUrls))

    def _get_timeseries_for_catalogitem(self, catalogItem):
        if catalogItem not in self.timeseriesResults:
            return None
        return self.timeseriesResults[catalogItem]

    @TRACER.start_as_current_span("fetching_and_loading_timeseries")
    def load_results(
        self, time_filter: Optional[str] = None
    ) -> list[DataNeededForCovjson]:
        """Given a location that contains just catalog item ids, fill in the catalog items with the full
        endpoint response for the given catalog item so it can be more easily used for complex joins
        """

        self.timeseriesResults = self._get_all_timeseries_data(time_filter)

        locations_with_data: list[DataNeededForCovjson] = []

        for location in self.base_response.data:
            paramAndResults: list[ParameterWithResults] = []

            associatedCatalogItems = self.locationToCatalogItemUrls.get(location.id)
            if not associatedCatalogItems:
                continue
            for catalogItemUrl in associatedCatalogItems:
                catalogUrlAsResultUrl = getResultUrlFromCatalogUrl(
                    catalogItemUrl, time_filter
                )
                timseriesResults = self.timeseriesResults.get(catalogUrlAsResultUrl)
                # if there were no results for this catalog item, continue and don't even bother serializing
                if not timseriesResults:
                    continue

                if timseriesResults.get("detail") == "Internal Server Error":
                    await_(
                        self.cache.clear(catalogUrlAsResultUrl)
                    )  # clear the cache url so it can be refetched
                    raise RuntimeError(
                        f"Got an error when fetching {catalogUrlAsResultUrl}:{timseriesResults}"
                    )

                timeseriesModel = ResultResponse.model_validate(timseriesResults)
                # it is possible for a catalog item to have an associated result endpoint but no data inside of it
                if not timeseriesModel.data or not timeseriesModel:
                    continue
                results = timeseriesModel.get_results()
                dates = timeseriesModel.get_dates()
                if not results or not dates:
                    continue
                paramAndResults.append(
                    ParameterWithResults(
                        catalogItemId=catalogItemUrl,
                        timeseriesResults=results,
                        timeseriesDates=dates,
                        parameterId=timeseriesModel.get_parameter_id(),
                    )
                )
            locations_with_data.append(
                DataNeededForCovjson(
                    locationType=location.attributes.locationCoordinates.type,
                    location=location.id,
                    parameters=paramAndResults,
                    geometry=location.attributes.locationCoordinates.coordinates,
                )
            )

        return locations_with_data
