""" Defines a common regsitry class model for all Registry items """

import re
from pynamodb.models import Model
from pynamodb.attributes import MapAttribute


class RegistryModel(Model):
    """Common Top-Level Registry Model as a pynamodb Model"""

    def __init__(self, *args, **kwargs):
        # Convert snake_case and kebab-case keys to PascalCase keys
        kwargs = {self._convert_key(k): v for k, v in kwargs.items()}
        super().__init__(*args, **kwargs)

    def _convert_key(self, key):
        # Convert snake_case and kebab-case keys to PascalCase keys
        attributes = self.get_attributes()
        if hasattr(self, key) or key in attributes:
            return key
        words = re.split("[-_]", key)
        pascal_case_key = "".join(word.capitalize() for word in words)
        return pascal_case_key


class ExtendedMapAttribute(MapAttribute):
    """Convert Keys to CamelCase"""

    def __init__(self, *args, **kwargs):
        # Convert snake_case and kebab-case keys to PascalCase keys
        kwargs = {self._convert_key(k): v for k, v in kwargs.items()}
        super().__init__(*args, **kwargs)

    def _convert_key(self, key):
        # Convert snake_case and kebab-case keys to PascalCase keys
        attributes = self.get_attributes()
        if hasattr(self, key) or key in attributes:
            return key
        words = re.split("[-_]", key)
        pascal_case_key = "".join(word.capitalize() for word in words)
        return pascal_case_key
