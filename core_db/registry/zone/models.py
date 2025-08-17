"""Classes defining the ZoneFactsModel record model for the core-automation-zones table"""

from typing import Type, Dict, Any, Optional, List
from pydantic import ConfigDict, Field

from pydantic.main import BaseModel
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    BooleanAttribute,
    ListAttribute,
    MapAttribute,
    MapAttribute,
    ListAttribute,
)

from ...constants import ZONE_KEY
from ...models import TableFactory, DatabaseTable, EnhancedMapAttribute, DictAttribute
from ..models import RegistryFact


class SecurityAliasFacts(EnhancedMapAttribute):
    """Security Aliases for a Zone.

    This model represents a security alias, which is a named reference to a security-related value
    (such as a CIDR block or other identifier) used within a Zone. Security aliases are managed by
    Security Administrators and require the "CoreSecurityAdmin" role for modification.

    Attributes:
        type (str): The type of alias (e.g., "CIDR", "SG", etc.)
        value (str): The value associated with the alias
        description (str, optional): A description of the alias

    Examples:
        >>> # Both formats work identically (thanks to ExtendedMapAttribute)
        >>> alias1 = SecurityAliasFacts(
        ...     type="CIDR",
        ...     value="10.0.0.0/8",
        ...     description="Corporate network"
        ... )

        >>> alias2 = SecurityAliasFacts(
        ...     Type="CIDR",
        ...     Value="10.0.0.0/8",
        ...     Description="Corporate network"
        ... )
    """

    type = UnicodeAttribute(null=False, attr_name="Type")
    value = UnicodeAttribute(null=False, attr_name="Value")
    description = UnicodeAttribute(null=True, attr_name="Description")


class KmsFacts(EnhancedMapAttribute):
    """KMS Key details for a Zone.

    This model contains information about the AWS KMS Key used for encryption within a Zone.
    KMS keys are managed by Security Administrators and require the "CoreSecurityAdmin" role
    for modification.

    Attributes:
        aws_account_id (str): AWS Account ID where KMS Keys are managed/centralized
        kms_key_arn (str, optional): The ARN of the KMS Key for this Zone
        kms_key (str, optional): The KMS Key ID for this Zone
        delegate_aws_account_ids (list[str]): List of AWS Account IDs that can use the KMS Key
        allow_sns (bool, optional): Whether SNS is allowed to use the KMS Key

    Examples:
        >>> # Both formats work identically
        >>> kms1 = KmsFacts(
        ...     aws_account_id="123456789012",
        ...     kms_key_arn="arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
        ...     delegate_aws_account_ids=["123456789012", "123456789013"],
        ...     allow_sns=True
        ... )

        >>> kms2 = KmsFacts(
        ...     AwsAccountId="123456789012",
        ...     KmsKeyArn="arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
        ...     DelegateAwsAccountIds=["123456789012", "123456789013"],
        ...     AllowSNS=True
        ... )
    """

    aws_account_id = UnicodeAttribute(null=False, attr_name="AwsAccountId")
    kms_key_arn = UnicodeAttribute(null=True, attr_name="KmsKeyArn")
    kms_key = UnicodeAttribute(null=True, attr_name="KmsKey")
    delegate_aws_account_ids = ListAttribute(of=UnicodeAttribute, null=False, attr_name="DelegateAwsAccountIds")
    allow_sns = BooleanAttribute(null=True, attr_name="AllowSNS")


