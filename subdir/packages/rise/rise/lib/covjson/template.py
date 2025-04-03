# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

# The template that we will fill in with data and return to the user
from rise.lib.covjson.types import CoverageCollectionDict

COVJSON_TEMPLATE: CoverageCollectionDict = {
    "type": "CoverageCollection",
    ## CoverageJSON makes us specify a list of parameters that are relevant for the entire coverage collection
    "parameters": {},
    "referencing": [
        {
            "coordinates": ["x", "y"],
            "system": {
                "type": "GeographicCRS",
                "id": "http://www.opengis.net/def/crs/OGC/1.3/CRS84",
            },
        },
        {
            "coordinates": ["z"],
            "system": {
                "type": "VerticalCRS",
                "cs": {
                    "csAxes": [
                        {
                            "name": {"en": "time"},
                            "direction": "down",
                            "unit": {"symbol": "time"},
                        }
                    ]
                },
            },
        },
        {
            "coordinates": ["t"],
            "system": {"type": "TemporalRS", "calendar": "Gregorian"},
        },
    ],
    "coverages": {},  # type: ignore this w/ static type checks since it is a template and intended to be empty
}
