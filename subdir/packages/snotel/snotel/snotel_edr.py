# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import logging
from typing import Optional

from com.geojson.helpers import GeojsonFeatureCollectionDict, GeojsonFeatureDict
from com.helpers import EDRFieldsMapping
from com.otel import otel_trace
from com.protocol import EDRProviderProtocol
from pygeoapi.provider.base_edr import BaseEDRProvider
from rise.lib.covjson.types import CoverageCollectionDict
from snotel.lib.locations import SnotelLocationCollection
from snotel.lib.parameters import ParametersCollection
from pygeoapi.provider.base import ProviderQueryError

LOGGER = logging.getLogger(__name__)


class SnotelEDRProvider(BaseEDRProvider, EDRProviderProtocol):
    """The EDR Provider for the Snotel API"""

    def __init__(self, provider_def=None):
        """
        Initialize object

        :param provider_def: provider definition

        :returns: rise.base_edr.RiseEDRProvider
        """
        BaseEDRProvider.__init__(self, provider_def)
        self.instances = []

    @BaseEDRProvider.register()
    @otel_trace()
    def locations(
        self,
        location_id: Optional[str] = None,
        datetime_: Optional[str] = None,
        select_properties: Optional[list[str]] = None,
        crs: Optional[str] = None,
        format_: Optional[str] = None,
        **kwargs,
    ) -> CoverageCollectionDict | GeojsonFeatureCollectionDict | GeojsonFeatureDict:
        """
        Extract data from location
        """

        if not location_id and datetime_:
            raise ProviderQueryError(
                "Datetime parameter is not supported without location_id"
            )
        collection = SnotelLocationCollection(select_properties)
        if location_id:
            collection = collection.drop_all_locations_but_id(location_id)

        if not any([crs, datetime_, location_id]) or format_ == "geojson":
            return collection.to_geojson(
                itemsIDSingleFeature=location_id is not None,
                fields_mapping=self.get_fields(),
            )

        return collection.to_covjson(self.get_fields(), datetime_, select_properties)

    def get_fields(self) -> EDRFieldsMapping:
        """Get the list of all parameters (i.e. fields) that the user can filter by"""
        if not self._fields:
            self._fields = ParametersCollection().get_fields()
        return self._fields

    @BaseEDRProvider.register()
    @otel_trace()
    def cube(
        self,
        bbox: list,
        datetime_: Optional[str] = None,
        select_properties: Optional[list[str]] = None,
        z: Optional[str] = None,
        **kwargs,
    ) -> CoverageCollectionDict:
        """
        Returns a data cube defined by bbox and z parameters

        :param bbox: `list` of minx,miny,maxx,maxy coordinate values as `float`
        :param datetime_: temporal (datestamp or extent)
        :param z: vertical level(s)
        :param format_: data format of output
        """
        collection = SnotelLocationCollection(select_properties)

        collection.drop_all_locations_outside_bounding_box(bbox, z)

        return collection.to_covjson(self.get_fields(), datetime_, select_properties)

    @otel_trace()
    @BaseEDRProvider.register()
    def area(
        self,
        # Well known text (WKT) representation of the geometry for the area
        wkt: str,
        select_properties: list[str] = [],
        datetime_: Optional[str] = None,
        z: Optional[str] = None,
        **kwargs,
    ) -> CoverageCollectionDict:
        """
        Extract and return coverage data from a specified area.
        """
        collection = SnotelLocationCollection(select_properties)

        collection = collection.drop_outside_of_wkt(wkt, z)

        return collection.to_covjson(self.get_fields(), datetime_, select_properties)

    @BaseEDRProvider.register()
    def items(self, **kwargs):
        # We have to define this since pygeoapi has a limitation and needs both EDR and OAF for items
        # https://github.com/geopython/pygeoapi/issues/1748
        pass
