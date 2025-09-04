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

import re
from turtle import home
from typing import Optional, Type
from pydantic import Field

from pynamodb.attributes import UnicodeAttribute, ListAttribute

from ...models import TableFactory, DatabaseRecord, DatabaseTable


class ClientFactsModel(DatabaseTable):
    """PynamoDB model representing client organization configuration in the core-automation-clients table.

    This model stores comprehensive client organization information including AWS account details,
    regional configurations, bucket names, and automation settings. ClientFactsModel serves as the
    central registry for client organizations using the Core Automation platform.

    Attributes:
        client (UnicodeAttribute): Client ID or slug as the unique identifier for the client organization (hash key)
        client_id (UnicodeAttribute): Alternative client identifier for external system integration
        client_type (UnicodeAttribute): Type classification of the client (e.g., 'enterprise', 'startup', 'government')
        client_status (UnicodeAttribute): Current operational status of the client ('active', 'inactive', 'suspended')
        client_description (UnicodeAttribute): Detailed description of the client organization and its purpose
        client_name (UnicodeAttribute): Human-readable client organization name for display purposes
        organization_id (UnicodeAttribute): AWS Organization ID for the client's AWS Organization structure
        organization_name (UnicodeAttribute): AWS Organization name as configured in AWS Organizations service
        organization_account (UnicodeAttribute): AWS account number for the organization root account
        organization_email (UnicodeAttribute): Email address associated with the organization root account
        domain (UnicodeAttribute): Primary domain name for the organization's web presence
        iam_account (UnicodeAttribute): AWS account number where centralized IAM roles and policies are stored
        audit_account (UnicodeAttribute): AWS account number for centralized logging and audit trail storage
        automation_account (UnicodeAttribute): AWS account number where automation artifacts and resources are stored
        security_account (UnicodeAttribute): AWS account number for centralized security operations center
        network_account (UnicodeAttribute): AWS account number for centralized VPCs, DNS, and network services
        master_region (UnicodeAttribute): Primary AWS region where Core Automation control plane is deployed
        client_region (UnicodeAttribute): Default AWS region for client operations when region is not specified
        bucket_region (UnicodeAttribute): AWS region where the primary automation bucket is located
        bucket_name (UnicodeAttribute): Primary S3 bucket name for automation artifacts and deployment packages
        docs_bucket_name (UnicodeAttribute): S3 bucket name for storing generated documentation and reports
        artefact_bucket_name (UnicodeAttribute): S3 bucket name for storing deployment artifacts and build outputs
        ui_bucket_name (UnicodeAttribute): S3 bucket name for hosting the Core Automation web interface
        ui_bucket (UnicodeAttribute): Alternative S3 bucket name for UI hosting (legacy field, deprecated)
        scope (UnicodeAttribute): Resource name prefix for all automation-created resources to ensure uniqueness

        Inherited from DatabaseTable:
            created_at (UTCDateTimeAttribute): Timestamp when the record was first created (auto-generated)
            updated_at (UTCDateTimeAttribute): Timestamp when the record was last modified (auto-updated)

    Note:
        Uses a single global table for all clients since it stores the client registry itself.
        This table is accessed by the Core Automation platform infrastructure for multi-tenant operations.
        The hierarchy is: Client -> Portfolio -> App -> Branch -> Build -> Component
    """

    class Meta(DatabaseTable.Meta):
        """Meta class for ClientFactsModel DynamoDB table configuration.

        Inherits table configuration from DatabaseTable.Meta including:
        - billing_mode: PAY_PER_REQUEST for automatic scaling
        - stream_view_type: NEW_AND_OLD_IMAGES for change tracking
        - point_in_time_recovery: Enabled for data protection
        """

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

    # Resource naming and scoping
    scope = UnicodeAttribute(null=True, attr_name="Scope")

    def __repr__(self) -> str:
        """Return string representation of ClientFactsModel.

        Returns:
            str: String representation showing client identifier and name for debugging
        """
        return f"<ClientFactsModel(client={self.client},name={self.client_name})>"

    def get_resource_prefix(self) -> str:
        """Get the resource prefix for this client including scope.

        Returns:
            str: Resource prefix combining scope and client identifier for unique resource naming
        """
        scope = self.scope or ""
        return f"{scope}{self.client}"

    def get_bucket_name(self, bucket_type: str = "automation") -> str:
        """Get the appropriate bucket name for the specified type.

        Args:
            bucket_type (str): Type of bucket requested from available options

        Returns:
            str: Full bucket name for the specified type

        Raises:
            ValueError: If bucket_type is not one of the recognized types
        """
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
        """Check if this client uses a multi-account AWS setup.

        Returns:
            bool: True if multiple distinct AWS accounts are configured, False for single-account setup
        """
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


