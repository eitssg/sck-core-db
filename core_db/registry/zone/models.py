""" Classes defining the ZoneFacts record model for the core-automation-zones table """

from pynamodb.attributes import (
    UnicodeAttribute,
    MapAttribute,
    ListAttribute,
    NumberAttribute,
    BooleanAttribute
)

import core_framework as util

from ...constants import CLIENT_KEY, ZONE_KEY, ZONE_FACTS

from ...config import get_table_name

from ..models import RegistryModel, ExtendedMapAttribute


class SecurityAliasFacts(ExtendedMapAttribute):
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
    """str: The type of alias"""
    Value = UnicodeAttribute(null=False)
    """str: The value of the alias"""
    Description = UnicodeAttribute(null=True)
    """str: A description of the alias"""

    UserInstantiated = UnicodeAttribute(null=True)


class KmsFacts(ExtendedMapAttribute):
    """KMS Keys details

    A KMS Key is created for each **Zone**.  The KMS Key is used to encrypt/decrypt resources
    and data at rest.

    KmsFacts are created by Security Administrators.  You must have the role "CoreSecurityAdmin" to
    be able to modify the KmsFacts.

    """

    AwsAccountId = UnicodeAttribute(null=False)
    """str: The AWS Account ID where KMS Keys are managed/centralized"""
    KmsKeyArn = UnicodeAttribute(null=True)
    """str: The KMS Key ARN for this Zone"""
    KmsKey = UnicodeAttribute(null=True)
    """str: The KMS Key ID for this Zone"""
    DelegateAwsAccountIds = ListAttribute(of=UnicodeAttribute, null=False)
    """list[str]: List of AWS Account IDs that can use the KMS Key"""
    AllowSNS = BooleanAttribute(null=True)
    """bool: Allow SNS to use the KMS Key """

    UserInstantiated = UnicodeAttribute(null=True)


class AccountFacts(ExtendedMapAttribute):
    """Account Details FACTS describing the AWS Account

    AccountFacts are created by Network Administrators.  You must have the role "CoreNetworkAdmin" to
    be able to modify the AccountFacts.

    """

    Client = UnicodeAttribute(null=True)
    """str: The client name (AWS Organzation slug. e.g. "acme")"""
    OrganizationalUnit = UnicodeAttribute(null=True)
    """str: The Organizational Unit"""
    AwsAccountId = UnicodeAttribute(null=False)
    """str: The AWS Account ID"""
    AccountName = UnicodeAttribute(null=True)
    """str: The name of the account"""
    Environment = UnicodeAttribute(null=True)
    """str: The environment"""
    Kms = KmsFacts(null=True)
    """KmsFacts: KMS Key details"""
    ResourceNamespace = UnicodeAttribute(null=True)
    """str: The namespace for the resources"""
    NetworkName = UnicodeAttribute(null=True)
    """str: The name of the network.  What do your network Admins call this? """
    VpcAliases: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    """dict: VPC Aliases. Aliases are created for VPCs by the Networks pipelines"""
    SubnetAliases: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    """dict: Subnet Aliases. Aliases are created for Subnets by the Networks pipelines"""
    Tags: MapAttribute = MapAttribute(null=True)
    """dict: Tags to merge into the facts for this deployment"""

    UserInstantiated = UnicodeAttribute(null=True)


class ProxyFacts(ExtendedMapAttribute):
    """Proxy Details FACTS describing the Proxy information within the Zone

    Ports are created by Network Administrators.  You must have the role "CoreNetworkAdmin" to
    modify the ProxyFacts.

    """

    Host = UnicodeAttribute(null=True)
    """str: The proxy host. e.g. "proxy.acme.com" """
    Port = UnicodeAttribute(null=True)
    """str: The proxy port. e.g. 8080 """
    Url = UnicodeAttribute(null=True)
    """str: The proxy URL. e.g. "http://proxy.acme.com:8080" """
    NoProxy = UnicodeAttribute(null=True)
    """str: The no proxy list. e.g. "\\*.acme.com,10/8,192.168/16," """

    UserInstantiated = UnicodeAttribute(null=True)


