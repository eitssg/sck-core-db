""" Classes defining the Apps record model for the core-automation-zones table """

import re

from pynamodb.attributes import (
    UnicodeAttribute,
    MapAttribute,
    ListAttribute,
    NumberAttribute,
)

import core_framework as util

from ...constants import CLIENT_PORTFOLIO_KEY, ZONE_KEY, ZONE_FACTS

from ...config import get_table_name

from ..models import RegistryModel


def _convert_key(key):
    # Convert lowercase keys to camelCase keys
    words = re.split("[-_]", key)
    camel_case_key = words[0] + "".join(word.capitalize() for word in words[1:])
    return camel_case_key


class ExtendedMapAttribute(MapAttribute):

    def __init__(self, *args, **kwargs):
        # Convert lowercase keys to camelCase keys
        kwargs = {_convert_key(k): v for k, v in kwargs.items()}
        super().__init__(*args, **kwargs)


class SecurityAliasFacts(MapAttribute):
    """ Security Aliases

    { "alias_name": {"Type": "", "Value": "", "Description": ""}}

    """
    Type = UnicodeAttribute(null=False)
    Value = UnicodeAttribute(null=False)
    Description = UnicodeAttribute(null=True)

    UserInstantiated = UnicodeAttribute(null=True)

    def __init__(self, *args, **kwargs):
        # Convert lowercase keys to camelCase keys
        kwargs = {_convert_key(k): v for k, v in kwargs.items()}
        super().__init__(*args, **kwargs)


class KmsFacts(MapAttribute):
    """ KMS Keys details """

    AwsAccountId = UnicodeAttribute(null=True)
    KmsKeyArn = UnicodeAttribute(null=True)
    KmsKey = UnicodeAttribute(null=True)
    DelegateAwsAccountIds = ListAttribute(of=UnicodeAttribute, null=False)

    UserInstantiated = UnicodeAttribute(null=True)

    def __init__(self, *args, **kwargs):
        # Convert lowercase keys to camelCase keys
        kwargs = {_convert_key(k): v for k, v in kwargs.items()}
        super().__init__(*args, **kwargs)


class AccountFacts(MapAttribute):
    """ Account Details FACTS describing the AWS Account """

    Client = UnicodeAttribute(null=True)
    AwsAccountId = UnicodeAttribute(null=False)
    OrganizationalUnit = UnicodeAttribute(null=True)
    Environment = UnicodeAttribute(null=True)
    Kms = KmsFacts(null=True)
    ResourceNamespace = UnicodeAttribute(null=True)
    VpcAliases: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    SubnetAliases: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    AccountName = UnicodeAttribute(null=True)
    Tags: MapAttribute = MapAttribute(null=True)

    UserInstantiated = UnicodeAttribute(null=True)

    def __init__(self, *args, **kwargs):
        # Convert lowercase keys to camelCase keys
        kwargs = {_convert_key(k): v for k, v in kwargs.items()}
        super().__init__(*args, **kwargs)


class ProxyFacts(MapAttribute):
    """ Proxy Details FACTS describing the Proxy information within the Zone """

    Host = UnicodeAttribute(null=True)
    Port = UnicodeAttribute(null=True)
    Url = UnicodeAttribute(null=True)
    NoProxy = UnicodeAttribute(null=True)

    UserInstantiated = UnicodeAttribute(null=True)

    def __init__(self, *args, **kwargs):
        # Convert lowercase keys to camelCase keys
        kwargs = {_convert_key(k): v for k, v in kwargs.items()}
        super().__init__(*args, **kwargs)


class RegionFacts(MapAttribute):
    """ Region FACTS descriging the detailed information for each supported region in the Zone """

    AwsRegion = UnicodeAttribute(null=False)
    AzCount = NumberAttribute(null=True)

    # Image aliases
    ImageAliases: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)

    # Min successful instances percent
    MinSuccessfulInstancesPercent = NumberAttribute(null=True)

    # Security aliases
    SecurityAliases: MapAttribute = MapAttribute(
        null=True, of=ListAttribute(of=SecurityAliasFacts)
    )
    SecurityGroupAliases: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)

    # I wish to use this new field to group the proxy facts.
    Proxy = ListAttribute(of=ProxyFacts, null=True)

    # I don't want to use this to group the proxy facts.
    ProxyHost = UnicodeAttribute(null=True)
    ProxyPort = UnicodeAttribute(null=True)
    ProxyUrl = UnicodeAttribute(null=True)
    NoProxy = UnicodeAttribute(null=True)

    # Nameservers
    NameServers = ListAttribute(of=UnicodeAttribute, null=True)

    # Tags
    Tags: MapAttribute = MapAttribute(null=True)

    UserInstantiated = UnicodeAttribute(null=True)

    def __init__(self, *args, **kwargs):
        # Convert lowercase keys to camelCase keys
        kwargs = {_convert_key(k): v for k, v in kwargs.items()}
        super().__init__(*args, **kwargs)


class ZoneFacts(RegistryModel):
    """ Zone FACTS describe the AwsAccount and the Region details for the Deployment Zone """
    class Meta:
        table_name = get_table_name(ZONE_FACTS)
        region = util.get_region()
        host = util.get_dynamodb_host()
        read_capacity_units = 1
        write_capacity_units = 1

    # Hash/Range keys
    ClientPortfolio = UnicodeAttribute(attr_name=CLIENT_PORTFOLIO_KEY, hash_key=True)

    # This is the "label" of the zone.
    Zone = UnicodeAttribute(attr_name=ZONE_KEY, range_key=True)

    # Attributes
    AccountFacts = AccountFacts(null=False)
    RegionFacts: MapAttribute = MapAttribute(of=RegionFacts, null=False)

    UserInstantiated = UnicodeAttribute(null=True)

    def get_attribute_class(self, key: str):
        attribute = self.get_attributes().get(key)
        if attribute:
            return attribute.__class__
        return None

    def __init__(self, *args, **kwargs):
        # Convert lowercase keys to camelCase keys
        kwargs = {_convert_key(k): v for k, v in kwargs.items()}
        super().__init__(*args, **kwargs)
