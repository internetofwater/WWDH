# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from com.env import REDIS_HOST, REDIS_PORT
from pygeoapi.process.base import BaseProcessor
import logging
from pygeoapi.process.base import ProcessorExecuteError
from ontology.metadata import PROCESS_METADATA
import redis

LOGGER = logging.getLogger(__name__)


class CacheBustProcessor(BaseProcessor):
    """Hello World Processor example"""

    def __init__(self, processor_def):
        """
        Initialize object

        :param processor_def: provider definition

        :returns: pygeoapi.process.hello_world.HelloWorldProcessor
        """

        super().__init__(processor_def, PROCESS_METADATA)
        self.supports_outputs = True

    def execute(self, data, outputs=None):
        urls = data.get("urls")

        if urls is None:
            raise ProcessorExecuteError(
                "Cannot process an ontology request without a parameter"
            )

        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        return "application/json", {
            "id": "cache_buster",
            "": urls,
        }
        # client.flushall()
