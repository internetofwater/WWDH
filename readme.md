# RISE EDR Mappings

This repository maps the USBR RISE API to OGC EDR using pygeoapi for ETL. It defaults to redis for the caching implementation.

To run

```
docker compose up
```

You can run tests by entering the container shell and running pytest or opening the provided devcontainer and running the vscode test runner. View the [docs](./docs/) for more information.

## Limitations

- This repository uses extensive caching to prevent unnecessary fetch requests to RISE. OGC EDR does not map cleanly onto RISE without this. 
    - We set a default TTL of 24 hours. However, whenever we need to repopulate the cache, RISE sometimes denies parallelized requests and throws an error saying the server is down for maintenance, which is not the case.