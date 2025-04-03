# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from typing import Optional


from typing import Dict


def merge_pages(pages: Dict[str, dict]) -> dict:
    """Given multiple different pages of data, merge them together."""

    combined_data = {}

    for content in pages.values():
        for key in ("data", "included"):
            if key in content:
                combined_data.setdefault(key, []).extend(content[key])

    return combined_data


def no_duplicates_in_pages(pages: dict):
    found = {}
    for url in pages:
        for data in pages[url]["data"]:
            id = data["attributes"]["_id"]
            assert id not in found, (
                f"{id} with name {data['attributes']['locationName']} was found in both {url} and {found[id]}. You may need to clear the cache for {found[id]}"
            )
            found[id] = url


def flatten_values(input: dict[str, list]) -> list:
    """Given a dict of lists, flatten them into a single list"""
    output = []
    for _, v in input.items():
        for i in v:
            output.append(i)

    return output


def get_only_key(mapper: dict):
    value = list(mapper.values())[0]
    return value


def get_trailing_id(url: str) -> str:
    return url.split("/")[-1]


def getResultUrlFromCatalogUrl(url: str, datetime_: Optional[str]) -> str:
    """Create the result url given a catalog item url and the datetime we want to filter by"""
    base = f"https://data.usbr.gov/rise/api/result?itemId={get_trailing_id(url)}"

    if datetime_:
        parsed_date = datetime_.split("/")
        if len(parsed_date) == 2:
            after_date = parsed_date[0]
            before_date = parsed_date[1]
        else:
            # In RISE we are allowed to filter broadly by using the same start and end date
            # i.e. 2017-01-01 as the start and end would match on 2017-01-01:00:00:00 - 2017-01-01:23:59:59
            after_date = parsed_date[0]
            before_date = parsed_date[0]

        base += f"&dateTime%5Bbefore%5D={before_date}"
        base += f"&dateTime%5Bafter%5D={after_date}"

    return base
