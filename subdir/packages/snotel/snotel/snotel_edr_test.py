# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import datetime
from snotel.snotel_edr import SnotelEDRProvider

conf = {
    "name": "snotel",
    "title": "Snotel",
    "description": "Snotel",
    "type": "edr",
    "data": "https://wcc.sc.egov.usda.gov/awdbRestApi/swagger-ui/index.html",
}


def test_cube():
    # Example: http://localhost:5000/collections/snotel-edr/cube?bbox=-164.300537,67.195518,-160.620117,68.26125
    p = SnotelEDRProvider(conf)
    bboxCovering1175InAlaska = [-164.300537, 67.195518, -160.620117, 68.26125]
    out = p.cube(bbox=bboxCovering1175InAlaska)
    assert out
    assert len(out["coverages"]) == 13


def test_cube_with_multiple_locations():
    # Example: http://localhost:5000/collections/snotel-edr/cube?bbox=-136.499634,58.969836,-134.588013,59.822732
    bboxCoveringAlaska1285andAlaska1176 = [
        -136.499634,
        58.969836,
        -134.588013,
        59.822732,
    ]
    p = SnotelEDRProvider(conf)
    out = p.cube(bbox=bboxCoveringAlaska1285andAlaska1176)
    coveragesIn1176 = 8
    coveragesIn1285 = 7

    assert len(out["coverages"]) == coveragesIn1176 + coveragesIn1285


def test_cube_with_datetime_filter():
    p = SnotelEDRProvider(conf)
    bboxCovering1175InAlaska = [-164.300537, 67.195518, -160.620117, 68.26125]
    out = p.cube(bbox=bboxCovering1175InAlaska, datetime_="2010-01-01/..")
    assert len(out["coverages"]) == 13
    for cov in out["coverages"]:
        for tValue in cov["domain"]["axes"]["t"]["values"]:
            assert tValue >= datetime.datetime(2010, 1, 1).replace(
                tzinfo=datetime.timezone.utc
            )

    out = p.cube(bbox=bboxCovering1175InAlaska, datetime_="2010-01-01/2020-01-01")
    assert len(out["coverages"]) == 13
    for cov in out["coverages"]:
        for tValue in cov["domain"]["axes"]["t"]["values"]:
            assert tValue >= datetime.datetime(2010, 1, 1).replace(
                tzinfo=datetime.timezone.utc
            )
            assert tValue <= datetime.datetime(2020, 1, 1).replace(
                tzinfo=datetime.timezone.utc
            )


def test_cube_with_select_properties():
    p = SnotelEDRProvider(conf)
    bboxCovering1175InAlaska = [-164.300537, 67.195518, -160.620117, 68.26125]
    out = p.cube(
        bbox=bboxCovering1175InAlaska,
        datetime_="2010-01-01/..",
        select_properties=["DUMMY"],
    )
    assert len(out["coverages"]) == 0, (
        "DUMMY is a property that doesn't exist and thus there should be no features returned"
    )
    # We specified a parameter that exists on only one coverage; since all other coverages
    # don't have it, they will be filtered out from the coverage collection and thus only one
    # coverage will be returned
    out = p.cube(
        bbox=bboxCovering1175InAlaska,
        datetime_="2010-01-01/..",
        select_properties=["TAVG"],
    )
    assert len(out["coverages"]) == 1
    assert len(out["parameters"]) == 1
