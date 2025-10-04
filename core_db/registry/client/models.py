"""Client registry model for the core-automation-clients DynamoDB table.

This module provides PynamoDB and Pydantic models for client organization configuration
in the Core Automation platform. Client records store comprehensive organization information
including AWS account details, regional configurations, bucket names, and automation settings.

Key Components:
    - **ClientFactsModel**: PynamoDB model for client organization data stored in global table
    - **ClientFactsFactory**: Factory for global client registry table management
    - **ClientFact**: Pydantic model with validation and serialization capabilities

Client records serve as the foundation of the registry hierarchy and enable
multi-tenant operation with client-specific configurations and resource isolation.
The client registry uses a single global table since it stores the client definitions themselves.
"""

from typing import Optional, Type, List
from pydantic import BaseModel, Field, ConfigDict

from pynamodb.attributes import UnicodeAttribute, ListAttribute, MapAttribute

from ...models import TableFactory, DatabaseRecord, DatabaseTable


class ClientFactsModel(DatabaseTable):

    class Meta(DatabaseTable.Meta):

        pass

    # Primary key
    client = UnicodeAttribute(hash_key=True, attr_name="Client")

    # Core client metadata
    client_id = UnicodeAttribute(null=True, attr_name="ClientId")
    client_secret = UnicodeAttribute(null=True, attr_name="ClientSecret")
    client_type = UnicodeAttribute(null=True, attr_name="ClientType")
    client_status = UnicodeAttribute(null=True, attr_name="ClientStatus")
    client_description = UnicodeAttribute(null=True, attr_name="ClientDescription")
    client_name = UnicodeAttribute(null=True, attr_name="ClientName")
    client_scopes = ListAttribute(of=UnicodeAttribute, null=True, attr_name="ClientScopes")
    client_redirect_urls = ListAttribute(of=UnicodeAttribute, null=True, attr_name="ClientRedirectUrls")

    # AWS Organization configuration
    organization_id = UnicodeAttribute(null=True, attr_name="OrganizationId")
    organization_name = UnicodeAttribute(null=True, attr_name="OrganizationName")
    organization_account = UnicodeAttribute(null=True, attr_name="OrganizationAccount")
    organization_email = UnicodeAttribute(null=True, attr_name="OrganizationEmail")

    # Domain and networking
    domain = UnicodeAttribute(null=True, attr_name="Domain")
    homepage = UnicodeAttribute(null=True, attr_name="Homepage")

    # AWS Account assignments for multi-account architecture
    iam_account = UnicodeAttribute(null=True, attr_name="IamAccount")
    audit_account = UnicodeAttribute(null=True, attr_name="AuditAccount")
    automation_account = UnicodeAttribute(null=True, attr_name="AutomationAccount")
    security_account = UnicodeAttribute(null=True, attr_name="SecurityAccount")
    network_account = UnicodeAttribute(null=True, attr_name="NetworkAccount")

    # Regional configuration for deployment targeting
    master_region = UnicodeAttribute(null=True, attr_name="MasterRegion")
    client_region = UnicodeAttribute(null=True, attr_name="ClientRegion")
    bucket_region = UnicodeAttribute(null=True, attr_name="BucketRegion")

    # S3 bucket configuration for artifact storage
    bucket_name = UnicodeAttribute(null=True, attr_name="BucketName")
    docs_bucket_name = UnicodeAttribute(null=True, attr_name="DocsBucketName")
    artefact_bucket_name = UnicodeAttribute(null=True, attr_name="ArtefactBucketName")
    ui_bucket_name = UnicodeAttribute(null=True, attr_name="UiBucketName")
    ui_bucket = UnicodeAttribute(null=True, attr_name="UiBucket")  # Legacy field
    tags = MapAttribute(null=True, attr_name="Tags")
    tag_policy = ListAttribute(of=MapAttribute, null=True, attr_name="TagPolicy")

    # Resource naming and scoping
    scope = UnicodeAttribute(null=True, attr_name="Scope")

    def __repr__(self) -> str:
        return f"<ClientFactsModel(client={self.client},name={self.client_name})>"

    def get_resource_prefix(self) -> str:
        scope = self.scope or ""
        return f"{scope}{self.client}"

    def get_bucket_name(self, bucket_type: str = "automation") -> str:
        bucket_mapping = {
            "automation": self.bucket_name,
            "docs": self.docs_bucket_name,
            "artefacts": self.artefact_bucket_name,
            "ui": self.ui_bucket_name or self.ui_bucket,
        }

        if bucket_type not in bucket_mapping:
            raise ValueError(f"Unknown bucket type: {bucket_type}. Valid types: {list(bucket_mapping.keys())}")

        return bucket_mapping[bucket_type]

    def is_multi_account(self) -> bool:
        accounts = {
            self.organization_account,
            self.iam_account,
            self.audit_account,
            self.automation_account,
            self.security_account,
            self.network_account,
        }
        accounts.discard(None)  # type: ignore

        return len(accounts) > 1