class RegionFacts(ExtendedMapAttribute):
    """Region FACTS descriging the detailed information for each supported region in the Zone

    Region FACTS are provided for each region Alias available in the zone.  THe region alias
    is a slug name for the region.

        Examples Include:

        - us-west-1 -> usw
        - us-east-1 -> use
        - ap-southeast-1 -> sin
        - ap-southeast-2 -> syd

    When registering RegionFacts, you may do so under any "slug" name you wish as they are user
    defined and scopeed to the **Zone.**

    Regions are created by Network Administrators.  You must have the role "CoreNetworkAdmin" to
    be able to modify the RegionFacts.

    """

    AwsRegion = UnicodeAttribute(null=False)
    """str: The AWS Region"""
    AzCount = NumberAttribute(null=True)
    """int: The number of Availability Zones in the region as defined by the Network Engineer"""
    ImageAliases: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    """dict[str,str]: Image Aliases. Aliases are created for AMIs by the Images pipelines"""
    MinSuccessfulInstancesPercent = NumberAttribute(null=True)
    """int: The minimum percentage of successful instances required for a deployment in the Zone"""
    SecurityAliases: MapAttribute = MapAttribute(
        null=True, of=ListAttribute(of=SecurityAliasFacts)
    )
    """dict[str,SecurityAliasFacts]: Security Aliases publised by the security team define names for CIDR values. Aliases are created for Security Groups by the Security pipelines"""
    SecurityGroupAliases: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    """dict[str,str]: Security Group Aliases. Aliases are created for Security Groups by the Security pipelines"""
    Proxy = ListAttribute(of=ProxyFacts, null=True)
    """list[ProxyFacts]: Proxy details list of proxy endpoints. (New field - in incubation)"""
    ProxyHost = UnicodeAttribute(null=True)
    """str: The proxy host. e.g. "proxy.acme.com" """
    ProxyPort = NumberAttribute(null=True)
    """int: The proxy port. e.g. 8080 """
    ProxyUrl = UnicodeAttribute(null=True)
    """str: The proxy URL. e.g. "http://proxy.acme.com:8080" """
    NoProxy = UnicodeAttribute(null=True)
    """str: The no proxy list. e.g. "\\*.acme.com,10/8,192.168/16," """
    NameServers = ListAttribute(of=UnicodeAttribute, null=True)
    """list[str]: List of nameservers for the region"""
    Tags: MapAttribute = MapAttribute(null=True)
    """dict: Tags to merge into the facts for this deployment taht can be added to resources"""

    UserInstantiated = UnicodeAttribute(null=True)


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
        """str: The table name for the ZoneFacts"""
        region = util.get_region()
        """str: The region for the ZoneFacts"""
        host = util.get_dynamodb_host()
        """str: The host for the ZoneFacts"""
        read_capacity_units = 1
        """int: The read capacity units for the ZoneFacts"""
        write_capacity_units = 1
        """int: The write capacity units for the ZoneFacts"""

    Client = UnicodeAttribute(attr_name=CLIENT_KEY, hash_key=True)
    """str: The client portfolio name"""

    Zone = UnicodeAttribute(attr_name=ZONE_KEY, range_key=True)
    """str: The zone name. Any name to define the one."""

    AccountFacts = AccountFacts(null=False)
    """AccountFacts: AWS Account details for this Zone"""

    RegionFacts: MapAttribute = MapAttribute(of=RegionFacts, null=False)
    """dict[str, RegionFacts]: Region details indexed by region alias (slug)"""

    Tags: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)

    UserInstantiated = UnicodeAttribute(null=True)

    def get_attribute_class(self, key: str):
        attribute = self.get_attributes().get(key)
        if attribute:
            return attribute.__class__
        return None
