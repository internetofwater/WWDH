# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

FROM python:3.12

WORKDIR /pygeoapi

# Install GDAL and dependencies
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install the additional requirements for the RISE mapping
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# Install the RISE plugin
RUN pip install .
RUN pygeoapi openapi generate /pygeoapi/local.config.yml --output-file /pygeoapi/local.openapi.yml

# Hot reloading (remove for production)
ENTRYPOINT [ "pygeoapi", "serve", "--starlette" ]
