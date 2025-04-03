It seems like for RISE for pagination it still fetches everything in the backend and then splits into pages, so you should add as many limits to the initial query.

12.75 secs

```
time curl -X 'GET' \
    'https://data.usbr.gov/rise/api/location?include=catalogRecords.catalogItems&page=1&itemsPerPage=25' \
        H 'accept: application/vnd.api+json'
```
