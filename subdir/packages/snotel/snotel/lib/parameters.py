# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from com.cache import RedisCache
from com.helpers import EDRFieldsMapping, await_
from awdb_com.types import ReferenceDataDTO


class ParametersCollection:
    """
    A helper class used for fetching data about parameters;
    parameters are known as `reference-data` in the upstream SNOTEL API
    """

    parameters: ReferenceDataDTO

    def __init__(self) -> None:
        self.cache = RedisCache()
        result = await_(
            self.cache.get_or_fetch(
                "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/reference-data"
            )
        )
        self.parameters = ReferenceDataDTO.model_validate(result)

    def get_fields(self) -> EDRFieldsMapping:
        fields: EDRFieldsMapping = {}
        assert self.parameters.elements
        for parameter in self.parameters.elements:
            # We add asserts here since depending on query params it could be possible to not
            # have these in the response; however, given the default query params, we expect them
            assert parameter.code
            assert parameter.name
            description = parameter.description or parameter.physicalElementName
            assert description
            assert parameter.storedUnitCode
            fields[parameter.code] = {
                "title": parameter.name,
                "type": "string",
                "description": description,
                "x-ogc-unit": parameter.storedUnitCode,
            }

        return fields
