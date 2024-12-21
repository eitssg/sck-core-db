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
    """ Convert Keys to CamelCase """

    def __init__(self, *args, **kwargs):
        # Convert lowercase keys to camelCase keys
        kwargs = {_convert_key(k): v for k, v in kwargs.items()}
        super().__init__(*args, **kwargs)


class SecurityAliasFacts(MapAttribute):
    """Security Aliases

    { "alias_name": {"Type": "", "Value": "", "Description": ""}}

    Attributes:
        Type (str): The type of alias
        Value (str): The value of the alias
        Description (str): A description of the alias

    Security Aliases are created by Security Administrators.  You must have the role "CoreSecurityAdmin" to
    be able to modify the SecurityAliasFacts.

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
    """KMS Keys details

    A KMS Key is created for each **Zone**.  The KMS Key is used to encrypt/decrypt resources
    and data at rest.

    Attributes:
        AwsAccountId (str): The AWS Account ID where KMS Keys are managed/centralized
        KmsKeyArn (str): The KMS Key ARN for this Zone
        KmsKey (str): The KMS Key ID for this Zone
        DelegateAwsAccountIds (list): List of AWS Account IDs that can use the KMS Key

    KmsFacts are created by Security Administrators.  You must have the role "CoreSecurityAdmin" to
    be able to modify the KmsFacts.

    """

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
    """Account Details FACTS describing the AWS Account

    Attributes:
        Client (str): The client name (AWS Organzation slug. e.g. "acme")
        OrganizationalUnit (str): The Organizational Unit
        AwsAccountId (str): The AWS Account ID
        AccountName (str): The name of the account
        Environment (str): The environment
        Kms (KmsFacts): KMS Key details
        ResourceNamespace (str): The namespace for the resources
        VpcAliases (dict): VPC Aliases. Aliases are created for VPCs by the Networks pipelines
        SubnetAliases (dict): Subnet Aliases. Aliases are created for Subnets by the Networks pipelines
        Tags (dict): Tags to merge into the facts for this deployment

    AccountFacts are created by Network Administrators.  You must have the role "CoreNetworkAdmin" to
    be able to modify the AccountFacts.

    """

    Client = UnicodeAttribute(null=True)
    OrganizationalUnit = UnicodeAttribute(null=True)
    AwsAccountId = UnicodeAttribute(null=False)
    AccountName = UnicodeAttribute(null=True)
    Environment = UnicodeAttribute(null=True)
    Kms = KmsFacts(null=True)
    ResourceNamespace = UnicodeAttribute(null=True)
    VpcAliases: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    SubnetAliases: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    Tags: MapAttribute = MapAttribute(null=True)

    UserInstantiated = UnicodeAttribute(null=True)

    def __init__(self, *args, **kwargs):
        # Convert lowercase keys to camelCase keys
        kwargs = {_convert_key(k): v for k, v in kwargs.items()}
        super().__init__(*args, **kwargs)


class ProxyFacts(MapAttribute):
    """Proxy Details FACTS describing the Proxy information within the Zone

    Attributes:
        Host (str): The proxy host
        Port (str): The proxy port
        Url (str): The proxy URL
        NoProxy (str): The no proxy list

    Ports are created by Network Administrators.  You must have the role "CoreNetworkAdmin" to
    modify the ProxyFacts.

    """

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
    """Region FACTS descriging the detailed information for each supported region in the Zone

    Region FACTS are provided for each region Alias available in the zone.  THe region alias
    is a slug name for the region.

        Examples Include:

        * us-west-1 -> usw
        * us-east-1 -> use
        * ap-southeast-1 -> sin
        * ap-southeast-2 -> syd

    When registering RegionFacts, you may do so under any "slug" name you wish as they are user
    defined and scopeed to the **Zone.**

    Attributes:
        AwsRegion (str): The AWS Region
        AzCount (int): The number of Availability Zones in the region as defined by the Network Engineer
        ImageAliases (dict): Image Aliases. Aliases are created for AMIs by the Images pipelines
        MinSuccessfulInstancesPercent (int): The minimum percentage of successful instances required for a deployment in the Zone
        SecurityAliases (dict): Security Aliases publised by the security team define names for CIDR values. Aliases are created for Security Groups by the Security pipelines
        SecurityGroupAliases (dict): Security Group Aliases. Aliases are created for Security Groups by the Security pipelines
        Proxy (list[ProxyFacts]): Proxy details list of proxy endpoints. (New field - in incubation)
        ProxyHost (str): The proxy host. e.g. "proxy.acme.com"
        ProxyPort (int): The proxy port. e.g. 8080
        ProxyUrl (str): The proxy URL. e.g. "http://proxy.acme.com:8080"
        NoProxy (str): The no proxy list. e.g. "*.acme.com,10/8,192.168/16,169.254.169.253,169.254.169.254"
        NameServers (list): List of nameservers for the region
        Tags (dict): Tags to merge into the facts for this deployment taht can be added to resources

    Regions are created by Network Administrators.  You must have the role "CoreNetworkAdmin" to
    be able to modify the RegionFacts.

    """

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
    ProxyPort = NumberAttribute(null=True)
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
    """
    Zone FACTS describe the AwsAccount and the Region details for the Deployment Zone

    The zone is has a logical name defined by the zone creater and is used by App (deployments)
    to define the name of the **Zone** to deploy into.

    Zones are created by Network Administrators.  You must have the role "CoreNetworkAdmin" to
    be able to modify the ZoneFacts.

    Attributes:

        ClientPortfolio (str): The client portfolio name
        Zone (str): The zone name. Any name to define the one.
        AccountFacts (AccountFacts): AWS Account details for this Zone
        RegionFacts (dict[str, RegionFacts]): Region details indexed by region alias (slug)

    Znes are created by Cloud Network Administrators.  You must have the role "CoreNetworkAdmin" to
    be able to modify the ZoneFacts.

    """

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
