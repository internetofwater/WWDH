For the optimal path of a location query it seems like you can

- fetch `location/X`
  - use the `include` query param to include the associate catalog items and catalog records
  - join the response to make sure each catalog item is associated with the proper location
- for catalogitem use the catalogitem number as a query param for the `itemId` field in the `result/` endpoint
  - my understanding is that we can also use `locationId` here. However, if we don't have the catalogitem and thus don't filter by `itemId` it seems like we would potentially overfetch a ton if we only want the results of a single catalogitem.
- join the `result/` value with the location metadata/geometry
- return coveragejson according to the EDR spec
