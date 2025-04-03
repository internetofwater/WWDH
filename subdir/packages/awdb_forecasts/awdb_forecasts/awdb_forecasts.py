# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import logging
from typing import Literal, Optional

from awdb_forecasts.lib.forecast_locations import ForecastLocationCollection
from com.helpers import get_oaf_fields_from_pydantic_model
from com.otel import otel_trace
from com.protocol import OAFProviderProtocol
from pygeoapi.provider.base import BaseProvider
from pygeoapi.util import crs_transform
from com.geojson.helpers import (
    GeojsonFeatureDict,
    GeojsonFeatureCollectionDict,
    SortDict,
)
from com.cache import RedisCache
from awdb_com.types import StationDTO

LOGGER = logging.getLogger(__name__)


class AwdbForecastsProvider(BaseProvider, OAFProviderProtocol):
    """Rise Provider for OGC API Features"""

    def __init__(self, provider_def):
        """
        Initialize object
        :param provider_def: provider definition
        """
        BaseProvider.__init__(self, provider_def)
        self.cache = RedisCache()
        self.get_fields()

    @otel_trace()
    def items(
        self,
        bbox: list = [],
        datetime_: Optional[str] = None,
        resulttype: Optional[Literal["hits", "results"]] = "results",
        # select only features that contains all the `select_properties` values
        select_properties: Optional[
            list[str]
        ] = None,  # query this with ?properties in the actual url
        # select only features that contains all the `properties` with their corresponding values
        properties: list[tuple[str, str]] = [],
        sortby: Optional[list[SortDict]] = None,
        limit: Optional[int] = None,
        itemId: Optional[
            str
        ] = None,  # unlike edr, this is a string; we need to case to an int before filtering
        offset: Optional[int] = 0,
        skip_geometry: Optional[bool] = False,
        **kwargs,
    ) -> GeojsonFeatureCollectionDict | GeojsonFeatureDict:
        # items/ returns all features, locations/ returns only features with timeseries, and thus forecasts
        collection = ForecastLocationCollection(
            select_properties, only_stations_with_forecasts=False
        )
        if itemId:
            collection = collection.drop_all_locations_but_id(itemId)
        if bbox:
            collection = collection.drop_all_locations_outside_bounding_box(bbox)

        if datetime_:
            collection = collection.select_date_range(datetime_)

        if limit:
            collection = collection.drop_after_limit(limit)
        if offset:
            collection = collection.drop_before_offset(offset)

        if resulttype == "hits":
            return {
                "type": "FeatureCollection",
                "features": [],
                "numberMatched": len(collection.locations),
            }

        return collection.to_geojson(
            itemsIDSingleFeature=itemId is not None,
            skip_geometry=skip_geometry,
            select_properties=select_properties,
            properties=properties,
            sortby=sortby,
            fields_mapping=self.get_fields(),
        )

    @crs_transform
    def query(self, **kwargs):
        return self.items(**kwargs)

    def get(self, identifier, **kwargs):
        """
        query CSV id

        :param identifier: feature id

        :returns: dict of single GeoJSON feature
        """

        return self.items(itemId=identifier, bbox=[], **kwargs)

    def get_fields(self, **kwargs):
        """
        Get provider field information (names, types)

        Example response: {'field1': 'string', 'field2': 'number'}

        :returns: dict of field names and their associated JSON Schema types
        """
        if not self._fields:
            self._fields = get_oaf_fields_from_pydantic_model(StationDTO)
        return self._fields
