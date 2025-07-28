"""Defines a common registry class model for all Registry items"""

import re
from pynamodb.models import Model
from pynamodb.attributes import MapAttribute

import core_framework as util


class RegistryModel(Model):
    """Common Top-Level Registry Model as a pynamodb Model"""

    class Meta:
        """
        Meta class for RegistryModel.

        This class can be extended by specific registry models to define
        region, host, and other PynamoDB model settings.
        """

        # Default region and host can be set here if needed
        region = util.get_dynamodb_region()
        host = util.get_dynamodb_host()
        read_capacity_units = 1
        write_capacity_units = 1

    # Pre-compile regex pattern to avoid recompilation on every call
    _KEY_SPLIT_PATTERN = re.compile(r"[-_]")

    def __init__(self, *args, **kwargs):
        # Convert snake_case and kebab-case keys to PascalCase keys
        kwargs = self.convert_keys(**kwargs)
        super().__init__(*args, **kwargs)

    def convert_keys(self, **kwargs) -> dict:
        # Convert snake_case and kebab-case keys to PascalCase keys
        if not kwargs:
            return kwargs
        attributes = self.get_attributes()
        return {self._convert_key_with_attrs(k, attributes): v for k, v in kwargs.items()}

    def _convert_key_with_attrs(self, key: str, attributes: dict) -> str:
        # Convert snake_case and kebab-case keys to PascalCase keys
        if hasattr(self, key) or key in attributes:
            return key
        words = self._KEY_SPLIT_PATTERN.split(key)
        return "".join(word.capitalize() for word in words)

    def _convert_key(self, key):
        # Legacy method - for backward compatibility
        attributes = self.get_attributes()
        return self._convert_key_with_attrs(key, attributes)


class ExtendedMapAttribute(MapAttribute):
    """Convert Keys to PascalCase in MapAttributes"""

    # Add the same compiled regex pattern
    _KEY_SPLIT_PATTERN = re.compile(r"[-_]")

    def __init__(self, *args, **kwargs):
        # Convert snake_case and kebab-case keys to PascalCase keys
        kwargs = self.convert_keys(**kwargs)
        super().__init__(*args, **kwargs)

    def convert_keys(self, **kwargs) -> dict:
        # Convert snake_case and kebab-case keys to PascalCase keys
        if not kwargs:
            return kwargs
        attributes = self.get_attributes()
        return {self._convert_key_with_attrs(k, attributes): v for k, v in kwargs.items()}

    def _convert_key_with_attrs(self, key: str, attributes: dict) -> str:
        # Convert snake_case and kebab-case keys to PascalCase keys
        if hasattr(self, key) or key in attributes:
            return key
        words = self._KEY_SPLIT_PATTERN.split(key)
        return "".join(word.capitalize() for word in words)

    def _convert_key(self, key):
        # Legacy method
        attributes = self.get_attributes()
        return self._convert_key_with_attrs(key, attributes)
