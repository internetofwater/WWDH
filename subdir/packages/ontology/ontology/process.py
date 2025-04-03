# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from pygeoapi.process.base import BaseProcessor
import logging
from pygeoapi.process.base import ProcessorExecuteError
from ontology.metadata import PROCESS_METADATA
from ontology.ontology import ONTOLOGY

LOGGER = logging.getLogger(__name__)


class OntologyProcessor(BaseProcessor):
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
        parameters = data.get("parameters")

        if parameters is None:
            raise ProcessorExecuteError(
                "Cannot process an ontology request without a parameter"
            )

        value = ONTOLOGY[parameters]

        return "application/json", {"id": "ontology", "decoded": value}