class AccountFacts(EnhancedMapAttribute):
    """AWS Account details for a Zone.

    This model describes the AWS account associated with a Zone, including organizational
    information, environment, KMS details, network aliases, and tags. Managed by Network
    Administrators with the "CoreNetworkAdmin" role.

    Attributes:
        organizational_unit (str, optional): The Organizational Unit name
        aws_account_id (str): The AWS Account ID
        account_name (str, optional): The name of the account
        environment (str, optional): The environment (e.g., "prod", "dev")
        kms (KmsFacts, optional): KMS Key details
        resource_namespace (str, optional): Namespace for resources
        network_name (str, optional): Name of the network
        vpc_aliases (list[str], optional): VPC aliases created by network pipelines
        subnet_aliases (list[str], optional): Subnet aliases created by network pipelines
        tags (dict[str, Any], optional): Tags to merge into facts for this deployment

    Examples:
        >>> # Both formats work identically
        >>> account1 = AccountFacts(
        ...     aws_account_id="123456789012",
        ...     account_name="ACME Production",
        ...     environment="prod",
        ...     vpc_aliases=["vpc-main", "vpc-backup"],
        ...     subnet_aliases=["subnet-public", "subnet-private"],
        ...     tags={"Environment": "production", "Owner": "network-team"},
        ...     kms={"aws_account_id": "123456789012", "delegate_aws_account_ids": ["123456789012"]}
        ... )

        >>> account2 = AccountFacts(
        ...     AwsAccountId="123456789012",
        ...     AccountName="ACME Production",
        ...     Environment="prod",
        ...     VpcAliases=["vpc-main", "vpc-backup"],
        ...     SubnetAliases=["subnet-public", "subnet-private"],
        ...     Tags={"Environment": "production", "Owner": "network-team"},
        ...     Kms={"AwsAccountId": "123456789012", "DelegateAwsAccountIds": ["123456789012"]}
        ... )
    """

    organizational_unit = UnicodeAttribute(null=True, attr_name="OrganizationalUnit")
    aws_account_id = UnicodeAttribute(null=False, attr_name="AwsAccountId")
    account_name = UnicodeAttribute(null=True, attr_name="AccountName")
    environment = UnicodeAttribute(null=True, attr_name="Environment")
    kms = KmsFacts(null=True, attr_name="Kms")
    resource_namespace = UnicodeAttribute(null=True, attr_name="ResourceNamespace")
    network_name = UnicodeAttribute(null=True, attr_name="NetworkName")
    vpc_aliases = ListAttribute(of=UnicodeAttribute, null=True, attr_name="VpcAliases")
    subnet_aliases = ListAttribute(of=UnicodeAttribute, null=True, attr_name="SubnetAliases")
    tags = MapAttribute(null=True, attr_name="Tags")


class ProxyFacts(EnhancedMapAttribute):
    """Proxy configuration details for a Zone.

    This model describes proxy settings used within a Zone. Managed by Network
    Administrators with the "CoreNetworkAdmin" role.

    Attributes:
        host (str, optional): Proxy host (e.g., "proxy.acme.com")
        port (str, optional): Proxy port (e.g., "8080")
        url (str, optional): Proxy URL (e.g., "http://proxy.acme.com:8080")
        no_proxy (str, optional): No-proxy list (e.g., "*.acme.com,10/8,192.168/16")

    Examples:
        >>> # Both formats work identically
        >>> proxy1 = ProxyFacts(
        ...     host="proxy.acme.com",
        ...     port="8080",
        ...     url="http://proxy.acme.com:8080",
        ...     no_proxy="*.acme.com,10.0.0.0/8"
        ... )

        >>> proxy2 = ProxyFacts(
        ...     Host="proxy.acme.com",
        ...     Port="8080",
        ...     Url="http://proxy.acme.com:8080",
        ...     NoProxy="*.acme.com,10.0.0.0/8"
        ... )
    """

    host = UnicodeAttribute(null=True, attr_name="Host")
    port = UnicodeAttribute(null=True, attr_name="Port")
    url = UnicodeAttribute(null=True, attr_name="Url")
    no_proxy = UnicodeAttribute(null=True, attr_name="NoProxy")


