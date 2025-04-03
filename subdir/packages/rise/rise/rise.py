# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import logging
from typing import Literal, Optional

from com.helpers import OAFFieldsMapping, get_oaf_fields_from_pydantic_model
from com.otel import otel_trace
from com.protocol import OAFProviderProtocol
from pygeoapi.provider.base import BaseProvider
from pygeoapi.util import crs_transform
from rise.lib.cache import RISECache
from com.geojson.helpers import (
    GeojsonFeatureDict,
    GeojsonFeatureCollectionDict,
    SortDict,
)
from rise.lib.location import LocationResponseWithIncluded
from rise.lib.types.location import LocationDataAttributes

LOGGER = logging.getLogger(__name__)


class RiseProvider(BaseProvider, OAFProviderProtocol):
    """Rise Provider for OGC API Features"""

    _fields: OAFFieldsMapping

    def __init__(self, provider_def):
        """
        Initialize object
        :param provider_def: provider definition
        """
        self.cache = RISECache()
        super().__init__(provider_def)
        self.get_fields()

    @otel_trace()
    def items(
        self,
        bbox: list = [],
        datetime_: Optional[str] = None,
        resulttype: Optional[Literal["hits", "results"]] = "results",
        # return features as normal, but return only the properties specified in `select_properties`
        select_properties: Optional[
            list[str]
        ] = None,  # query this with ?properties in the actual url
        # filter out features based on whether they contain all the `properties` with their corresponding values
        properties: list[tuple[str, str]] = [],
        sortby: Optional[list[SortDict]] = None,
        limit: Optional[int] = None,
        itemId: Optional[
            str
        ] = None,  # unlike edr, this is a string; we need to case to an int before filtering
        offset: Optional[int] = 0,
        skip_geometry: Optional[bool] = False,
        **kwargs,  # other implicit args added by pygeoapi
    ) -> GeojsonFeatureCollectionDict | GeojsonFeatureDict:
        if itemId:
            assert not properties, (
                "Cannot use itemId and properties together since that would potentially filter out the single item"
            )

        # we don't filter by parameters here since OAF filters features by
        # the attributes of the feature, not the parameters of the associated timeseries data
        raw_resp = self.cache.get_or_fetch_all_param_filtered_pages(
            only_include_locations_with_data=False
        )
        response = LocationResponseWithIncluded.from_api_pages(raw_resp)

        if itemId:
            response = response.drop_everything_but_one_location(int(itemId))

        if datetime_:
            response = response.drop_outside_of_date_range(datetime_)

        # Even though bbox is required, it can be an empty list. If it is empty just skip filtering
        if bbox:
            response = response.drop_outside_of_bbox(bbox)

        if offset:
            response = response.drop_before_offset(offset)

        if limit:
            response = response.drop_after_limit(limit)

        if resulttype == "hits":
            return {
                "type": "FeatureCollection",
                "features": [],
                "numberMatched": len(response.data),
            }

        return response.to_geojson(
            itemsIDSingleFeature=itemId is not None,
            skip_geometry=skip_geometry,
            select_properties=select_properties,
            properties=properties,
            fields_mapping=self._fields,
            sortby=sortby,
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

    def get_fields(self, **kwargs) -> OAFFieldsMapping:
        """
        Get provider field information (names, types)

        Example response: {'field1': 'string', 'field2': 'number'}

        :returns: dict of field names and their associated JSON Schema types
        """
        if not self._fields:
            self._fields = get_oaf_fields_from_pydantic_model(LocationDataAttributes)

        return self._fields
