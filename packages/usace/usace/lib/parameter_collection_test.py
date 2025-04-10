# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from usace.lib.parameter_collection import ParameterCollection


def test_parameter_collection():
    pc = ParameterCollection()
    assert pc.parameters
    fields = pc.get_fields()

    assert "Conc-Acidity" in fields
    assert "Cond" in fields
