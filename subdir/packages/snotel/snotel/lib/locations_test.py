# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT


from snotel.lib.locations import SnotelLocationCollection


def test_filter_by_id():
    brightonInSaltLakeCounty = "361"
    newCollection = SnotelLocationCollection().drop_all_locations_but_id(
        brightonInSaltLakeCounty
    )
    assert len(newCollection.locations) == 1


def test_get_no_data_from_very_old_datetime():
    newCollection = SnotelLocationCollection().select_date_range("1800-01-01")
    assert len(newCollection.locations) == 0


def test_get_no_data_from_very_old_range():
    newCollection = SnotelLocationCollection().select_date_range(
        "1700-01-01/1800-01-01"
    )
    assert len(newCollection.locations) == 0


def test_ranges_are_mutually_exclusive():
    items_after_1980_01_01 = SnotelLocationCollection().select_date_range(
        "1980-01-02/.."
    )
    assert len(items_after_1980_01_01.locations) == 414
