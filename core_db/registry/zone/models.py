"""Classes defining the ZoneFacts record model for the core-automation-zones table"""

from pynamodb.attributes import (
    UnicodeAttribute,
    MapAttribute,
    ListAttribute,
    NumberAttribute,
    BooleanAttribute,
)

import core_logging as log

from ...constants import CLIENT_KEY, ZONE_KEY, ZONE_FACTS
from ...config import get_table_name
from ..models import RegistryModel, ExtendedMapAttribute


class SecurityAliasFacts(ExtendedMapAttribute):
    """
    Security Aliases for a Zone.

    This model represents a security alias, which is a named reference to a security-related value
    (such as a CIDR block or other identifier) used within a Zone. Security aliases are managed by
    Security Administrators and require the "CoreSecurityAdmin" role for modification.

    Attributes
    ----------
    Type : str
        The type of alias (e.g., "CIDR", "SG", etc.).
    Value : str
        The value associated with the alias.
    Description : str, optional
        A description of the alias.
    """

    Type = UnicodeAttribute(null=False)
    Value = UnicodeAttribute(null=False)
    Description = UnicodeAttribute(null=True)
    UserInstantiated = UnicodeAttribute(null=True)  # Internal PynamoDB field


class KmsFacts(ExtendedMapAttribute):
    """
    KMS Key details for a Zone.

    This model contains information about the AWS KMS Key used for encryption within a Zone.
    KMS keys are managed by Security Administrators and require the "CoreSecurityAdmin" role
    for modification.

    Attributes
    ----------
    AwsAccountId : str
        AWS Account ID where KMS Keys are managed/centralized.
    KmsKeyArn : str, optional
        The ARN of the KMS Key for this Zone.
    KmsKey : str, optional
        The KMS Key ID for this Zone.
    DelegateAwsAccountIds : list[str]
        List of AWS Account IDs that can use the KMS Key.
    AllowSNS : bool, optional
        Whether SNS is allowed to use the KMS Key.
    """

    AwsAccountId = UnicodeAttribute(null=False)
    KmsKeyArn = UnicodeAttribute(null=True)
    KmsKey = UnicodeAttribute(null=True)
    DelegateAwsAccountIds = ListAttribute(of=UnicodeAttribute, null=False)
    AllowSNS = BooleanAttribute(null=True)
    UserInstantiated = UnicodeAttribute(null=True)  # Internal PynamoDB field


class AccountFacts(ExtendedMapAttribute):
    """
    AWS Account details for a Zone.

    This model describes the AWS account associated with a Zone, including organizational
    information, environment, KMS details, network aliases, and tags. Managed by Network
    Administrators with the "CoreNetworkAdmin" role.

    Attributes
    ----------
    Client : str, optional
        The client name (AWS Organization slug, e.g., "acme").
    OrganizationalUnit : str, optional
        The Organizational Unit name.
    AwsAccountId : str
        The AWS Account ID.
    AccountName : str, optional
        The name of the account.
    Environment : str, optional
        The environment (e.g., "prod", "dev").
    Kms : KmsFacts, optional
        KMS Key details.
    ResourceNamespace : str, optional
        Namespace for resources.
    NetworkName : str, optional
        Name of the network.
    VpcAliases : dict[str, str], optional
        VPC aliases created by network pipelines.
    SubnetAliases : dict[str, str], optional
        Subnet aliases created by network pipelines.
    Tags : dict, optional
        Tags to merge into facts for this deployment.
    """

    Client = UnicodeAttribute(null=True)
    OrganizationalUnit = UnicodeAttribute(null=True)
    AwsAccountId = UnicodeAttribute(null=False)
    AccountName = UnicodeAttribute(null=True)
    Environment = UnicodeAttribute(null=True)
    Kms = KmsFacts(null=True)
    ResourceNamespace = UnicodeAttribute(null=True)
    NetworkName = UnicodeAttribute(null=True)
    VpcAliases = MapAttribute(of=UnicodeAttribute, null=True)
    SubnetAliases = MapAttribute(of=UnicodeAttribute, null=True)
    Tags = MapAttribute(null=True)
    UserInstantiated = UnicodeAttribute(null=True)  # Internal PynamoDB field


class ProxyFacts(ExtendedMapAttribute):
    """
    Proxy configuration details for a Zone.

    This model describes proxy settings used within a Zone. Managed by Network
    Administrators with the "CoreNetworkAdmin" role.

    Attributes
    ----------
    Host : str, optional
        Proxy host (e.g., "proxy.acme.com").
    Port : str, optional
        Proxy port (e.g., "8080").
    Url : str, optional
        Proxy URL (e.g., "http://proxy.acme.com:8080").
    NoProxy : str, optional
        No-proxy list (e.g., "*.acme.com,10/8,192.168/16").
    """

    Host = UnicodeAttribute(null=True)
    Port = UnicodeAttribute(null=True)
    Url = UnicodeAttribute(null=True)
    NoProxy = UnicodeAttribute(null=True)
    UserInstantiated = UnicodeAttribute(null=True)  # Internal PynamoDB field


