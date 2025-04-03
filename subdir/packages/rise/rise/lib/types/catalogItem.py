# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import logging
from typing import Literal, Optional

from pydantic import BaseModel, Field

LOGGER = logging.getLogger(__name__)


class CatalogItemRelationships(BaseModel):
    parameter: Optional[dict[Literal["data"], dict[Literal["type", "id"], str]]] = None
    catalogRecord: dict[Literal["data"], dict[Literal["type", "id"], str]]


class CatalogItemAttributes(BaseModel):
    id: int = Field(..., alias="_id")
    itemTitle: str
    itemDescription: str

    parameterName: Optional[str]
    parameterId: Optional[int]
    parameterTimestep: Optional[str]

    parameterUnit: Optional[str]
    parameterTransformation: Optional[str]
    dataStructure: str
    matrix: dict


class CatalogItemData(BaseModel):
    id: str
    type: Literal["CatalogItem"]
    attributes: CatalogItemAttributes
    relationships: CatalogItemRelationships


class CatalogItemResponse(BaseModel):
    data: CatalogItemData

    def get_parameter(self) -> dict[str, str] | None:
        try:
            parameterName = self.data.attributes.parameterName
            if not parameterName:
                return None

            id = self.data.attributes.parameterId
            # NOTE id is returned as an int but needs to be a string in order to query it
            return {"id": str(id), "name": parameterName}
        except KeyError:
            LOGGER.error(f"Could not find a parameter in {self}")
            return None
