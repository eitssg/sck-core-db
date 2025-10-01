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

from ...models import TableFactory, DatabaseTable, EnhancedMapAttribute, DictAttribute
from ..models import RegistryFact


class SecurityAliasFacts(EnhancedMapAttribute):
    """
    Attributes:
        type: The type of alias (e.g., 'CIDR', 'SG', etc.).
        value: The value associated with the alias.
        description: A description of the alias.
    """

    type = UnicodeAttribute(null=False, attr_name="Type")
    value = UnicodeAttribute(null=False, attr_name="Value")
    description = UnicodeAttribute(null=True, attr_name="Description")


class KmsFacts(EnhancedMapAttribute):
    """
    Attributes:
        aws_account_id: AWS Account ID where KMS Keys are managed/centralized.
        kms_key_arn: The ARN of the KMS Key for this Zone.
        kms_key: The KMS Key ID for this Zone.
        delegate_aws_account_ids: List of AWS Account IDs that can use the KMS Key
        allow_sns: Whether SNS is allowed to use the KMS Key.
    """

    aws_account_id = UnicodeAttribute(null=False, attr_name="AwsAccountId")
    kms_key_arn = UnicodeAttribute(null=True, attr_name="KmsKeyArn")
    kms_key = UnicodeAttribute(null=True, attr_name="KmsKey")
    delegate_aws_account_ids = ListAttribute(of=UnicodeAttribute, null=False, attr_name="DelegateAwsAccountIds")
    allow_sns = BooleanAttribute(null=True, attr_name="AllowSNS")


class AccountFacts(EnhancedMapAttribute):
    """
    Attributes:
        organizational_unit: The Organizational Unit name.
        aws_account_id: The AWS Account ID.
        account_name: The name of the account.
        environment: The environment (e.g., 'prod', 'dev').
        kms: KMS Key details.
        resource_namespace: Namespace for resources.
        network_name: Name of the network.
        vpc_aliases: VPC aliases created by network pipelines.
        subnet_aliases: Subnet aliases created by network pipelines.
        tags: Tags to merge into facts for this deployment.
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
    """
    Attributes:
        host: Proxy host (e.g., 'proxy.acme.com').
        port: Proxy port (e.g., '8080').
        url: Proxy URL (e.g., 'http://proxy.acme.com:8080').
        no_proxy: No-proxy list (e.g., '*.acme.com,10/8,192.168/16').
    """

    host = UnicodeAttribute(null=True, attr_name="Host")
    port = UnicodeAttribute(null=True, attr_name="Port")
    url = UnicodeAttribute(null=True, attr_name="Url")
    no_proxy = UnicodeAttribute(null=True, attr_name="NoProxy")


class RegionFacts(EnhancedMapAttribute):
    """
    Attributes:
        aws_region: The AWS region code (e.g., 'us-west-2').
        az_count: Number of Availability Zones in the region.
        image_aliases: Aliases for AMIs created by image pipelines.
        min_successful_instances_percent: Minimum percent of successful instances for deployment.
        security_aliases: Security aliases published by the security team.
        security_group_aliases: Security group aliases.
        proxy: List of proxy endpoint details.
        proxy_host: Proxy host.
        proxy_port: Proxy port.
        proxy_url: Proxy URL.
        no_proxy: No-proxy list.
        name_servers: List of nameservers for the region.
        tags: Tags for deployment resources.
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
    """
    Attributes:
        zone: Zone identifier (unique zone name within client namespace).
        account_facts: AWS Account details for the zone.
        region_facts: Region details mapped by AWS region name.
        tags: Global tags for deployment resources.
    """

    class Meta(DatabaseTable.Meta):

        pass

    # Composite primary key
    zone = UnicodeAttribute(hash_key=True, attr_name="Zone")

    # Zone configuration
    account_facts = AccountFacts(null=False, attr_name="AccountFacts")
    region_facts = DictAttribute(of=RegionFacts, null=False, attr_name="RegionFacts")
    tags = MapAttribute(of=UnicodeAttribute, null=True, attr_name="Tags")

    def __repr__(self) -> str:
        return f"<ZoneFactsModel(zone={self.zone})>"


ZoneFactsType = Type[ZoneFactsModel]


class ZoneFactsFactory:

    @classmethod
    def get_model(cls, client_name: str) -> ZoneFactsType:
        return TableFactory.get_model(ZoneFactsModel, client=client_name)

    @classmethod
    def create_table(cls, client_name: str, wait: bool = True) -> bool:
        return TableFactory.create_table(ZoneFactsModel, client_name, wait=wait)

    @classmethod
    def delete_table(cls, client_name: str, wait: bool = True) -> bool:
        return TableFactory.delete_table(ZoneFactsModel, client_name, wait=wait)

    @classmethod
    def exists(cls, client_name: str) -> bool:
        return TableFactory.exists(ZoneFactsModel, client_name)


class SecurityAliasFactsItem(BaseModel):

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
        return cls(**model.to_simple_dict())

    @classmethod
    def model_class(cls, client: str) -> ZoneFactsType:
        return ZoneFactsFactory.get_model(client)

    def to_model(self, client: str) -> ZoneFactsModel:
        model_class = ZoneFactsFactory.get_model(client)
        return model_class(**self.model_dump(by_alias=False, exclude_none=True))

    def __repr__(self) -> str:
        return f"<ZoneFact(zone={self.zone})>"