class RegionFacts(ExtendedMapAttribute):
    """
    Region details for a Zone.

    This model provides detailed information about each supported AWS region within a Zone.
    Managed by Network Administrators with the "CoreNetworkAdmin" role.

    Attributes
    ----------
    AwsRegion : str
        The AWS region code (e.g., "us-west-2").
    AzCount : int, optional
        Number of Availability Zones in the region.
    ImageAliases : dict[str, str], optional
        Aliases for AMIs created by image pipelines.
    MinSuccessfulInstancesPercent : int, optional
        Minimum percent of successful instances for deployment.
    SecurityAliases : dict[str, list[SecurityAliasFacts]], optional
        Security aliases published by the security team.
    SecurityGroupAliases : dict[str, str], optional
        Security group aliases.
    Proxy : list[ProxyFacts], optional
        List of proxy endpoint details.
    ProxyHost : str, optional
        Proxy host.
    ProxyPort : int, optional
        Proxy port.
    ProxyUrl : str, optional
        Proxy URL.
    NoProxy : str, optional
        No-proxy list.
    NameServers : list[str], optional
        List of nameservers for the region.
    Tags : dict, optional
        Tags for deployment resources.
    """

    AwsRegion = UnicodeAttribute(null=False)
    AzCount = NumberAttribute(null=True)
    ImageAliases = MapAttribute(of=UnicodeAttribute, null=True)
    MinSuccessfulInstancesPercent = NumberAttribute(null=True)
    SecurityAliases = MapAttribute(null=True, of=ListAttribute(of=SecurityAliasFacts))
    SecurityGroupAliases = MapAttribute(of=UnicodeAttribute, null=True)
    Proxy = ListAttribute(of=ProxyFacts, null=True)
    ProxyHost = UnicodeAttribute(null=True)
    ProxyPort = NumberAttribute(null=True)
    ProxyUrl = UnicodeAttribute(null=True)
    NoProxy = UnicodeAttribute(null=True)
    NameServers = ListAttribute(of=UnicodeAttribute, null=True)
    Tags = MapAttribute(null=True)
    UserInstantiated = UnicodeAttribute(null=True)  # Internal PynamoDB field


