# Documentation for the RISE API EDR Mapping

[EDR](https://docs.ogc.org/is/19-086r5/19-086r5.html) is an OGC API that allows a user to filter locations by parameters and their associated data.

- It can return either geojson or coveragejson depending on the endpoint.
  - geojson maps easier to RISE
  - coveragejson requires more complex ETL since it returns both a location geometry and the associated results for each of its parameters

## There are 2 main challenges

- How / when does RISE update data? What is the best way to cache an API call that does not have a `timeStep` update interval?
- How do we optimize the generation of coveragejson?
  - covjson requires returning a location as well as its parameter metadata and results.
  - Is there a better way to get this data besides joining across multiple calls?

## Background for challenges

### Caching

To my understanding, RISE does not provide an TLL/invalidation header for each response in the API.

- You can assume it for some endpoints if a response returns data with a defined update `timeStep` interval.
  - However, we also need to fetch URLs like `/location` for metadata that do not have an update interval, yet may still be updated.
- It is also not always clear when and how data in the API is updated. - (i.e. are old results ever deleted? Is the schema ever changed? Are new results ever created at an interval that is different from what is specified?
  )

It is worth discussing the best way to fill the cache, due to the fact that some coveragejson queries may require too many API calls all at once.

- In our cache implementation we use a hard coded TTL
  - Appears to be a reasonable tradeoff.
  - Reduces complexity on our end so we do not need to check for updates or go into the JSON differently for different endpoints.
  - May need to do other ways of staggering the fetches in case a user requests lots of new data all at once.

### CoverageJson Causes Many API Calls

`/locations/{id}`, `/area` and `/cube` in EDR returns [coveragejson](https://covjson.org/).

- coveragejson lists both location geometry and its associated timerseries data in the same output.
- In RISE, locations are decoupled from their parameters and results into different API calls.
  - This causes more complexity / API calls

#### Example

When the user goes to `http://localhost:5000/collections/rise-edr/locations/1` this pseudo code will be executed:

- fetch `https://data.usbr.gov/rise/api/location/1`
- block until the location is fetched
- for each catalogItem in `https://data.usbr.gov/rise/api/location/1`'s `catalogItem` mapping:
  - async fetch the associated catalogItem then store the necessary metadata.
- block until all catalogItems are fetched
- for each catalogItem in `https://data.usbr.gov/rise/api/location/1`'s `catalogItem` mapping:
  - async fetch the associated result
- block until all results are fetched
- join the parameter metadata and results back to the coveragejson output.

This results in `1 + $NUM_CATALOG_ITEMS + $NUM_RESULTS` (where `$NUM_RESULTS <= $NUM_CATALOG_ITEMS`) API calls for one coveragejson output.

This is a bigger challenge for `area/` and `cube/` queries where a user could request many different locations all at once.

- We do limit the impact of this by using `async` fetches and caching
- However, if the cache is stale, we need to do many fetches
  - the API's firewall may block us and return an error via HTML.
  - This makes the entire call fail since it is incomplete.
