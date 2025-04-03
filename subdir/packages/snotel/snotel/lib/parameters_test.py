# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from snotel.lib.parameters import ParametersCollection


def test_parameter_collection():
    assert ParametersCollection()


def test_get_fields():
    fields = ParametersCollection().get_fields()
    fields["WSPD"] = {
        "title": "WIND SPEED OBSERVED",
        "type": "string",
        "description": "wind speed",
        "x-ogc-unit": "mph",
    }
