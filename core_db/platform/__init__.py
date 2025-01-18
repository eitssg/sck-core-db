"""Module to hold the distribution files for the core-automation database """

templates = [
    "core-automation-api-facts.yaml",
    "core-automation-api-items.yaml",
    "core-automation-api-roles.yaml",
]

specs = ["deployspec.yaml", "teardownspec.yaml"]

__all__ = ["templates", "specs"]