class RegionFacts(EnhancedMapAttribute):
    """Region details for a Zone.

    This model provides detailed information about each supported AWS region within a Zone.
    Managed by Network Administrators with the "CoreNetworkAdmin" role.

    Attributes:
        aws_region (str): The AWS region code (e.g., "us-west-2")
        az_count (int, optional): Number of Availability Zones in the region
        image_aliases (dict[str, str], optional): Aliases for AMIs created by image pipelines (stored as MapAttribute)
        min_successful_instances_percent (int, optional): Minimum percent of successful instances for deployment
        security_aliases (dict[str, list[SecurityAliasFacts]], optional): Security aliases published by the security team (stored as MapAttribute)
        security_group_aliases (dict[str, str], optional): Security group aliases (stored as MapAttribute)
        proxy (list[ProxyFacts], optional): List of proxy endpoint details
        proxy_host (str, optional): Proxy host
        proxy_port (int, optional): Proxy port
        proxy_url (str, optional): Proxy URL
        no_proxy (str, optional): No-proxy list
        name_servers (list[str], optional): List of nameservers for the region
        tags (dict[str, Any], optional): Tags for deployment resources (stored as MapAttribute)

    Examples:
        >>> # Both formats work identically
        >>> region1 = RegionFacts(
        ...     aws_region="us-west-2",
        ...     az_count=3,
        ...     proxy_host="proxy.acme.com",
        ...     proxy_port=8080,
        ...     image_aliases={"ubuntu": "ami-12345", "amazon-linux": "ami-67890"},
        ...     tags={"Environment": "production", "Region": "us-west-2"},
        ...     security_aliases={
        ...         "corporate-cidrs": [
        ...             {"type": "CIDR", "value": "10.0.0.0/8", "description": "Corporate network"}
        ...         ]
        ...     }
        ... )

        >>> region2 = RegionFacts(
        ...     AwsRegion="us-west-2",
        ...     AzCount=3,
        ...     ProxyHost="proxy.acme.com",
        ...     ProxyPort=8080,
        ...     ImageAliases={"ubuntu": "ami-12345", "amazon-linux": "ami-67890"},
        ...     Tags={"Environment": "production", "Region": "us-west-2"},
        ...     SecurityAliases={
        ...         "corporate-cidrs": [
        ...             {"Type": "CIDR", "Value": "10.0.0.0/8", "Description": "Corporate network"}
        ...         ]
        ...     }
        ... )
    """

    aws_region = UnicodeAttribute(null=False, attr_name="AwsRegion")
    az_count = NumberAttribute(null=True, attr_name="AzCount")
    image_aliases = MapAttribute(of=UnicodeAttribute, null=True, attr_name="ImageAliases")
    min_successful_instances_percent = NumberAttribute(null=True, attr_name="MinSuccessfulInstancesPercent")
    security_aliases = MapAttribute(null=True, of=ListAttribute(of=SecurityAliasFacts), attr_name="SecurityAliases")
    security_group_aliases = MapAttribute(of=UnicodeAttribute, null=True, attr_name="SecurityGroupAliases")
    proxy = ListAttribute(of=ProxyFacts, null=True, attr_name="Proxy")
    proxy_host = UnicodeAttribute(null=True, attr_name="ProxyHost")
    proxy_port = NumberAttribute(null=True, attr_name="ProxyPort")
    proxy_url = UnicodeAttribute(null=True, attr_name="ProxyUrl")
    no_proxy = UnicodeAttribute(null=True, attr_name="NoProxy")
    name_servers = ListAttribute(of=UnicodeAttribute, null=True, attr_name="NameServers")
    tags = MapAttribute(null=True, attr_name="Tags")


