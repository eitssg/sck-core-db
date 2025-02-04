"""Defines a common regsitry class model for all Registry items"""

import re
from pynamodb.models import Model
from pynamodb.attributes import MapAttribute


class RegistryModel(Model):
    """Common Top-Level Registry Model as a pynamodb Model"""

    def __init__(self, *args, **kwargs):
        # Convert snake_case and kebab-case keys to PascalCase keys
        kwargs = self.convert_keys(**kwargs)
        super().__init__(*args, **kwargs)

    def convert_keys(self, **kwargs) -> dict:
        # Convert snake_case and kebab-case keys to PascalCase keys
        return {self._convert_key(k): v for k, v in kwargs.items()}

    def _convert_key(self, key):
        # Convert snake_case and kebab-case keys to PascalCase keys
        attributes = self.get_attributes()
        if hasattr(self, key) or key in attributes:
            return key
        words = re.split("[-_]", key)
        pascal_case_key = "".join(word.capitalize() for word in words)
        return pascal_case_key

    def convert_keys_alt(self, **kwargs) -> dict:
        # Convert snake_case and kebab-case keys to PascalCase keys.  Does NOT handle camelCase
        rv = {}
        for k, v in kwargs.items():
            nk = self._convert_key(k)
            if isinstance(v, dict):
                rv[nk] = self.convert_keys(**v)
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        v[i] = self.convert_keys(**item)
            else:
                rv[nk] = v
        return rv


class ExtendedMapAttribute(MapAttribute):
    """Convert Keys to CamelCase"""

    def __init__(self, *args, **kwargs):
        # Convert snake_case and kebab-case keys to PascalCase keys
        kwargs = self.convert_keys(**kwargs)
        super().__init__(*args, **kwargs)

    def convert_keys(self, **kwargs) -> dict:
        # Convert snake_case and kebab-case keys to PascalCase keys
        return {self._convert_key(k): v for k, v in kwargs.items()}

    def _convert_key(self, key):
        # Convert snake_case and kebab-case keys to PascalCase keys
        attributes = self.get_attributes()
        if hasattr(self, key) or key in attributes:
            return key
        words = re.split("[-_]", key)
        pascal_case_key = "".join(word.capitalize() for word in words)
        return pascal_case_key
