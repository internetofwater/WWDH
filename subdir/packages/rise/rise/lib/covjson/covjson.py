# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import logging
from typing import Any, Tuple

from com.helpers import EDRFieldsMapping, await_
from rise.lib.covjson.template import COVJSON_TEMPLATE
from rise.lib.covjson.types import (
    CoverageCollectionDict,
    CoverageDict,
    CoverageRangeDict,
    ParameterDict,
)
from rise.lib.cache import RISECache
from rise.lib.add_results import DataNeededForCovjson

LOGGER = logging.getLogger(__name__)


def _generate_coverage_item(
    location_type: str,
    coords: list[Any] | Tuple[float, float],
    times: list[str | None],
    paramToCoverage: dict[str, CoverageRangeDict],
) -> CoverageDict:
    # if it is a point it will have different geometry

    if location_type == "Point":
        # z = location_feature["attributes"]["elevation"]
        x, y = coords[0], coords[1]

        coverage_item: CoverageDict = {
            "type": "Coverage",
            "domainType": "PointSeries",
            "domain": {
                "type": "Domain",
                "axes": {
                    "x": {"values": [x]},
                    "y": {"values": [y]},
                    "t": {"values": times},
                },
            },
            "ranges": paramToCoverage,
        }

    else:
        coverage_item: CoverageDict = {
            "type": "Coverage",
            "domainType": "PolygonSeries",
            "domain": {
                "type": "Domain",
                "axes": {
                    "composite": {
                        "dataType": location_type,
                        "coordinates": ["x", "y"],
                        "values": [coords],
                    },
                    "t": {"values": times},
                },
            },
            "ranges": paramToCoverage,
        }

    return coverage_item


class CovJSONBuilder:
    """A helper class for building CovJSON from a Rise JSON Response"""

    def __init__(self, cache: RISECache):
        self._cache = cache

    def _insert_parameter_metadata(
        self,
        paramsToGeoJsonOutput: EDRFieldsMapping,
        location_response: list[DataNeededForCovjson],
    ):
        relevant_parameters = []
        for location in location_response:
            for p in location.parameters:
                relevant_parameters.append(p.parameterId)

        paramNameToMetadata: dict[str, ParameterDict] = {}

        for param_id in relevant_parameters:
            if param_id not in paramsToGeoJsonOutput:
                LOGGER.error(
                    f"Could not find metadata for {param_id} in {sorted(paramsToGeoJsonOutput.keys())}"
                )
                continue

            associatedData = paramsToGeoJsonOutput[param_id]

            _param: ParameterDict = {
                "type": "Parameter",
                "description": {"en": associatedData["description"]},
                "unit": {"symbol": associatedData["x-ogc-unit"]},
                "observedProperty": {
                    "id": param_id,
                    "label": {"en": associatedData["title"]},
                },
            }
            natural_language_name = associatedData["title"]
            paramNameToMetadata[natural_language_name] = _param

        return paramNameToMetadata

    def _get_coverages(
        self,
        locationsWithResults: list[DataNeededForCovjson],
        paramsToGeoJsonOutput: EDRFieldsMapping,
    ) -> list[CoverageDict]:
        """Return the data needed for the 'coverage' key in the covjson response"""

        coverages = []
        for location_feature in locationsWithResults:
            for param in location_feature.parameters:
                if not (  # ensure param contains data so it can be used for covjson
                    param.timeseriesResults
                ):
                    # Since coveragejson does not allow a parameter without results,
                    # we can skip adding the parameter/location combination all together
                    continue

                value = paramsToGeoJsonOutput.get(str(param.parameterId))
                if not value:
                    continue
                naturalLanguageName = value["title"]

                range: dict[str, CoverageRangeDict] = {
                    naturalLanguageName: {
                        "axisNames": ["t"],
                        "dataType": "float",
                        "shape": [len(param.timeseriesResults)],
                        "values": param.timeseriesResults,
                        "type": "NdArray",
                    }
                }

                coverage_item = _generate_coverage_item(
                    location_feature.locationType,
                    location_feature.geometry,
                    param.timeseriesDates,
                    range,
                )

                coverages.append(coverage_item)

        return coverages

    def fill_template(
        self,
        location_response: list[DataNeededForCovjson],
        select_properties: list[str] | None,
    ) -> CoverageCollectionDict:
        templated_covjson: CoverageCollectionDict = COVJSON_TEMPLATE
        paramIdToMetadata: EDRFieldsMapping = await_(
            self._cache.get_or_fetch_parameters()
        )
        if select_properties:
            paramIdToMetadata = {
                k: v for k, v in paramIdToMetadata.items() if k in select_properties
            }

        templated_covjson["coverages"] = self._get_coverages(
            location_response, paramIdToMetadata
        )
        templated_covjson["parameters"] = self._insert_parameter_metadata(
            paramIdToMetadata, location_response=location_response
        )

        # don't actually care about the pydantic model, we just want to use it to validate
        # PydanticCoverageCollection.model_validate(templated_covjson)
        return templated_covjson
