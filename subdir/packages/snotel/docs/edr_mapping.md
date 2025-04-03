# EDR Mappings

The process to generate EDR mappings for snotel is relatively straightforward. Locations, metadata, and timeseries data are separated so they need to be joined. Howevever, there is no pagination.

- `locations/`:
  - _in parallel_:
    - fetch `stations/` with `stationNames=*`
    - cache this - will include all geometry data for plotting/filtering
    - fetch `reference-data/` to get all parameter metadata
      - cache this
      - appears that the `elements` key is the one that stores all the parameter information
      - `units` has all the units for the actual timeseries
      - join each relevant location with the associated reference-data
  - _in parallel_:
    - fetch all `data/$ELEMENT_NAME` to get the associated elements for each
    - merge into a final table - generate covjson

# OAF Mappings

- fetch `stations/` with `stationNames=*`

# Docs

Docs for snotel can be found via the swagger ui here: https://wcc.sc.egov.usda.gov/awdbRestApi/swagger-ui/index.html