ClientFactsType = Type[ClientFactsModel]


class ClientFactsFactory:
    """Factory class for managing the global ClientFactsModel table.

    Provides methods for getting the global model class, creating/deleting the table,
    and checking table existence. Unlike other registry factories, this manages a single
    global table since client records define the clients themselves.

    Note:
        Client registry uses a single global table, not client-specific tables, because
        it stores the client definitions that enable multi-tenant operations.
    """

    @classmethod
    def get_model(cls, client: str) -> ClientFactsType:
        """Get the global ClientFactsModel class.

        Returns:
            ClientFactsType: Global ClientFactsModel class for client registry operations

        Note:
            Unlike other factories, this returns the base model class since client registry
            is global and not client-specific.
        """
        return TableFactory.get_model(ClientFactsModel, client=client)

    @classmethod
    def create_table(cls, client: str, wait: bool = True) -> bool:
        """Create the ClientFactsModel table for the given client.

        Args:
            wait (bool): Whether to wait for table creation to complete before returning

        Returns:
            bool: True if table was created successfully, False if it already exists

        Raises:
            Exception: If table creation fails due to AWS service issues
        """
        return TableFactory.create_table(ClientFactsModel, client, wait=wait)

    @classmethod
    def delete_table(cls, client: str, wait: bool = True) -> bool:
        """Delete the ClientFactsModel table for the given client.

        Args:
            wait (bool): Whether to wait for table deletion to complete before returning

        Returns:
            bool: True if table was deleted, False if it did not exist
        """
        return TableFactory.delete_table(ClientFactsModel, client, wait=wait)

    @classmethod
    def exists(cls, client: str) -> bool:
        """Check if the ClientFactsModel table exists for the given client.

        Args:
            client (str): The client identifier

        Returns:
            bool: True if the table exists, False otherwise
        """
        return TableFactory.exists(ClientFactsModel, client)


