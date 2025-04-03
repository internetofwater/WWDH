# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from typing import Optional
from pydantic import BaseModel, field_validator


class ResultAttributes(BaseModel):
    itemId: int
    locationId: int
    result: Optional[float]
    parameterId: str

    @field_validator("parameterId", check_fields=True, mode="before")
    @classmethod
    def ensure_str(cls, parameterId):
        """Ensure parameterId is standardized as a str since in covjson it must be a str"""
        if not isinstance(parameterId, str):
            return str(parameterId)
        return parameterId

    dateTime: Optional[str]


class ResultData(BaseModel):
    attributes: ResultAttributes


class ResultResponse(BaseModel):
    data: list[ResultData]

    def get_parameter_id(self):
        """We can assume that there is only one parameter in the response since it would not make sense to combine results from different parameters"""
        param = None
        for d in self.data:
            if not param:
                param = d.attributes.parameterId
            elif param != d.attributes.parameterId:
                raise Exception("Multiple parameters in response")

        return self.data[0].attributes.parameterId

    def get_results(self):
        return [d.attributes.result for d in self.data]

    def get_dates(self):
        return [d.attributes.dateTime for d in self.data]
