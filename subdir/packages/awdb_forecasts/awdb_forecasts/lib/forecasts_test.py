# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from awdb_forecasts.lib.forecasts import ForecastResultCollection


def test_parse_forecasts():
    streamVolumeAdjusted = "SRVO"
    fc = ForecastResultCollection().fetch_all_data(
        station_triplets=["09379900:AZ:USGS"], element_code=streamVolumeAdjusted
    )
    vals = fc["09379900:AZ:USGS"][0].forecastValues
    assert vals