class ClientFact(DatabaseRecord):
    """Pydantic model for Client Facts with validation and serialization.

    Provides type validation, PascalCase serialization for APIs, and conversion methods
    between PynamoDB and API formats. Extends DatabaseRecord to inherit audit fields
    and serialization behavior.

    Attributes:
        client (str): Client ID or slug as the unique identifier for the client organization (required)
        client_id (str, optional): Alternative client identifier for external system integration
        client_type (str, optional): Type classification of the client organization
        client_status (str, optional): Current operational status of the client
        client_description (str, optional): Detailed description of the client organization
        client_name (str, optional): Human-readable client organization name for display
        organization_id (str, optional): AWS Organization ID for the client's AWS Organization
        organization_name (str, optional): AWS Organization name as configured in AWS Organizations
        organization_account (str, optional): AWS account number for the organization root account
        organization_email (str, optional): Email address associated with the organization root account
        domain (str, optional): Primary domain name for the organization's web presence
        iam_account (str, optional): AWS account number for centralized IAM roles and policies
        audit_account (str, optional): AWS account number for centralized logging and audit trails
        automation_account (str, optional): AWS account number for automation artifacts and resources
        security_account (str, optional): AWS account number for centralized security operations
        network_account (str, optional): AWS account number for centralized VPCs and network services
        master_region (str, optional): Primary AWS region for Core Automation control plane deployment
        client_region (str, optional): Default AWS region for client operations when not specified
        bucket_region (str, optional): AWS region where the primary automation bucket is located
        bucket_name (str, optional): Primary S3 bucket name for automation artifacts and packages
        docs_bucket_name (str, optional): S3 bucket name for generated documentation and reports
        artefact_bucket_name (str, optional): S3 bucket name for deployment artifacts and build outputs
        ui_bucket_name (str, optional): S3 bucket name for hosting the Core Automation web interface
        ui_bucket (str, optional): Alternative S3 bucket name for UI hosting (legacy field)
        scope (str, optional): Resource name prefix for all automation-created resources

        Inherited from DatabaseRecord:
            created_at (datetime): Timestamp when the record was first created (auto-generated)
            updated_at (datetime): Timestamp when the record was last modified (auto-updated)

    Note:
        All string fields use PascalCase aliases for API compatibility and DynamoDB attribute naming.
        The client field serves as both the Pydantic identifier and DynamoDB hash key.

    Examples:
        >>> # Create client with minimal required fields
        >>> client = ClientFact(
        ...     Client="acme-corp",
        ...     ClientName="ACME Corporation",
        ...     ClientType="enterprise",
        ...     ClientStatus="active"
        ... )

        >>> # Create client with full configuration
        >>> client = ClientFact(
        ...     Client="startup-tech",
        ...     ClientId="STARTUP001",
        ...     ClientName="StartupTech Inc",
        ...     ClientType="startup",
        ...     ClientStatus="active",
        ...     OrganizationAccount="987654321098",
        ...     IamAccount="987654321098",
        ...     MasterRegion="us-west-1",
        ...     BucketName="startup-tech-automation",
        ...     Scope="st-"
        ... )

        >>> # Convert from DynamoDB model
        >>> db_client = ClientFactsModel(client="acme-corp")
        >>> pydantic_client = ClientFact.from_model(db_client)

        >>> # Convert to DynamoDB format
        >>> db_model = client.to_model("global")
    """

    client: str = Field(
        ...,
        alias="Client",
        description="Client ID or slug as the unique identifier for the client organization",
    )
    # Core Client Fields with PascalCase aliases
    client_id: Optional[str] = Field(
        None,
        alias="ClientId",
        description="Alternative client identifier for external system integration",
    )
    client_secret: Optional[str] = Field(
        None,
        alias="ClientSecret",
        description="Client secret used for confidential client authentication",
    )
    client_type: Optional[str] = Field(
        None,
        alias="ClientType",
        description="Type classification of the client organization",
    )
    client_status: Optional[str] = Field(
        None,
        alias="ClientStatus",
        description="Current operational status of the client",
    )
    client_description: Optional[str] = Field(
        None,
        alias="ClientDescription",
        description="Detailed description of the client organization and its purpose",
    )
    # Client Identification
    client_name: Optional[str] = Field(
        None,
        alias="ClientName",
        description="Human-readable client organization name for display purposes",
    )
    client_scopes: Optional[list[str]] = Field(
        None,
        alias="ClientScopes",
        description="List of OAuth 2.0 scopes granted to the client",
    )
    client_redirect_urls: list[str] = Field(
        None,
        alias="ClientRedirectUrls",
        description="List of redirect URIs for the client",
    )
    # AWS Organization Configuration
    organization_id: Optional[str] = Field(
        None,
        alias="OrganizationId",
        description="AWS Organization ID for the client's AWS Organization structure",
    )
    organization_name: Optional[str] = Field(
        None,
        alias="OrganizationName",
        description="AWS Organization name as configured in AWS Organizations service",
    )
    organization_account: Optional[str] = Field(
        None,
        alias="OrganizationAccount",
        description="AWS account number for the organization root account",
    )
    organization_email: Optional[str] = Field(
        None,
        alias="OrganizationEmail",
        description="Email address associated with the organization root account",
    )
    # Domain and Networking
    domain: Optional[str] = Field(
        None,
        alias="Domain",
        description="Primary domain name for the organization's web presence",
    )
    homepage: Optional[str] = Field(
        None,
        alias="Homepage",
        description="Homepage URL for the organization's web presence",
    )
    # AWS Account Assignments
    iam_account: Optional[str] = Field(
        None,
        alias="IamAccount",
        description="AWS account number where centralized IAM roles and policies are stored",
    )
    audit_account: Optional[str] = Field(
        None,
        alias="AuditAccount",
        description="AWS account number for centralized logging and audit trail storage",
    )
    automation_account: Optional[str] = Field(
        None,
        alias="AutomationAccount",
        description="AWS account number where automation artifacts and resources are stored",
    )
    security_account: Optional[str] = Field(
        None,
        alias="SecurityAccount",
        description="AWS account number for centralized security operations center",
    )
    network_account: Optional[str] = Field(
        None,
        alias="NetworkAccount",
        description="AWS account number for centralized VPCs, DNS, and network services",
    )

    # Regional Configuration
    master_region: Optional[str] = Field(
        None,
        alias="MasterRegion",
        description="Primary AWS region where Core Automation control plane is deployed",
    )
    client_region: Optional[str] = Field(
        None,
        alias="ClientRegion",
        description="Default AWS region for client operations when region is not specified",
    )
    bucket_region: Optional[str] = Field(
        None,
        alias="BucketRegion",
        description="AWS region where the primary automation bucket is located",
    )

    # S3 Bucket Configuration
    bucket_name: Optional[str] = Field(
        None,
        alias="BucketName",
        description="Primary S3 bucket name for automation artifacts and deployment packages",
    )
    docs_bucket_name: Optional[str] = Field(
        None,
        alias="DocsBucketName",
        description="S3 bucket name for storing generated documentation and reports",
    )
    artefact_bucket_name: Optional[str] = Field(
        None,
        alias="ArtefactBucketName",
        description="S3 bucket name for storing deployment artifacts and build outputs",
    )
    ui_bucket_name: Optional[str] = Field(
        None,
        alias="UiBucketName",
        description="S3 bucket name for hosting the Core Automation web interface",
    )
    ui_bucket: Optional[str] = Field(
        None,
        alias="UiBucket",
        description="Alternative S3 bucket name for UI hosting (legacy field, deprecated)",
    )
    # Resource Naming
    scope: Optional[str] = Field(
        None,
        alias="Scope",
        description="Resource name prefix for all automation-created resources to ensure uniqueness",
    )

    @classmethod
    def model_class(cls, client: str) -> ClientFactsType:
        """Get the PynamoDB model class for this Pydantic model.

        Returns:
            ClientFactsType: Global ClientFactsModel class for database operations
        """
        return ClientFactsFactory.get_model(client)

    @classmethod
    def from_model(cls, model: ClientFactsModel) -> "ClientFact":
        """Convert a PynamoDB ClientFactsModel instance to a ClientFact Pydantic model.

        Args:
            client_model (ClientFactsModel): PynamoDB model instance to convert

        Returns:
            ClientFact: Pydantic model instance with data from the PynamoDB model
        """
        return cls(**model.to_simple_dict())

    def to_model(self, client: str) -> ClientFactsModel:
        """Convert to PynamoDB ClientFactsModel instance.

        Args:
            client (str): Client identifier for table isolation (used for factory)

        Returns:
            ClientFactsModel: PynamoDB ClientFactsModel instance ready for database operations

        """
        model_class = ClientFactsFactory.get_model(client)
        return model_class(**self.model_dump(include_secrets=True, by_alias=False, exclude_none=True))

    def get_resource_prefix(self) -> str:
        """Get the resource prefix for this client including scope.

        Returns:
            str: Resource prefix combining scope and client identifier for unique resource naming
        """
        scope = self.scope or ""
        return f"{scope}{self.client}"

    def get_bucket_name(self, bucket_type: str = "automation") -> str:
        """Get the appropriate bucket name for the specified type.

        Args:
            bucket_type (str): Type of bucket requested from available options

        Returns:
            str: Full bucket name for the specified type

        Raises:
            ValueError: If bucket_type is not one of the recognized types
        """
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
        """Check if this client uses a multi-account AWS setup.

        Returns:
            bool: True if multiple distinct AWS accounts are configured, False for single-account setup
        """
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

    def model_dump(self, **kwargs) -> dict:
        """Dump the model fields to a dictionary.

        Returns:
            dict: Dictionary representation of the model fields
        """
        if "include_secrets" in kwargs and not kwargs.pop("include_secrets", False):
            kwargs["exclude"] = {kwargs.get("exclude", set()) | {"client_secret"}}

        return super().model_dump(**kwargs)

    def __repr__(self) -> str:
        """Return a string representation of the ClientFact instance.

        Returns:
            str: String representation showing client identifier and name for debugging
        """
        return f"<ClientFact(client={self.client},name={self.client_name})>"