class ZoneFacts(RegistryModel):
    """
    Protocol defining the interface for ZoneFacts models.

    This protocol defines the structure for zone facts models that can be created
    dynamically for different clients using the ZoneFactsFactory. It represents
    a complete zone configuration including AWS account details, regional settings,
    network configurations, security aliases, proxy settings, and deployment metadata
    for infrastructure automation.

    A Zone is a deployment boundary that contains applications deployed together
    in a specific AWS Account, with multiple region definitions and shared
    infrastructure configuration.

    Attributes
    ----------
    Client : UnicodeAttribute
        Client identifier (alternate key "client")
        AWS Organization slug representing the client organization
    Zone : UnicodeAttribute
        Zone identifier (alternate key "zone")
        Unique zone name within the client namespace
    AccountFacts : AccountFacts
        AWS Account details for the zone including:
        - Account ID and organizational unit information
        - KMS key configuration for encryption
        - Network aliases (VPC and subnet mappings)
        - Resource namespace and naming conventions
        - Environment classification and tags
    RegionFacts : MapAttribute
        Region details mapped by AWS region name containing:
        - Regional proxy and network configurations
        - Security aliases and group mappings
        - Image aliases for AMI references
        - Availability zone counts and deployment settings
        - Regional tags and metadata
    Tags : MapAttribute
        Global tags for deployment resources (alternate key "tags")
        Key-value pairs applied to all resources in the zone
    UserInstantiated : UnicodeAttribute
        Internal PynamoDB field indicating user instantiation

    Notes
    -----
    ZoneFacts inherits all standard PynamoDB methods from ModelProtocol including:

    Instance Methods:
        - save(condition=None): Save zone configuration to DynamoDB
        - delete(condition=None): Delete zone configuration from DynamoDB
        - update(actions, condition=None): Update zone with specific actions
        - refresh(consistent_read=None): Refresh zone data from DynamoDB
        - serialize(values=None): Serialize zone to dictionary format
        - deserialize(values): Deserialize data into zone instance
        - to_simple_dict(): Convert zone to simple dictionary representation
        - get_attributes(): Get all zone model attributes
        - convert_keys(**kwargs): Convert attribute keys to proper case

    Class Methods:
        - get(client, zone): Get specific zone by client and zone identifiers
        - query(client, **kwargs): Query all zones for a specific client
        - scan(**kwargs): Scan all zones across the table
        - count(client=None, **kwargs): Count zones for client or globally
        - exists(): Check if the zone facts table exists
        - create_table(wait=False): Create the DynamoDB table for zones
        - delete_table(): Delete the zone facts table
        - describe_table(): Get detailed table description from DynamoDB
        - batch_get(keys, **kwargs): Batch retrieve multiple zones
        - batch_write(auto_commit=True): Create batch write context manager
        - get_meta_data(): Get zone model metadata and schema information
        - from_raw_data(data): Create zone instance from raw DynamoDB data

    Custom Methods:
        - get_attribute_class(key): Get the class type of a specific attribute

    Access Control
    --------------
    Zone configuration requires specific administrative roles:

    - **NetworkAdmin Role**: Required for AccountFacts, RegionFacts network settings
    - **SecurityAdmin Role**: Required for KMS configuration and SecurityAliases
    - **General Access**: Tags and basic zone metadata can be modified by zone owners

    Regional Configuration
    ----------------------
    Each zone supports multiple AWS regions with independent configuration:

    - **Network Settings**: Region-specific proxy, nameservers, and network aliases
    - **Security Settings**: Regional security groups and security aliases
    - **Image Management**: Region-specific AMI aliases for deployment pipelines
    - **Deployment Settings**: Availability zone counts and success thresholds

    Examples
    --------
    Creating a new zone with the factory pattern:

    >>> model_class = ZoneFactsFactory.get_model("acme")
    >>> zone = model_class(
    ...     "acme", "production-east",
    ...     AccountFacts={
    ...         "AwsAccountId": "123456789012",
    ...         "Environment": "prod",
    ...         "OrganizationalUnit": "production",
    ...         "Kms": {
    ...             "AwsAccountId": "123456789012",
    ...             "KmsKeyArn": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
    ...             "DelegateAwsAccountIds": ["123456789012", "123456789013"]
    ...         }
    ...     },
    ...     RegionFacts={
    ...         "us-east-1": {
    ...             "AwsRegion": "us-east-1",
    ...             "AzCount": 3,
    ...             "ProxyHost": "proxy.acme.com",
    ...             "ProxyPort": 8080,
    ...             "SecurityAliases": {
    ...                 "corporate-cidrs": [
    ...                     {"Type": "CIDR", "Value": "10.0.0.0/8", "Description": "Corporate network"}
    ...                 ]
    ...             }
    ...         }
    ...     },
    ...     Tags={"Environment": "production", "Owner": "platform-team"}
    ... )
    >>> zone.save()

    Querying zones for a client:

    >>> zones = list(model_class.query("acme"))
    >>> for zone in zones:
    ...     print(f"Zone: {zone.Client}:{zone.Zone}")
    ...     print(f"  Account: {zone.AccountFacts.AwsAccountId}")
    ...     print(f"  Regions: {list(zone.RegionFacts.keys())}")

    Updating regional configuration:

    >>> zone = model_class.get("acme", "production-east")
    >>> zone.RegionFacts["us-west-2"] = {
    ...     "AwsRegion": "us-west-2",
    ...     "AzCount": 3,
    ...     "ProxyHost": "proxy-west.acme.com",
    ...     "ProxyPort": 8080
    ... }
    >>> zone.save()

    Managing security aliases (requires SecurityAdmin role):

    >>> zone.RegionFacts["us-east-1"]["SecurityAliases"]["dmz-subnets"] = [
    ...     {"Type": "SUBNET", "Value": "subnet-12345", "Description": "DMZ subnet A"},
    ...     {"Type": "SUBNET", "Value": "subnet-67890", "Description": "DMZ subnet B"}
    ... ]
    >>> zone.save()

    Batch operations for multiple zones:

    >>> with model_class.batch_write() as batch:
    ...     for zone_name in ["dev-east", "test-east", "staging-east"]:
    ...         zone = model_class("acme", zone_name, AccountFacts=base_account, Tags=base_tags)
    ...         batch.save(zone)

    Data Structure Examples
    -----------------------
    Complete zone configuration structure:

    >>> {
    ...     "Client": "acme",
    ...     "Zone": "production-east",
    ...     "AccountFacts": {
    ...         "AwsAccountId": "123456789012",
    ...         "AccountName": "ACME Production",
    ...         "Environment": "prod",
    ...         "OrganizationalUnit": "production",
    ...         "ResourceNamespace": "acme-prod",
    ...         "NetworkName": "production-network",
    ...         "Kms": {
    ...             "AwsAccountId": "123456789012",
    ...             "KmsKeyArn": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
    ...             "KmsKey": "12345678-1234-1234-1234-123456789012",
    ...             "DelegateAwsAccountIds": ["123456789012", "123456789013"],
    ...             "AllowSNS": True
    ...         },
    ...         "VpcAliases": {"main": "vpc-12345678", "dmz": "vpc-87654321"},
    ...         "SubnetAliases": {"web": "subnet-12345", "app": "subnet-67890"},
    ...         "Tags": {"CostCenter": "engineering", "Project": "platform"}
    ...     },
    ...     "RegionFacts": {
    ...         "us-east-1": {
    ...             "AwsRegion": "us-east-1",
    ...             "AzCount": 3,
    ...             "MinSuccessfulInstancesPercent": 75,
    ...             "ImageAliases": {"web-server": "ami-12345678", "app-server": "ami-87654321"},
    ...             "SecurityAliases": {
    ...                 "corporate-cidrs": [
    ...                     {"Type": "CIDR", "Value": "10.0.0.0/8", "Description": "Corporate network"},
    ...                     {"Type": "CIDR", "Value": "192.168.0.0/16", "Description": "VPN network"}
    ...                 ],
    ...                 "dmz-subnets": [
    ...                     {"Type": "SUBNET", "Value": "subnet-12345", "Description": "DMZ subnet A"}
    ...                 ]
    ...             },
    ...             "SecurityGroupAliases": {"web-sg": "sg-12345678", "app-sg": "sg-87654321"},
    ...             "Proxy": [
    ...                 {"Host": "proxy.acme.com", "Port": "8080", "Url": "http://proxy.acme.com:8080"}
    ...             ],
    ...             "ProxyHost": "proxy.acme.com",
    ...             "ProxyPort": 8080,
    ...             "ProxyUrl": "http://proxy.acme.com:8080",
    ...             "NoProxy": "*.acme.com,10.0.0.0/8,192.168.0.0/16",
    ...             "NameServers": ["8.8.8.8", "8.8.4.4"],
    ...             "Tags": {"Region": "us-east-1", "Environment": "production"}
    ...         }
    ...     },
    ...     "Tags": {"Environment": "production", "Owner": "platform-team", "Backup": "daily"}
    ... }
    """

    class Meta(RegistryModel.Meta):
        pass

    # PynamoDB attribute definitions
    Client = UnicodeAttribute(attr_name=CLIENT_KEY, hash_key=True)
    Zone = UnicodeAttribute(attr_name=ZONE_KEY, range_key=True)
    AccountFacts = AccountFacts(null=False)
    RegionFacts = MapAttribute(of=RegionFacts, null=False)
    Tags = MapAttribute(of=UnicodeAttribute, null=True)
    UserInstantiated = UnicodeAttribute(null=True)


