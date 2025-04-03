# Western Water Datahub EDR Mappings

This repository maps the various federal water data APIs like the USBR RISE API to OGC EDR using pygeoapi for ETL. It defaults to redis for the caching implementation.

## Usage

- To install dependencies run `make deps`
  - We use uv for dependency management and thus you should have it installed
  - You can however also use the `requirements.txt` as well for quick checks as it is kept up to date automatically
- To run the server run: `make dev`
- To run the redis container for caching, run `docker compose up`
- To run tests run: `make test`

## Limitations

- This repository uses extensive caching to prevent unnecessary fetch requests to RISE. OGC EDR does not map cleanly onto RISE without this.
  - We set a default TTL. However, whenever we need to repopulate the cache, RISE sometimes denies parallelized requests and throws an error saying the server is down for maintenance, which is not the case.

## OGC API Features Spec Compliance

| Provider | Property Filters/Display | Result Type | BBox | Datetime | Sort By | Skip Geometry | CQL | Transactions | CRS |
| -------- | ------------------------ | ----------- | ---- | -------- | ------- | ------------- | --- | ------------ | --- |
| `RISE`   | ✅ / ✅                  | ✅          | ✅   | ✅       | ✅      | ✅            | ❌  | ❌           | ✅  |
| `SNOTEL` | ✅ / ✅                  | ✅          | ✅   | ✅       | ✅      | ✅            | ❌  | ❌           | ✅  |

## OGC EDR Spec Compliance

| Provider | Position | Radius | Area | Cube | Trajectory | Coordidor | Items |
| -------- | -------- | ------ | ---- | ---- | ---------- | --------- | ----- |
| RISE     | ❌       | ❌     | ✅   | ✅   | ❌         | ❌        | ✅    |
| SNOTEL   | ❌       | ❌     | ✅   | ✅   | ❌         | ❌        | ✅    |

### EDR Query Options

| Provider | Coords | Parameter-Name | Datetime |
| -------- | ------ | -------------- | -------- |
| RISE     | ✅     | ✅             | ✅       |
| SNOTEL   | ✅     | ✅             | ✅       |
