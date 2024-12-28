""" Classes defining the Apps record model for the core-automation-apps table """

import re

from pynamodb.models import Model
from pynamodb.attributes import MapAttribute, UnicodeAttribute

import core_framework as util

from ...constants import CLIENT_PORTFOLIO_KEY, APP_KEY

from ...config import get_table_name, APP_FACTS


class AppFacts(Model):
    """
    Classes defining the Apps record model for the core-automation-apps table

    Args:
        **kwargs: Arbitrary keyword arguments with the attributes
            * ClientPortfolio: str: Client Portfolio (alternate key "client-portfolio")
            * AppRegex: str: App Regex (alternate key "app-regex")
            * Name: str: Name of the app (alternate key "name")
            * Environment: str: Environment of the app (alternate key "environment")
            * Account: str: Account of the app (alternate key "account")
            * Zone: str: Zone of the app (alternate key "zone")
            * ImgeAliases: dict: Image Aliases of the app to reduce bake time (alternate key "image-aliases")
            * Repository: str: Git repository of the app (alternate key "repository")
            * Region: str: Region of the app (alternate key "region")
            * Tags: dict: Tags of the app (alternate key "tags")
            * EnforceValidation: str: Enforce validation of the app (alternate key "enforce-validation")
            * Metadata: dict: Metadata of the app (alternate key "metadata")

    Returns:
        AppFacts: AppFacts object
    """

    class Meta:
        table_name = get_table_name(APP_FACTS)
        region = util.get_region()
        host = util.get_dynamodb_host()
        read_capacity_units = 1
        write_capacity_units = 1

    ClientPortfolio = UnicodeAttribute(attr_name=CLIENT_PORTFOLIO_KEY, hash_key=True)
    """str: Client Portfolio (alternate key "client-portfolio") """

    AppRegex = UnicodeAttribute(attr_name=APP_KEY, range_key=True)
    """str: App Regex (alternate key "app-regex") """

    Name: UnicodeAttribute = UnicodeAttribute(null=True)
    """str: Name of the app (alternate key "name") """

    Environment: UnicodeAttribute = UnicodeAttribute(null=True)
    """str: Environment of the app (alternate key "environment") """

    Account: UnicodeAttribute = UnicodeAttribute(null=True)
    """str: Zone name of the app (alternate key "account") (same as Zone) """

    Zone: UnicodeAttribute = UnicodeAttribute(null=False)
    """str: Zone name of the app (alternate key "zone") (same as Account)

        We call this "zone" now.  a "zone" contains "apps" that are deployed together
        in an Acccount. A zone can have multiple region definitions.

    """

    ImgeAliases: MapAttribute = MapAttribute(null=True)
    """str: Image Aliases of the app to reduce bake time (alternate key "image-aliases") """

    Repository = UnicodeAttribute(null=True)
    """str: Git repository of the app (alternate key "repository") """

    Region = UnicodeAttribute(null=False)
    """str: Region alise (slug) of the app (alternate key "region") """

    Tags: MapAttribute = MapAttribute(null=True)
    """dict: Tags of the app (alternate key "tags") """

    EnforceValidation: UnicodeAttribute = UnicodeAttribute(null=True)
    """str: Enforce validation of the app (alternate key "enforce-validation") """

    Metadata: MapAttribute = MapAttribute(null=True)
    """dict: Metadata of the app (alternate key "metadata") """

    UserInstantiated: UnicodeAttribute = UnicodeAttribute(null=True)

    def __init__(self, *args, **kwargs):
        # Convert lowercase keys to camelCase keys
        kwargs = {self._convert_key(k): v for k, v in kwargs.items()}
        super().__init__(*args, **kwargs)

    @staticmethod
    def _convert_key(key):
        # Convert lowercase keys to camelCase keys
        words = re.split("[-_]", key)
        camel_case_key = "".join(word.capitalize() for word in words)
        return camel_case_key