ClientFactsType = Type[ClientFactsModel]


class ClientFactsFactory:

    @classmethod
    def get_model(cls) -> ClientFactsType:
        return TableFactory.get_model(ClientFactsModel)

    @classmethod
    def create_table(cls, wait: bool = True) -> bool:
        return TableFactory.create_table(ClientFactsModel, wait=wait)

    @classmethod
    def delete_table(cls, wait: bool = True) -> bool:
        return TableFactory.delete_table(ClientFactsModel, wait=wait)

    @classmethod
    def exists(cls) -> bool:
        return TableFactory.exists(ClientFactsModel)


class TagPolicyFact(BaseModel):

    model_config = ConfigDict(populate_by_name=True)

    tag_name: str = Field(
        None,
        alias="Tags",
        description="Tags to apply to all automation-created resources",
    )
    required: bool = Field(
        False,
        alias="Required",
        description="Whether tags are required on resources",
    )
    description: str = Field(
        "",
        alias="Description",
        description="Description of the tag policy.  Why the tag is required and what it is used for.",
    )

    def model_dump(self, *args, **kwargs) -> dict:
        kwargs.setdefault("exclude_none", True)
        kwargs.setdefault("by_alias", True)
        return super().model_dump(*args, **kwargs)


class ClientFact(DatabaseRecord):

    client: str = Field(
        ...,
        alias="Client",
        description="Client ID or slug as the unique identifier for the client organization",
    )
    # Core Client Fields with PascalCase aliases
    client_id: Optional[str] = Field(
        default=None,
        alias="ClientId",
        description="Alternative client identifier for external system integration",
    )
    client_secret: Optional[str] = Field(
        default=None,
        alias="ClientSecret",
        description="Client secret used for confidential client authentication",
    )
    client_type: Optional[str] = Field(
        default=None,
        alias="ClientType",
        description="Type classification of the client organization",
    )
    client_status: Optional[str] = Field(
        default=None,
        alias="ClientStatus",
        description="Current operational status of the client",
    )
    client_description: Optional[str] = Field(
        default=None,
        alias="ClientDescription",
        description="Detailed description of the client organization and its purpose",
    )
    # Client Identification
    client_name: Optional[str] = Field(
        default=None,
        alias="ClientName",
        description="Human-readable client organization name for display purposes",
    )
    client_scopes: Optional[list[str]] = Field(
        default=None,
        alias="ClientScopes",
        description="List of OAuth 2.0 scopes granted to the client",
    )
    client_redirect_urls: list[str] = Field(
        default=None,
        alias="ClientRedirectUrls",
        description="List of redirect URIs for the client",
    )
    # AWS Organization Configuration
    organization_id: Optional[str] = Field(
        default=None,
        alias="OrganizationId",
        description="AWS Organization ID for the client's AWS Organization structure",
    )
    organization_name: Optional[str] = Field(
        default=None,
        alias="OrganizationName",
        description="AWS Organization name as configured in AWS Organizations service",
    )
    organization_account: Optional[str] = Field(
        default=None,
        alias="OrganizationAccount",
        description="AWS account number for the organization root account",
    )
    organization_email: Optional[str] = Field(
        default=None,
        alias="OrganizationEmail",
        description="Email address associated with the organization root account",
    )
    # Domain and Networking
    domain: Optional[str] = Field(
        default=None,
        alias="Domain",
        description="Primary domain name for the organization's web presence",
    )
    homepage: Optional[str] = Field(
        default=None,
        alias="Homepage",
        description="Homepage URL for the organization's web presence",
    )
    # AWS Account Assignments
    iam_account: Optional[str] = Field(
        default=None,
        alias="IamAccount",
        description="AWS account number where centralized IAM roles and policies are stored",
    )
    audit_account: Optional[str] = Field(
        default=None,
        alias="AuditAccount",
        description="AWS account number for centralized logging and audit trail storage",
    )
    automation_account: Optional[str] = Field(
        default=None,
        alias="AutomationAccount",
        description="AWS account number where automation artifacts and resources are stored",
    )
    security_account: Optional[str] = Field(
        default=None,
        alias="SecurityAccount",
        description="AWS account number for centralized security operations center",
    )
    network_account: Optional[str] = Field(
        default=None,
        alias="NetworkAccount",
        description="AWS account number for centralized VPCs, DNS, and network services",
    )

    # Regional Configuration
    master_region: Optional[str] = Field(
        default=None,
        alias="MasterRegion",
        description="Primary AWS region where Core Automation control plane is deployed",
    )
    client_region: Optional[str] = Field(
        default=None,
        alias="ClientRegion",
        description="Default AWS region for client operations when region is not specified",
    )
    bucket_region: Optional[str] = Field(
        default=None,
        alias="BucketRegion",
        description="AWS region where the primary automation bucket is located",
    )

    # S3 Bucket Configuration
    bucket_name: Optional[str] = Field(
        default=None,
        alias="BucketName",
        description="Primary S3 bucket name for automation artifacts and deployment packages",
    )
    docs_bucket_name: Optional[str] = Field(
        default=None,
        alias="DocsBucketName",
        description="S3 bucket name for storing generated documentation and reports",
    )
    artefact_bucket_name: Optional[str] = Field(
        default=None,
        alias="ArtefactBucketName",
        description="S3 bucket name for storing deployment artifacts and build outputs",
    )
    ui_bucket_name: Optional[str] = Field(
        default=None,
        alias="UiBucketName",
        description="S3 bucket name for hosting the Core Automation web interface",
    )
    ui_bucket: Optional[str] = Field(
        default=None,
        alias="UiBucket",
        description="Alternative S3 bucket name for UI hosting (legacy field, deprecated)",
    )
    # Resource Naming
    scope: Optional[str] = Field(
        default=None,
        alias="Scope",
        description="Resource name prefix for all automation-created resources to ensure uniqueness",
    )
    tags: Optional[dict[str, str]] = Field(
        default=None,
        alias="Tags",
        description="Tags to apply to all automation-created resources",
    )
    tag_policy: Optional[List[TagPolicyFact]] = Field(
        default=None,
        alias="TagPolicy",
        description="Policy governing the application of tags to resources",
    )

    def get_resource_prefix(self) -> str:
        scope = self.scope or ""
        return f"{scope}{self.client}"

    def get_bucket_name(self, bucket_type: str = "automation") -> str:
        bucket_mapping = {
            "automation": self.bucket_name,
            "docs": self.docs_bucket_name,
            "artefacts": self.artefact_bucket_name,
            "ui": self.ui_bucket_name or self.ui_bucket,
        }

        if bucket_type not in bucket_mapping:
            raise ValueError(f"Unknown bucket type: {bucket_type}. Valid types: {list(bucket_mapping.keys())}")

        return bucket_mapping[bucket_type] or ""

    def is_multi_account(self) -> bool:
        accounts = {
            self.organization_account,
            self.iam_account,
            self.audit_account,
            self.automation_account,
            self.security_account,
            self.network_account,
        }
        # Remove None values and check if more than one unique account
        accounts.discard(None)
        return len(accounts) > 1

    @classmethod
    def from_model(cls, model: ClientFactsModel) -> "ClientFact":
        return cls(**model.to_simple_dict())

    @classmethod
    def model_class(cls) -> ClientFactsType:
        return ClientFactsFactory.get_model()

    def to_model(self) -> ClientFactsModel:
        model_class = ClientFactsFactory.get_model()
        return model_class(**self.model_dump(include_secrets=True, by_alias=False, exclude_none=True))

    def model_dump(self, **kwargs) -> dict:
        if "include_secrets" in kwargs and not kwargs.pop("include_secrets", False):
            kwargs["exclude"] = {kwargs.get("exclude", set()) | {"client_secret"}}

        return super().model_dump(**kwargs)

    def __repr__(self) -> str:
        return f"<ClientFact(client={self.client},name={self.client_name})>"
