""" Classes defining the Apps record model for the core-automation-apps table """

import re

from pynamodb.models import Model
from pynamodb.attributes import MapAttribute, UnicodeAttribute

import core_framework as util

from ...constants import CLIENT_PORTFOLIO_KEY, APP_KEY

from ...config import get_table_name, APP_FACTS


class AppFacts(Model):

    class Meta:
        table_name = get_table_name(APP_FACTS)
        region = util.get_region()
        host = util.get_dynamodb_host()
        read_capacity_units = 1
        write_capacity_units = 1

    # Hash/Range keys
    ClientPortfolio = UnicodeAttribute(attr_name=CLIENT_PORTFOLIO_KEY, hash_key=True)
    AppRegex = UnicodeAttribute(attr_name=APP_KEY, range_key=True)

    # Do you wish to give it a friendly name?
    Name: UnicodeAttribute = UnicodeAttribute(null=True)

    # Are you prod, nonprod, dev, uat, preprod, staging.  You choose.
    Environment: UnicodeAttribute = UnicodeAttribute(null=True)

    # Which "zone" to go into (deprecated.  Use "Zone").
    Account: UnicodeAttribute = UnicodeAttribute(null=True)

    # We call this "zone" now.  a "zone" contains "apps" that are deployed together
    # in an Acccount. A zone can have multiple region definitions.
    Zone: UnicodeAttribute = UnicodeAttribute(null=False)

    # Attributes
    ImgeAliases: MapAttribute = MapAttribute(null=True)
    Repository = UnicodeAttribute(null=True)

    # You MUST specify a region.  This is used to select Facts from the Zone.
    Region = UnicodeAttribute(null=False)

    # Tags to merge into the facts for this deployment.
    Tags: MapAttribute = MapAttribute(null=True)

    # If True, then the deployment will enforce validation rules.
    EnforceValidation: UnicodeAttribute = UnicodeAttribute(null=True)

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
