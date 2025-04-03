# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

PROCESS_METADATA = {
    "version": "0.1.0",
    "id": "resolve-ontology",
    "title": {"en": "Resolve Ontology"},
    "description": {
        "en": "An example process that takes a name as input, and echoes "
        "it back as output. Intended to demonstrate a simple "
        "process with a single literal input.",
    },
    "jobControlOptions": ["sync-execute", "async-execute"],
    "keywords": ["Semantic web", "ontology", "parameters"],
    "links": [
        {
            "type": "text/html",
            "rel": "about",
            "title": "information",
            "href": "https://example.org/process",
            "hreflang": "en-US",
        }
    ],
    "inputs": {
        "name": {
            "title": "parameter",
            "description": "The name of the parameter you wish to resolve into the collection specific term",
            "schema": {"type": "array", "items": {"type": "string"}},
            "minOccurs": 1,
            "maxOccurs": 1,
            "keywords": ["ontology", "parameter"],
        },
    },
    "outputs": {
        "decoding": {
            "title": "Hello, world",
            "description": 'A "hello world" echo with the name and (optional)'
            "message submitted for processing",
            "schema": {"type": "object", "contentMediaType": "application/json"},
        }
    },
    "example": {
        "inputs": {
            "name": "decoded parameters",
            "message": "An optional message.",
        }
    },
}