class ZoneFactsModel(DatabaseTable):
    """Zone facts model for client-specific zone registry tables.

    This model represents a complete zone configuration including AWS account details, regional settings,
    network configurations, security aliases, proxy settings, and deployment metadata for infrastructure
    automation.

    A Zone is a deployment boundary that contains applications deployed together in a specific AWS Account,
    with multiple region definitions and shared infrastructure configuration.

    Attributes:
         zone (str): Zone identifier (hash key)
             Unique zone name within the client namespace
             Example: "production-east", "dev-west", "staging-central"
         account_facts (AccountFacts): AWS Account details for the zone including:
             - Account ID and organizational unit information
             - KMS key configuration for encryption
             - Network aliases (VPC and subnet mappings)
             - Resource namespace and naming conventions
             - Environment classification and tags
         region_facts (dict[str, RegionFacts]): Region details mapped by AWS region name containing:
             - Regional proxy and network configurations
             - Security aliases and group mappings
             - Image aliases for AMI references
             - Availability zone counts and deployment settings
             - Regional tags and metadata
        tags (dict[str, Any], optional): Global tags for deployment resources (stored as MapAttribute)
             Key-value pairs applied to all resources in the zone
             Example: {"Environment": "production", "Owner": "platform-team"}

    Note:
        **Zone Structure**: Zones are deployment boundaries that define:

        - **AWS Account Assignment**: Which AWS account contains the zone's resources
        - **Regional Configuration**: Settings for each AWS region the zone supports
        - **Security Configuration**: KMS keys, security aliases, and group mappings
        - **Network Configuration**: VPC/subnet aliases, proxy settings, nameservers
        - **Deployment Settings**: Success thresholds, image aliases, tagging strategy

        **Access Control**: Zone configuration requires specific administrative roles:

        - **NetworkAdmin Role**: Required for AccountFacts, RegionFacts network settings
        - **SecurityAdmin Role**: Required for KMS configuration and SecurityAliases
        - **General Access**: Tags and basic zone metadata can be modified by zone owners

        **Regional Configuration**: Each zone supports multiple AWS regions with independent configuration:

        - **Network Settings**: Region-specific proxy, nameservers, and network aliases
        - **Security Settings**: Regional security groups and security aliases
        - **Image Management**: Region-specific AMI aliases for deployment pipelines
        - **Deployment Settings**: Availability zone counts and success thresholds

        **Factory Pattern**: ZoneFactsModel uses client-specific tables:

        - **Client "acme"**: Table "acme-core-automation-zone"
        - **Client "enterprise"**: Table "enterprise-core-automation-zone"
        - **Isolation**: Each client's data is completely separated

         The hierarchy is: Zone -> Portfolio -> App -> Branch -> Build -> Component

    Examples:
        >>> # Both formats work identically (thanks to DatabaseTable)
        >>> # Snake case (Python style)
        >>> zone1 = ZoneFactsModel(
        ...     zone="production-east",
        ...     account_facts={
        ...         "aws_account_id": "123456789012",
        ...         "environment": "prod",
        ...         "kms": {"aws_account_id": "123456789012", "delegate_aws_account_ids": ["123456789012"]}
        ...     },
        ...     region_facts={
        ...         "us-east-1": {
        ...             "aws_region": "us-east-1",
        ...             "az_count": 3,
        ...             "proxy_host": "proxy.acme.com"
        ...         }
        ...     },
        ...     tags={"Environment": "production", "Owner": "platform-team"}
        ... )

        >>> # PascalCase (DynamoDB style)
        >>> zone2 = ZoneFactsModel(
        ...     Zone="production-east",
        ...     AccountFacts={
        ...         "AwsAccountId": "123456789012",
        ...         "Environment": "prod",
        ...         "Kms": {"AwsAccountId": "123456789012", "DelegateAwsAccountIds": ["123456789012"]}
        ...     },
        ...     RegionFacts={
        ...         "us-east-1": {
        ...             "AwsRegion": "us-east-1",
        ...             "AzCount": 3,
        ...             "ProxyHost": "proxy.acme.com"
        ...         }
        ...     },
        ...     Tags={"Environment": "production", "Owner": "platform-team"}
        ... )
    """

    class Meta(DatabaseTable.Meta):
        """Meta class for ZoneFactsModel DynamoDB table configuration.

        Inherits configuration from DatabaseTable.Meta including table naming,
        region settings, and billing mode.
        """

        pass

    # Composite primary key
    zone = UnicodeAttribute(hash_key=True, attr_name=ZONE_KEY)

    # Zone configuration
    account_facts = AccountFacts(null=False, attr_name="AccountFacts")
    region_facts = DictAttribute(of=RegionFacts, null=False, attr_name="RegionFacts")
    tags = MapAttribute(of=UnicodeAttribute, null=True, attr_name="Tags")

    def __repr__(self) -> str:
        """Return string representation of ZoneFactsModel.

                Returns:
                    str: String representation showing client and zone identifiers

                Examples:
        -            >>> zone = ZoneFactsModel(client="acme", zone="production-east")
        +            >>> zone = ZoneFactsModel(zone="production-east")
                    >>> repr(zone)
        -            '<ZoneFactsModel(client=acme,zone=production-east)>'
        +            '<ZoneFactsModel(zone=production-east)>'
        """
        return f"<ZoneFactsModel(zone={self.zone})>"


