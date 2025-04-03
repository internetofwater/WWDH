# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from com.helpers import get_oaf_fields_from_pydantic_model, parse_bbox, parse_z
from pydantic import BaseModel
import pytest
from rise.lib.types.helpers import ZType
import shapely.wkt


def test_parse_bbox():
    bbox = ["-6.0", "50.0", "-4.35", "52.0"]
    parse_result = parse_bbox(bbox)
    shapely_bbox = parse_result[0]
    assert shapely_bbox
    zval = parse_result[1]
    assert not zval

    wkt = "POINT(-5.0 51)"
    single_point = shapely.wkt.loads(wkt)

    parse_result = parse_bbox(bbox)
    if parse_result[0]:
        assert parse_result[0].contains(single_point)
    else:
        assert False


def test_z_parse():
    assert (ZType.SINGLE, [10]) == parse_z("10")
    assert (ZType.RANGE, [10, 20]) == parse_z("10/20")
    assert (ZType.ENUMERATED_LIST, [10, 20, 30]) == parse_z("10,20,30")

    assert (ZType.ENUMERATED_LIST, [100, 150]) == parse_z("R2/100/50")

    with pytest.raises(Exception):
        parse_z("10/20/30")

    with pytest.raises(Exception):
        parse_z("10//30")

    with pytest.raises(Exception):
        parse_z("10,20,30,")


def test_get_oaf_fields_from_pydnatic():
    class DummyModel(BaseModel):
        field1: int
        field2: str
        field3: float
        field4: list  # don't include types that can't be serialized to the 3 types

    mapping = get_oaf_fields_from_pydantic_model(DummyModel)
    assert mapping["field1"]["type"] == "integer"
    assert mapping["field2"]["type"] == "string"
    assert mapping["field3"]["type"] == "number"
    assert "field4" not in mapping