ZoneFactsType = type[ZoneFacts]


class ZoneFactsFactory:
    """Factory to create client-specific ZoneFacts models with dynamic table names."""

    _model_cache = {}

    @classmethod
    def get_model(cls, client: str, auto_create_table: bool = True) -> ZoneFactsType:
        """
        Get a ZoneFacts model class for a specific client.

        Parameters
        ----------
        client : str
            The client name for table name generation.
        auto_create_table : bool, optional
            Whether to auto-create the table if it doesn't exist (default: True)

        Returns
        -------
        type[ZoneFacts]
            A ZoneFacts model class configured for the specified client.
        """
        if client not in cls._model_cache:
            model_class: ZoneFactsType = cls._create_client_model(client)
            cls._model_cache[client] = model_class

            # Auto-create table if requested
            if auto_create_table:
                cls._ensure_table_exists(model_class)

        return cls._model_cache[client]

    @classmethod
    def _ensure_table_exists(cls, model_class: ZoneFactsType) -> None:
        """
        Ensure the table exists, create it if it doesn't.

        Parameters
        ----------
        model_class : type
            The model class to check/create table for
        client : str
            The client name for logging
        """
        try:
            if not model_class.exists():
                log.info("Creating zone table : %s", model_class.Meta.table_name)
                model_class.create_table(wait=True)
                log.info("Successfully created zone table: %s", model_class.Meta.table_name)
        except Exception as e:
            log.error("Failed to create zone table %s: %s", model_class.Meta.table_name, str(e))
            # Don't raise - let the operation proceed and fail naturally

    @classmethod
    def _create_client_model(cls, client: str) -> ZoneFactsType:
        """Create a new ZoneFacts model class for a specific client."""

        class ZoneFactsModel(ZoneFacts):
            class Meta(ZoneFacts.Meta):
                table_name = get_table_name(ZONE_FACTS, client)

        return ZoneFactsModel