ZoneFactsType = Type[ZoneFactsModel]


class ZoneFactsFactory:
    """Factory class for creating client-specific ZoneFactsModel instances and managing tables.

    Provides methods for getting client-specific models, creating/deleting tables,
    and checking table existence. Acts as a wrapper around TableFactory for ZoneFactsModel.

    Examples:
        >>> # Get client-specific model
        >>> client_model = ZoneFactsFactory.get_model("acme")

        >>> # Create table for client
        >>> ZoneFactsFactory.create_table("acme", wait=True)

        >>> # Check if table exists
        >>> exists = ZoneFactsFactory.exists("acme")

        >>> # Delete table
        >>> ZoneFactsFactory.delete_table("acme", wait=True)
    """

    @classmethod
    def get_model(cls, client_name: str) -> ZoneFactsType:
        """Get the ZoneFactsModel model for the given client.

        Args:
            client_name (str): The name of the client

        Returns:
            ZoneFactsType: The ZoneFactsModel model for the given client

        Examples:
            >>> model_class = ZoneFactsFactory.get_model("acme")
            >>> zone = model_class(zone="production-east")
        """
        return TableFactory.get_model(ZoneFactsModel, client=client_name)

    @classmethod
    def create_table(cls, client_name: str, wait: bool = True) -> bool:
        """Create the ZoneFactsModel table for the given client.

        Args:
            client_name (str): The name of the client
            wait (bool): Whether to wait for table creation to complete

        Returns:
            bool: True if table was created, False if it already exists

        Examples:
            >>> ZoneFactsFactory.create_table("acme", wait=True)
            True
        """
        return TableFactory.create_table(ZoneFactsModel, client_name, wait=wait)

    @classmethod
    def delete_table(cls, client_name: str, wait: bool = True) -> bool:
        """Delete the ZoneFactsModel table for the given client.

        Args:
            client_name (str): The name of the client
            wait (bool): Whether to wait for table deletion to complete

        Returns:
            bool: True if table was deleted, False if it did not exist

        Examples:
            >>> ZoneFactsFactory.delete_table("acme", wait=True)
            True
        """
        return TableFactory.delete_table(ZoneFactsModel, client_name, wait=wait)

    @classmethod
    def exists(cls, client_name: str) -> bool:
        """Check if the ZoneFactsModel table exists for the given client.

        Args:
            client_name (str): The name of the client

        Returns:
            bool: True if the table exists, False otherwise

        Examples:
            >>> ZoneFactsFactory.exists("acme")
            True
        """
        return TableFactory.exists(ZoneFactsModel, client_name)


class SecurityAliasFactsItem(BaseModel):
    """Pydantic model for SecurityAliasFacts MapAttribute.

    Provides validation and serialization for security alias information with PascalCase API aliases.

    Attributes:
        type (str): The type of alias (e.g., 'CIDR', 'SG', etc.)
        value (str): The value associated with the alias
        description (str, optional): A description of the alias

    Examples:
        >>> alias = SecurityAliasFactsItem(
        ...     Type="CIDR",
        ...     Value="10.0.0.0/8",
        ...     Description="Corporate network"
        ... )
    """

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(
        ...,
        alias="Type",
        description="The type of alias (e.g., 'CIDR', 'SG', etc.)",
    )
    value: str = Field(
        ...,
        alias="Value",
        description="The value associated with the alias",
    )
    description: Optional[str] = Field(
        None,
        alias="Description",
        description="A description of the alias",
    )


