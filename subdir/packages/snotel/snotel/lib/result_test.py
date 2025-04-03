# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import pytest
from snotel.lib.parameters import ParametersCollection
from snotel.lib.result import ResultCollection


@pytest.fixture
def fields():
    res = ParametersCollection().get_fields()
    assert "TMIN" in res
    return res


def test_get_one_element_metadata(fields):
    collection = ResultCollection()._fetch_metadata_for_elements(
        station_triplets=["908:WA:SNTL"], element_code="TMIN"
    )
    assert collection[0].data
    assert collection[0].data[0].stationElement


def test_get_all_data(fields):
    collection = ResultCollection().fetch_all_data(
        station_triplets=["908:WA:SNTL", "301:CA:SNTL"],
        element_code="*",
    )
    assert len(collection) == 2
    assert collection["908:WA:SNTL"].data
    assert collection["301:CA:SNTL"].data
