# AWDB Forecasts

Forecasts don't map cleanly to EDR since they have divided by timeperiod so we need to create extra collections

- Create these collections:
  - January 01 - March 31 AWDB Forecast
  - April 01 - June 30 AWDB Forecast
  - July 01 - September 30 AWDB Forecast
  - October 01 - December 31 AWDB Forecast

Each collection time period maps to the forecast period argument

![forecast period](image.png)

Each collection has all parameters.

Timefilter for EDR queries applies to the `beginPublicationDate` and `endPublicationDate` query params.