class KmsFactsItem(BaseModel):
    """Pydantic model for KmsFacts MapAttribute.

    Provides validation and serialization for KMS key information with PascalCase API aliases.

    Attributes:
        aws_account_id (str): AWS Account ID where KMS Keys are managed/centralized
        kms_key_arn (str, optional): The ARN of the KMS Key for this Zone
        kms_key (str, optional): The KMS Key ID for this Zone
        delegate_aws_account_ids (list[str]): List of AWS Account IDs that can use the KMS Key
        allow_sns (bool, optional): Whether SNS is allowed to use the KMS Key

    Examples:
        >>> kms = KmsFactsItem(
        ...     AwsAccountId="123456789012",
        ...     KmsKeyArn="arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
        ...     DelegateAwsAccountIds=["123456789012", "123456789013"]
        ... )
    """

    model_config = ConfigDict(populate_by_name=True)

    aws_account_id: str = Field(
        ...,
        alias="AwsAccountId",
        description="AWS Account ID where KMS Keys are managed/centralized",
    )
    kms_key_arn: Optional[str] = Field(
        None,
        alias="KmsKeyArn",
        description="The ARN of the KMS Key for this Zone",
    )
    kms_key: Optional[str] = Field(
        None,
        alias="KmsKey",
        description="The KMS Key ID for this Zone",
    )
    delegate_aws_account_ids: List[str] = Field(
        ...,
        alias="DelegateAwsAccountIds",
        description="List of AWS Account IDs that can use the KMS Key",
    )
    allow_sns: Optional[bool] = Field(
        None,
        alias="AllowSNS",
        description="Whether SNS is allowed to use the KMS Key",
    )


class ProxyFactsItem(BaseModel):
    """Pydantic model for ProxyFacts MapAttribute.

    Provides validation and serialization for proxy configuration with PascalCase API aliases.

    Attributes:
        host (str, optional): Proxy host (e.g., 'proxy.acme.com')
        port (str, optional): Proxy port (e.g., '8080')
        url (str, optional): Proxy URL (e.g., 'http://proxy.acme.com:8080')
        no_proxy (str, optional): No-proxy list (e.g., '*.acme.com,10/8,192.168/16')

    Examples:
        >>> proxy = ProxyFactsItem(
        ...     Host="proxy.acme.com",
        ...     Port="8080",
        ...     Url="http://proxy.acme.com:8080",
        ...     NoProxy="*.acme.com,10.0.0.0/8"
        ... )
    """

    model_config = ConfigDict(populate_by_name=True)

    host: Optional[str] = Field(
        None,
        alias="Host",
        description="Proxy host (e.g., 'proxy.acme.com')",
    )
    port: Optional[str] = Field(
        None,
        alias="Port",
        description="Proxy port (e.g., '8080')",
    )
    url: Optional[str] = Field(
        None,
        alias="Url",
        description="Proxy URL (e.g., 'http://proxy.acme.com:8080')",
    )
    no_proxy: Optional[str] = Field(
        None,
        alias="NoProxy",
        description="No-proxy list (e.g., '*.acme.com,10/8,192.168/16')",
    )


