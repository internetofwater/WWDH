# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import pytest
import requests


@pytest.fixture(scope="session", autouse=True)
def setup_before_tests():
    # RISE has issues with ipv6 connections and has much better
    # performance with it disabled
    requests.packages.urllib3.util.connection.HAS_IPV6 = False  # type: ignore
