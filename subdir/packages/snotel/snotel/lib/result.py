# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from typing import Optional
from com.cache import RedisCache
from com.datetime import datetime_from_iso
from com.helpers import await_, parse_date
from awdb_com.types import StationDataDTO
from datetime import datetime, timezone


class ResultCollection:
    """
    A helper class for fetching results and processing them

    In snotel results are called `data`
    """

    results: list[StationDataDTO]

    def __init__(
        self,
    ):
        self.cache = RedisCache()

    def _fetch_metadata_for_elements(
        self, station_triplets: list[str], element_code: str
    ):
        """
        Fetch the elements for a series of station triplets; since no begin or end date is specified it will return just a small amount of data
        but still include the begin and end date in the response
        """
        assert station_triplets, "No station triplets provided"
        station_triplets_comma_separated = ",".join(station_triplets)
        assert element_code
        url = f"https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data?elements={element_code}&stationTriplets={station_triplets_comma_separated}"
        result = await_(self.cache.get_or_fetch(url))
        assert "error" not in result, result
        return [StationDataDTO.model_validate(res) for res in result]

    def _get_earliest_and_latest_date_from_filter(
        self, datetime_filter: str
    ) -> tuple[datetime, datetime]:
        """
        In EDR you can specify a format like ../1910-01-01
        to fetch all data up to and including 1910-01-01

        However, SNOTEL fails if you try to pass in datetime.min/max
        since it apparently is too early/late, thus we have to set it to a reasonable date
        This function is useful for retrieving that info
        """
        if (
            (parsed_date := parse_date(datetime_filter))
            and isinstance(parsed_date, tuple)
            and len(parsed_date) == 2
        ):
            earliestDate, latestDate = parsed_date
        else:
            earliestDate = latestDate = parsed_date

        earliestDate = max(
            earliestDate,
            datetime_from_iso("1900-01-01"),
        )

        MAGIC_LAST_DATE_FOR_API = "2100-01-01"
        latestDate = min(
            latestDate,
            datetime_from_iso(MAGIC_LAST_DATE_FOR_API),
        )

        return earliestDate, latestDate

    def fetch_all_data(
        self,
        station_triplets: list[str],
        element_code: str = "*",
        force_fetch: bool = False,
        datetime_filter: Optional[str] = None,
    ) -> dict[str, StationDataDTO]:
        """
        Given a list of station triples, fetch all associated data for them
        """
        # If there aren't any stations in the list there is nothing to fetch
        if not station_triplets:
            return {}

        metadata = self._fetch_metadata_for_elements(station_triplets, element_code)
        urls_for_full_data = []
        for station in metadata:
            if not station.data:
                continue

            earliestDate, latestDate = (
                (
                    datetime.max.replace(tzinfo=timezone.utc),
                    datetime.min.replace(tzinfo=timezone.utc),
                )
                if not datetime_filter
                else self._get_earliest_and_latest_date_from_filter(datetime_filter)
            )
            elements: list[str] = []
            for datastream in station.data:
                if not datastream.stationElement:
                    continue

                if not datetime_filter:
                    start, end = (
                        datastream.stationElement.beginDate,
                        datastream.stationElement.endDate,
                    )
                    assert start and end
                    startDate = datetime_from_iso(start)
                    endDate = datetime_from_iso(end)
                    if startDate < earliestDate:
                        earliestDate = startDate
                    if endDate > latestDate:
                        latestDate = endDate

                assert datastream.stationElement.elementCode
                elements.append(datastream.stationElement.elementCode)

            assert earliestDate < latestDate, (
                f"{earliestDate} was not before {latestDate}"
            )
            full_results_url = f"https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data?beginDate={earliestDate.strftime('%Y-%m-%d %H:%M:%S')}&endDate={latestDate.strftime('%Y-%m-%d %H:%M:%S')}&elements={','.join(elements)}&stationTriplets={station.stationTriplet}"
            urls_for_full_data.append(full_results_url)

        result: dict[str, dict] = await_(
            self.cache.get_or_fetch_group(urls_for_full_data, force_fetch)
        )
        for url, res in result.items():
            assert "error" not in res, (url, res)

        stationToData: dict[str, StationDataDTO] = {}
        for _url, datastreams in result.items():
            for item in datastreams:
                data = StationDataDTO.model_validate(item)
                assert data.stationTriplet
                stationToData[data.stationTriplet] = data

        return stationToData