class AccountFactsItem(BaseModel):
    """Pydantic model for AccountFacts MapAttribute.

    Provides validation and serialization for AWS account information with PascalCase API aliases.

    Attributes:
        organizational_unit (str, optional): The Organizational Unit name
        aws_account_id (str): The AWS Account ID
        account_name (str, optional): The name of the account
        environment (str, optional): The environment (e.g., 'prod', 'dev')
        kms (KmsFactsItem, optional): KMS Key details
        resource_namespace (str, optional): Namespace for resources
        network_name (str, optional): Name of the network
        vpc_aliases (list[str], optional): VPC aliases created by network pipelines
        subnet_aliases (list[str], optional): Subnet aliases created by network pipelines
        tags (dict[str, Any], optional): Tags to merge into facts for this deployment

    Examples:
        >>> account = AccountFactsItem(
        ...     AwsAccountId="123456789012",
        ...     AccountName="ACME Production",
        ...     Environment="prod"
        ... )
    """

    model_config = ConfigDict(populate_by_name=True)

    organizational_unit: Optional[str] = Field(
        None,
        alias="OrganizationalUnit",
        description="The Organizational Unit name",
    )
    aws_account_id: str = Field(
        ...,
        alias="AwsAccountId",
        description="The AWS Account ID",
    )
    account_name: Optional[str] = Field(
        None,
        alias="AccountName",
        description="The name of the account",
    )
    environment: Optional[str] = Field(
        None,
        alias="Environment",
        description="The environment (e.g., 'prod', 'dev')",
    )
    kms: Optional[KmsFactsItem] = Field(
        None,
        alias="Kms",
        description="KMS Key details",
    )
    resource_namespace: Optional[str] = Field(
        None,
        alias="ResourceNamespace",
        description="Namespace for resources",
    )
    network_name: Optional[str] = Field(
        None,
        alias="NetworkName",
        description="Name of the network",
    )
    vpc_aliases: Optional[List[str]] = Field(
        None,
        alias="VpcAliases",
        description="VPC aliases created by network pipelines",
    )
    subnet_aliases: Optional[List[str]] = Field(
        None,
        alias="SubnetAliases",
        description="Subnet aliases created by network pipelines",
    )
    tags: Optional[Dict[str, Any]] = Field(
        None,
        alias="Tags",
        description="Tags to merge into facts for this deployment",
    )


class RegionFactsItem(BaseModel):
    """Pydantic model for RegionFacts MapAttribute.

    Provides validation and serialization for AWS region configuration with PascalCase API aliases.

    Attributes:
        aws_region (str): The AWS region code (e.g., 'us-west-2')
        az_count (int, optional): Number of Availability Zones in the region
        image_aliases (dict[str, str], optional): Aliases for AMIs created by image pipelines (stored as MapAttribute)
        min_successful_instances_percent (int, optional): Minimum percent of successful instances for deployment
        security_aliases (dict[str, list[SecurityAliasFactsItem]], optional): Security aliases published by the security team
        security_group_aliases (dict[str, str], optional): Security group aliases
        proxy (list[ProxyFactsItem], optional): List of proxy endpoint details
        proxy_host (str, optional): Proxy host
        proxy_port (int, optional): Proxy port
        proxy_url (str, optional): Proxy URL
        no_proxy (str, optional): No-proxy list
        name_servers (list[str], optional): List of nameservers for the region
        tags (dict[str, Any], optional): Tags for deployment resources

    Examples:
        >>> region = RegionFactsItem(
        ...     AwsRegion="us-west-2",
        ...     AzCount=3,
        ...     ProxyHost="proxy.acme.com",
        ...     ProxyPort=8080
        ... )
    """

    model_config = ConfigDict(populate_by_name=True)

    aws_region: str = Field(
        ...,
        alias="AwsRegion",
        description="The AWS region code (e.g., 'us-west-2')",
    )
    az_count: Optional[int] = Field(
        None,
        alias="AzCount",
        description="Number of Availability Zones in the region",
    )
    image_aliases: Optional[Dict[str, str]] = Field(
        None,
        alias="ImageAliases",
        description="Aliases for AMIs created by image pipelines",
    )
    min_successful_instances_percent: Optional[int] = Field(
        None,
        alias="MinSuccessfulInstancesPercent",
        description="Minimum percent of successful instances for deployment",
    )
    security_aliases: Optional[Dict[str, List[SecurityAliasFactsItem]]] = Field(
        None,
        alias="SecurityAliases",
        description="Security aliases published by the security team",
    )
    security_group_aliases: Optional[Dict[str, str]] = Field(
        None,
        alias="SecurityGroupAliases",
        description="Security group aliases",
    )
    proxy: Optional[List[ProxyFactsItem]] = Field(
        None,
        alias="Proxy",
        description="List of proxy endpoint details",
    )
    proxy_host: Optional[str] = Field(
        None,
        alias="ProxyHost",
        description="Proxy host",
    )
    proxy_port: Optional[int] = Field(
        None,
        alias="ProxyPort",
        description="Proxy port",
    )
    proxy_url: Optional[str] = Field(
        None,
        alias="ProxyUrl",
        description="Proxy URL",
    )
    no_proxy: Optional[str] = Field(
        None,
        alias="NoProxy",
        description="No-proxy list",
    )
    name_servers: Optional[List[str]] = Field(
        None,
        alias="NameServers",
        description="List of nameservers for the region",
    )
    tags: Optional[Dict[str, Any]] = Field(
        None,
        alias="Tags",
        description="Tags for deployment resources",
    )


