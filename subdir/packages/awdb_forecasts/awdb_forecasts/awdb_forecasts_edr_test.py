# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from awdb_forecasts.awdb_forecasts_edr import AwdbForecastsEDRProvider


def test_specific_location():
    topOfAlaskaID15896000 = "15896000"
    p = AwdbForecastsEDRProvider()
    out = p.locations(location_id=topOfAlaskaID15896000)
    assert out
