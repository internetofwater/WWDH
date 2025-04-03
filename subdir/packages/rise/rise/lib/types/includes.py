# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional

"""
This file contains the pydantic models for specifically the
'includes:' key of the Rise JSON response
"""


class RelationshipDataDict(BaseModel):
    id: str
    type: str


class RelationshipData(BaseModel):
    data: list[RelationshipDataDict]

    @field_validator("data", check_fields=True, mode="before")
    @classmethod
    def ensure_list(cls, data):
        """Ensure data is standardized as a list since it can be a list of dicts or an unnested dict"""
        if not isinstance(data, list):
            return [data]
        return data


class IncludeRelationships(BaseModel):
    catalogRecord: Optional[RelationshipData] = None
    location: Optional[RelationshipData] = None
    catalogItems: Optional[RelationshipData] = None
    parameter: Optional[RelationshipData] = None


class LocationIncluded(BaseModel):
    id: str
    attributes: dict
    type: Literal["CatalogRecord", "Location", "CatalogItem"]
    relationships: IncludeRelationships = Field(default_factory=IncludeRelationships)