# =============================================================================
# Main Pydantic Model
# =============================================================================


class ZoneFact(RegistryFact):
    """Pydantic model for Zone Facts with validation and serialization.

        Provides type validation, PascalCase serialization for APIs,
        and conversion methods between PynamoDB and API formats.

        Inherits audit fields (created_at, updated_at) from RegistryFact.

        Attributes:
            zone (str): Zone identifier (unique zone name within client namespace)
            account_facts (AccountFactsItem): AWS Account details for the zone
            region_facts (dict[str, RegionFactsItem]): Region details mapped by AWS region name
    -        tags (dict[str, str], optional): Global tags for deployment resources
    +        tags (dict[str, Any], optional): Global tags for deployment resources

        Examples:
            >>> # Create zone fact with validation
            >>> zone = ZoneFact(
            ...     Zone="production-east",
            ...     AccountFacts={"AwsAccountId": "123456789012"},
            ...     RegionFacts={"us-east-1": {"AwsRegion": "us-east-1"}}
            ... )

            >>> # Convert from DynamoDB model
            >>> db_zone = ZoneFactsModel(zone="production-east")
            >>> pydantic_zone = ZoneFact.from_dynamodb(db_zone)

    """

    # Core Zone Fields with PascalCase aliases
    zone: str = Field(
        ...,
        alias="Zone",
        description="Zone identifier (unique zone name within client namespace)",
    )
    # Complex Zone Configuration Fields
    account_facts: AccountFactsItem = Field(
        ...,
        alias="AccountFacts",
        description="AWS Account details for the zone",
    )
    region_facts: Dict[str, RegionFactsItem] = Field(
        ...,
        alias="RegionFacts",
        description="Region details mapped by AWS region name",
    )
    tags: Optional[Dict[str, Any]] = Field(
        None,
        alias="Tags",
        description="Global tags for deployment resources",
    )

    @classmethod
    def from_model(cls, model: ZoneFactsModel) -> "ZoneFact":
        """Convert PynamoDB ZoneFactsModel to Pydantic ZoneFact.

        Args:
            zone_model (ZoneFactsModel): PynamoDB ZoneFactsModel instance

        Returns:
            ZoneFact: Pydantic ZoneFact instance

        Examples:
            >>> db_zone = ZoneFactsModel(zone="production-east")
            >>> pydantic_zone = ZoneFact.from_dynamodb(db_zone)
        """
        return cls(**model.to_simple_dict())

    def to_model(self, client: str):
        """Convert Pydantic ZoneFact to PynamoDB ZoneFactsModel.

        Returns:
            ZoneFactsModel: PynamoDB ZoneFactsModel instance

        """
        model_class = ZoneFactsFactory.get_model(client)
        return model_class(**self.model_dump(by_alias=False, exclude_none=True))

    @classmethod
    def model_class(cls, client: str) -> ZoneFactsType:
        """Get the PynamoDB model class for this Pydantic model.

        Args:
            client (str): Client name for table selection

        Returns:
            ZoneFactsType: Client-specific PynamoDB ZoneFactsModel class

        Examples:
            >>> model_class = ZoneFact.get_database_model("acme")
            >>> zone = model_class(zone="production-east")
        """
        return ZoneFactsFactory.get_model(client)

    def __repr__(self) -> str:
        """String representation for debugging.

        Returns:
            str: String representation of the zone fact

        Examples:
             >>> zone = ZoneFact(Zone="production-east", AccountFacts={...}, RegionFacts={...})
             >>> repr(zone)
             '<ZoneFact(zone=production-east)>'
        """
        return f"<ZoneFact(zone={self.zone})>"
