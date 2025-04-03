# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from datetime import datetime
from com.datetime import datetime_from_iso
from com.env import TRACER
from com.geojson.helpers import (
    GeojsonFeatureDict,
    GeojsonFeatureCollectionDict,
    SortDict,
    all_properties_found_in_feature,
    filter_out_properties_not_selected,
    sort_by_properties_in_place,
)
from com.helpers import (
    EDRFieldsMapping,
    OAFFieldsMapping,
    parse_bbox,
    parse_date,
    parse_z,
)
import geojson_pydantic
from rise.lib.covjson.types import CoverageCollectionDict
from rise.lib.types.helpers import ZType
from snotel.lib.covjson_builder import CovjsonBuilder
from awdb_com.types import StationDTO
import shapely
from typing import Optional, assert_never, cast
import shapely.wkt

type longitudeAndLatitude = tuple[float, float]


class LocationCollection:
    """A wrapper class containing locations and methods to filter them"""

    locations: list[StationDTO]

    def drop_all_locations_but_id(self, location_id: str):
        data = [v for v in self.locations if v.stationId == str(location_id)]
        self.locations = data
        return self

    def drop_after_limit(self, limit: int):
        """
        Return only the location data for the locations in the list up to the limit
        """
        self.locations = self.locations[:limit]
        return self

    def drop_before_offset(self, offset: int):
        """
        Return only the location data for the locations in the list after the offset
        """
        self.locations = self.locations[offset:]
        return self

    def drop_outside_of_wkt(self, wkt: Optional[str] = None, z: Optional[str] = None):
        parsed_geo = shapely.wkt.loads(str(wkt)) if wkt else None
        return self._filter_by_geometry(parsed_geo, z)

    def drop_all_locations_outside_bounding_box(self, bbox, z=None):
        if bbox:
            parse_result = parse_bbox(bbox)
            shapely_box = parse_result[0] if parse_result else None
            z = parse_result[1] if parse_result else z

        shapely_box = parse_bbox(bbox)[0] if bbox else None
        # TODO what happens if they specify both a bbox with z and a z value?
        z = parse_bbox(bbox)[1] if bbox else z
        return self._filter_by_geometry(shapely_box, z)

    def select_date_range(self, datetime_: str):
        """
        Drop locations if their begin-end range is outside of the query date range
        """
        location_indices_to_remove = set()

        parsed_date = parse_date(datetime_)
        MAGIC_UPSTREAM_DATE_SIGNIFYING_STILL_IN_SERVICE = "2100-01-01"

        if isinstance(parsed_date, tuple) and len(parsed_date) == 2:
            startQuery, endQuery = parsed_date

            for i, location in enumerate(self.locations):
                if not location.beginDate or not location.endDate:
                    location_indices_to_remove.add(i)
                    continue
                skipEndDateCheck = location.endDate.startswith(
                    MAGIC_UPSTREAM_DATE_SIGNIFYING_STILL_IN_SERVICE
                )
                startDate = datetime_from_iso(location.beginDate)
                endDate = datetime_from_iso(location.endDate)

                locationIsInsideQueryRange = startDate <= startQuery and (
                    endQuery <= endDate if not skipEndDateCheck else True
                )
                if not locationIsInsideQueryRange:
                    location_indices_to_remove.add(i)

        elif isinstance(parsed_date, datetime):
            for i, location in enumerate(self.locations):
                if not location.beginDate or not location.endDate:
                    location_indices_to_remove.add(i)
                    continue
                skipEndDateCheck = (
                    location.endDate == MAGIC_UPSTREAM_DATE_SIGNIFYING_STILL_IN_SERVICE
                )
                startDate = datetime_from_iso(location.beginDate)
                endDate = datetime_from_iso(location.endDate)
                if parsed_date < startDate or (
                    not skipEndDateCheck and parsed_date > endDate
                ):
                    location_indices_to_remove.add(i)
        else:
            raise RuntimeError(
                "datetime_ must be a date or date range with two dates separated by '/' but got {}".format(
                    datetime_
                )
            )

        # delete them backwards so we don't have to make a copy of the list or mess up indices while iterating
        for index in sorted(location_indices_to_remove, reverse=True):
            del self.locations[index]

        return self

    def to_geojson(
        self,
        itemsIDSingleFeature=False,
        skip_geometry: Optional[bool] = False,
        select_properties: Optional[list[str]] = None,
        properties: Optional[list[tuple[str, str]]] = None,
        fields_mapping: EDRFieldsMapping | OAFFieldsMapping = {},
        sortby: Optional[list[SortDict]] = None,
    ) -> GeojsonFeatureCollectionDict | GeojsonFeatureDict:
        """
        Return a geojson feature if the client queried for items/{itemId} or a feature collection if they queried for items/ even if the result is only one item
        """
        features: list[geojson_pydantic.Feature] = []

        for loc in self.locations:
            feature: GeojsonFeatureDict = {
                "type": "Feature",
                "properties": loc.model_dump(exclude={"latitude", "longitude"}),
                "geometry": {
                    "type": "Point",
                    "coordinates": [loc.longitude, loc.latitude],
                }
                if not skip_geometry
                else None,
                "id": loc.stationId,
            }

            serialized_feature = geojson_pydantic.Feature.model_validate(feature)
            if properties:
                # narrow the FieldsMapping type here manually since properties is a query arg for oaf and thus we know that OAFFieldsMapping must be used
                fields_mapping = cast(OAFFieldsMapping, fields_mapping)
                if not all_properties_found_in_feature(
                    serialized_feature, properties, fields_mapping
                ):
                    continue

            if select_properties:
                filter_out_properties_not_selected(
                    serialized_feature, select_properties
                )

            features.append(serialized_feature)

        if sortby:
            sort_by_properties_in_place(features, sortby)

        geojson_pydantic.FeatureCollection(
            type="FeatureCollection",
            features=features,
        )
        if itemsIDSingleFeature:
            assert len(features) == 1, (
                "The user queried a single item but we have more than one present. This is a sign that filtering by locationid wasn't done properly"
            )
            return GeojsonFeatureDict(**features[0].model_dump(exclude_unset=True))
        return GeojsonFeatureCollectionDict(
            **{
                "type": "FeatureCollection",
                "features": [
                    feature.model_dump(by_alias=True, exclude_unset=True)
                    for feature in features
                ],
            }
        )

    @TRACER.start_as_current_span("geometry_filter")
    def _filter_by_geometry(
        self,
        geometry: Optional[shapely.geometry.base.BaseGeometry],
        # Vertical level
        z: Optional[str] = None,
    ):
        """
        Filter a list of locations by any arbitrary geometry; if they are not inside of it, drop their data
        """
        indices_to_pop = set()
        parsed_z = parse_z(str(z)) if z else None

        for i, v in enumerate(self.locations):
            elevation = v.elevation

            if elevation is None:
                indices_to_pop.add(i)
                continue

            if parsed_z:
                match parsed_z:
                    case [ZType.RANGE, x]:
                        if elevation < x[0] or elevation > x[1]:
                            indices_to_pop.add(i)
                    case [ZType.SINGLE, x]:
                        if elevation != x[0]:
                            indices_to_pop.add(i)
                    case [ZType.ENUMERATED_LIST, x]:
                        if elevation not in x:
                            indices_to_pop.add(i)
                    case _:
                        assert_never(parsed_z)

            if geometry:
                if v.latitude is None or v.longitude is None:
                    indices_to_pop.add(i)
                    continue

                locationPoint = shapely.geometry.point.Point(
                    # need to convert the pydantic model to a simple
                    # dict to use shapely with it
                    [v.longitude, v.latitude]
                )

                if not geometry.contains(locationPoint):
                    indices_to_pop.add(i)

        # by reversing the list we pop from the end so the
        # indices will be in the correct even after removing items
        for i in sorted(indices_to_pop, reverse=True):
            self.locations.pop(i)

        return self

    def to_covjson(
        self,
        fieldMapper: EDRFieldsMapping,
        datetime_: Optional[str],
        select_properties: Optional[list[str]],
    ) -> CoverageCollectionDict:
        stationTriples: list[str] = [
            location.stationTriplet
            for location in self.locations
            if location.stationTriplet
        ]

        tripleToGeometry: dict[str, longitudeAndLatitude] = {}
        for location in self.locations:
            if location.stationTriplet and location.longitude and location.latitude:
                assert location.longitude and location.latitude
                tripleToGeometry[location.stationTriplet] = (
                    location.longitude,
                    location.latitude,
                )

        # We cast the return value here because we know it will be a CoverageCollectionDict
        covjson_result = CovjsonBuilder(
            stationTriples, tripleToGeometry, fieldMapper, datetime_, select_properties
        ).render()

        return cast(
            CoverageCollectionDict,
            covjson_result,
        )
