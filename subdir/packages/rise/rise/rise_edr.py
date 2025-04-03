# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import logging
from typing import ClassVar, Optional

from com.helpers import await_
from com.otel import otel_trace
from com.protocol import EDRProviderProtocol
from pygeoapi.provider.base import (
    ProviderQueryError,
)
from pygeoapi.provider.base_edr import BaseEDRProvider
from rise.lib.covjson.covjson import CovJSONBuilder
from rise.lib.location import LocationResponseWithIncluded
from rise.lib.cache import RISECache
from rise.lib.add_results import LocationResultBuilder

LOGGER = logging.getLogger(__name__)


class RiseEDRProvider(BaseEDRProvider, EDRProviderProtocol):
    """The EDR Provider for the USBR Rise API"""

    LOCATION_API: ClassVar[str] = "https://data.usbr.gov/rise/api/location"
    BASE_API: ClassVar[str] = "https://data.usbr.gov"
    cache: RISECache

    def __init__(self, provider_def=None):
        """
        Initialize object

        :param provider_def: provider definition

        :returns: rise.base_edr.RiseEDRProvider
        """
        try:
            self.cache = RISECache()
        except KeyError:
            LOGGER.error(
                "You must specify a cache implementation in the config.yml for RISE"
            )
            raise

        provider_def = {
            "name": "Rise EDR",
            "type": "feature",
            "data": "remote",
        } or provider_def

        BaseEDRProvider.__init__(self, provider_def)

        self.instances = []  # used so pygeoapi doesn't register the same query multiple times in the UI

    @otel_trace()
    @BaseEDRProvider.register()
    def locations(
        self,
        location_id: Optional[str] = None,
        datetime_: Optional[str] = None,
        select_properties: Optional[list[str]] = None,
        crs: Optional[str] = None,
        format_: Optional[str] = None,
        **kwargs,
    ):
        """
        Extract data from location
        """
        if not location_id and datetime_:
            raise ProviderQueryError("Can't filter by date on every location")

        raw_resp = self.cache.get_or_fetch_all_param_filtered_pages(select_properties)
        response = LocationResponseWithIncluded.from_api_pages(raw_resp)

        if location_id:
            try:
                location_id_as_int = int(location_id)
            except ValueError:
                raise ProviderQueryError(
                    f"Invalid location id: '{location_id}'; RISE location IDs must be integers"
                )
            response = response.drop_everything_but_one_location(location_id_as_int)

        # If a location exists but has no CatalogItems, it should not appear in locations
        response = response.drop_locations_without_catalogitems()

        # FROM SPEC: If a location id is not defined the API SHALL return a GeoJSON features array of valid location identifiers,
        if not any([crs, datetime_, location_id]) or format_ == "geojson":
            return response.to_geojson(
                itemsIDSingleFeature=location_id is not None,
                fields_mapping=self.get_fields(),
            )

        # if we are returning covjson we need to fetch the results and fill in the json
        builder = LocationResultBuilder(cache=self.cache, base_response=response)
        response_with_results = builder.load_results(time_filter=datetime_)
        return CovJSONBuilder(self.cache).fill_template(
            response_with_results, select_properties
        )

    def get_fields(self):
        """Get the list of all parameters (i.e. fields) that the user can filter by"""
        if self._fields:
            return self._fields

        self._fields = await_(self.cache.get_or_fetch_parameters())

        return self._fields

    @otel_trace()
    @BaseEDRProvider.register()
    def cube(
        self,
        bbox: list,
        datetime_: Optional[str] = None,
        select_properties: Optional[list] = None,
        z: Optional[str] = None,
        format_: Optional[str] = None,
        **kwargs,
    ):
        """
        Returns a data cube defined by bbox and z parameters

        :param bbox: `list` of minx,miny,maxx,maxy coordinate values as `float`
        :param datetime_: temporal (datestamp or extent)
        :param z: vertical level(s)
        :param format_: data format of output
        """
        # Example: http://localhost:5000/collections/rise-edr/cube?bbox=-101.381836,27.215556,-92.680664,32.23139
        raw_resp = self.cache.get_or_fetch_all_param_filtered_pages(select_properties)
        response = LocationResponseWithIncluded.from_api_pages(raw_resp)

        if datetime_:
            response = response.drop_outside_of_date_range(datetime_)

        response = response.drop_outside_of_bbox(bbox, z)

        builder = LocationResultBuilder(cache=self.cache, base_response=response)
        response_with_results = builder.load_results(time_filter=datetime_)
        return CovJSONBuilder(self.cache).fill_template(
            response_with_results, select_properties
        )

    @otel_trace()
    @BaseEDRProvider.register()
    def area(
        self,
        # Well known text (WKT) representation of the geometry for the area
        wkt: str,
        select_properties: list[str] = [],
        datetime_: Optional[str] = None,
        z: Optional[str] = None,
        format_: Optional[str] = None,
        **kwargs,
    ):
        """
        Extract and return coverage data from a specified area.
        Example: http://localhost:5000/collections/rise-edr/area?coords=POLYGON%20((-109.204102%2047.010226,%20-104.655762%2047.010226,%20-104.655762%2049.267805,%20-109.204102%2049.267805,%20-109.204102%2047.010226))&f=json
        """

        raw_resp = self.cache.get_or_fetch_all_param_filtered_pages(select_properties)
        assert len(raw_resp) > 1
        found = set()
        for url in raw_resp:
            for data in raw_resp[url]["data"]:
                id = data["attributes"]["_id"]
                assert id not in found, (
                    f"{id} is a duplicate with name {data['attributes']['locationName']} in {url}"
                )
                found.add(id)
        response = LocationResponseWithIncluded.from_api_pages(raw_resp)

        assert not response.has_duplicate_locations()

        if datetime_:
            response = response.drop_outside_of_date_range(datetime_)

        if wkt != "":
            response = response.drop_outside_of_wkt(wkt, z)

        assert not response.has_duplicate_locations()

        builder = LocationResultBuilder(cache=self.cache, base_response=response)
        response_with_results = builder.load_results(time_filter=datetime_)
        return CovJSONBuilder(self.cache).fill_template(
            response_with_results, select_properties
        )

    @BaseEDRProvider.register()
    def items(self, **kwargs):
        # We have to define this since pygeoapi has a limitation and needs both EDR and OAF for items
        # https://github.com/geopython/pygeoapi/issues/1748
        pass

    def __repr__(self):
        return "<RiseEDRProvider>"
