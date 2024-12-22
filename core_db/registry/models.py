""" Defines a common regsitry class model for all Registry items """

import re
from pynamodb.models import Model


class RegistryModel(Model):
    """Common Top-Level Registry Model as a pynamodb Model"""

    class Meta:
        """
        :no-index:
        """

        pass

    def __init__(self, *args, **kwargs):
        # Convert lowercase keys to camelCase keys
        kwargs = {self._convert_key(k): v for k, v in kwargs.items()}
        super().__init__(*args, **kwargs)

    def _convert_key(self, key):
        # Convert lowercase keys to camelCase keys
        words = re.split("[-_]", key)
        camel_case_key = words[0] + "".join(word.capitalize() for word in words[1:])
        return camel_case_key
