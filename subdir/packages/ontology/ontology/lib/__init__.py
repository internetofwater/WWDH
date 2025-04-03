# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

PROCESS_METADATA = {
    "version": "0.1.0",
    "id": "hello-world",
    "title": {"en": "Hello World", "fr": "Bonjour le Monde"},
    "description": {
        "en": "An example process that takes a name as input, and echoes "
        "it back as output. Intended to demonstrate a simple "
        "process with a single literal input.",
        "fr": "Un exemple de processus qui prend un nom en entrée et le "
        "renvoie en sortie. Destiné à démontrer un processus "
        "simple avec une seule entrée littérale.",
    },
    "jobControlOptions": ["sync-execute", "async-execute"],
    "keywords": ["hello world", "example", "echo"],
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
        "parameters": {
            "title": "parameters",
            "description": "The name of the person or entity that you wish to"
            "be echoed back as an output",
            "schema": {"type": "string"},
            "minOccurs": 1,
            "maxOccurs": 1,
            "keywords": ["full name", "personal"],
        },
    },
    "outputs": {
        "echo": {
            "title": "Hello, world",
            "description": 'A "hello world" echo with the name and (optional)'
            " message submitted for processing",
            "schema": {"type": "object", "contentMediaType": "application/json"},
        }
    },
    "example": {
        "inputs": {
            "name": "World",
            "message": "An optional message.",
        }
    },
}
