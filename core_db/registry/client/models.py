"""Classes defining the Clients record model for the core-automation-clients table"""

from pynamodb.attributes import UnicodeAttribute

import core_logging as log

from ...constants import CLIENT_FACTS
from ...config import get_table_name
from ..models import RegistryModel


class ClientFacts(RegistryModel):
    """
    Model representing client organization configuration in the core-automation-clients table.

    This model stores comprehensive client organization information including AWS account details,
    regional configurations, bucket names, and automation settings. ClientFacts serves as the
    central registry for client organizations using the Core Automation platform.

    Attributes
    ----------
    Client : UnicodeAttribute
        Client ID or slug as the unique identifier for the client organization (hash key)
        Must be URL-safe and unique across all clients
        Example: "acme", "myorg", "example-corp"
    ClientName : UnicodeAttribute, optional
        Human-readable client organization name
        Example: "ACME Corporation", "My Organization"
    OrganizationId : UnicodeAttribute, optional
        AWS Organization ID for the client's AWS Organization
        Example: "o-t73gu32ai5", "o-example123456"
    OrganizationName : UnicodeAttribute, optional
        AWS Organization name as configured in AWS Organizations
        Example: "ACME Production Organization"
    OrganizationAccount : UnicodeAttribute, optional
        AWS account number for the organization root account (master account)
        Example: "123456789012"
    OrganizationEmail : UnicodeAttribute, optional
        Email address associated with the organization root account
        Example: "aws-admin@acme.com", "aws+root@myorg.com"
    Domain : UnicodeAttribute, optional
        Primary domain name for the organization
        Used for DNS configurations and resource naming
        Example: "acme.com", "myorg.example.com"
    IamAccount : UnicodeAttribute, optional
        AWS account number where centralized IAM roles and policies are stored
        Example: "123456789012"
    AuditAccount : UnicodeAttribute, optional
        AWS account number for centralized logging and audit trail storage
        Example: "987654321098"
    MasterRegion : UnicodeAttribute, optional
        Primary AWS region where Core Automation control plane is deployed
        Example: "us-west-2", "us-east-1"
    DocsBucketName : UnicodeAttribute, optional
        S3 bucket name for storing generated documentation and reports
        Example: "acme-core-automation-docs"
    ClientRegion : UnicodeAttribute, optional
        Default AWS region for client operations when region is not specified
        Example: "us-west-2", "eu-west-1"
    AutomationAccount : UnicodeAttribute, optional
        AWS account number where automation artifacts and resources are stored
        Example: "123456789012"
    BucketName : UnicodeAttribute, optional
        Primary S3 bucket for automation artifacts (packages, files, templates)
        Example: "acme-core-automation"
    BucketRegion : UnicodeAttribute, optional
        AWS region where the primary automation bucket is located
        Example: "us-west-2"
    ArtefactBucketName : UnicodeAttribute, optional
        S3 bucket name for storing deployment artifacts and build outputs
        Example: "acme-core-automation-artefacts"
    SecurityAccount : UnicodeAttribute, optional
        AWS account number for centralized security operations center (SOC)
        Example: "111111111111"
    NetworkAccount : UnicodeAttribute, optional
        AWS account number for centralized VPCs, DNS, and network services
        Example: "222222222222"
    UiBucketName : UnicodeAttribute, optional
        S3 bucket name for hosting the Core Automation web interface
        Example: "acme-core-automation-ui"
    Scope : UnicodeAttribute, optional
        Resource name prefix for all automation-created resources
        Must end with hyphen for proper concatenation
        Example: "dev-", "test-", "staging-"

        Note: This prefix is prepended to all resource names including:
        - S3 buckets: "{scope}acme-core-automation"
        - DynamoDB tables: "{scope}core-automation-clients"
        - Lambda functions: "{scope}core-automation-invoker"
        - IAM roles: "{scope}CoreAutomationExecutionRole"
    UiBucket : UnicodeAttribute, optional
        Alternative S3 bucket name for UI hosting (legacy field)
        Example: "core-automation-ui"
    UserInstantiated : UnicodeAttribute, optional
        Internal PynamoDB field indicating user instantiation

    Examples
    --------
    Creating a new client configuration:

    >>> client = ClientFacts(
    ...     "acme",
    ...     ClientName="ACME Corporation",
    ...     OrganizationId="o-example123456",
    ...     OrganizationAccount="123456789012",
    ...     Domain="acme.com",
    ...     MasterRegion="us-west-2",
    ...     Scope="prod-"
    ... )
    >>> client.save()

    Retrieving a client:

    >>> client = ClientFacts.get("acme")
    >>> print(f"Client: {client.ClientName}")
    >>> print(f"Domain: {client.Domain}")
    >>> print(f"Master Region: {client.MasterRegion}")

    Updating client configuration:

    >>> client = ClientFacts.get("acme")
    >>> client.SecurityAccount = "111111111111"
    >>> client.NetworkAccount = "222222222222"
    >>> client.save()

    Listing all clients:

    >>> for client in ClientFacts.scan():
    ...     print(f"{client.Client}: {client.ClientName}")

    Configuring multiple AWS accounts:

    >>> client = ClientFacts(
    ...     "enterprise",
    ...     ClientName="Enterprise Corp",
    ...     OrganizationAccount="123456789012",  # Root account
    ...     IamAccount="123456789012",           # IAM roles account
    ...     AuditAccount="987654321098",         # Logging account
    ...     SecurityAccount="111111111111",      # Security account
    ...     NetworkAccount="222222222222",       # Network account
    ...     AutomationAccount="333333333333",    # Automation account
    ...     MasterRegion="us-east-1",
    ...     BucketRegion="us-east-1"
    ... )
    >>> client.save()

    Managing resource naming with scope:

    >>> client = ClientFacts(
    ...     "dev-client",
    ...     ClientName="Development Environment",
    ...     Scope="dev-",
    ...     BucketName="dev-myclient-core-automation",
    ...     DocsBucketName="dev-myclient-core-automation-docs"
    ... )
    >>> client.save()

    Notes
    -----
    **Account Strategy**: Different AWS accounts can be configured for different purposes:

    - **OrganizationAccount**: Root account for AWS Organizations
    - **IamAccount**: Centralized IAM roles and policies
    - **AuditAccount**: CloudTrail, Config, and audit logs
    - **SecurityAccount**: Security monitoring and SOC tools
    - **NetworkAccount**: VPCs, DNS, and network infrastructure
    - **AutomationAccount**: Core Automation deployment and artifacts

    **Resource Naming**: The Scope field affects all resource naming:

    - Without scope: "core-automation-clients"
    - With scope "dev-": "dev-core-automation-clients"
    - Ensures environment isolation and easy identification

    **Regional Configuration**: Multiple region fields serve different purposes:

    - **MasterRegion**: Core Automation control plane location
    - **ClientRegion**: Default region for client operations
    - **BucketRegion**: Primary bucket location (may differ for compliance)

    **Single Table Design**: Unlike other registry models, ClientFacts uses a single
    global table without client-specific table names, as it stores the client registry
    itself and is accessed by the Core Automation platform infrastructure.

    See Also
    --------
    PortfolioFacts : Portfolio configuration per client
    ZoneFacts : Zone configuration per client
    AppFacts : Application configuration per client
    """

    class Meta(RegistryModel.Meta):
        pass

    # Primary key
    Client = UnicodeAttribute(hash_key=True)

    # Client identification
    ClientName = UnicodeAttribute(null=True)

    # AWS Organization configuration
    OrganizationId = UnicodeAttribute(null=True)
    OrganizationName = UnicodeAttribute(null=True)
    OrganizationAccount = UnicodeAttribute(null=True)
    OrganizationEmail = UnicodeAttribute(null=True)

    # Domain and networking
    Domain = UnicodeAttribute(null=True)

    # AWS Account assignments
    IamAccount = UnicodeAttribute(null=True)
    AuditAccount = UnicodeAttribute(null=True)
    AutomationAccount = UnicodeAttribute(null=True)
    SecurityAccount = UnicodeAttribute(null=True)
    NetworkAccount = UnicodeAttribute(null=True)

    # Regional configuration
    MasterRegion = UnicodeAttribute(null=True)
    ClientRegion = UnicodeAttribute(null=True)
    BucketRegion = UnicodeAttribute(null=True)

    # S3 bucket configuration
    BucketName = UnicodeAttribute(null=True)
    DocsBucketName = UnicodeAttribute(null=True)
    ArtefactBucketName = UnicodeAttribute(null=True)
    UiBucketName = UnicodeAttribute(null=True)
    UiBucket = UnicodeAttribute(null=True)  # Legacy field

    # Resource naming
    Scope = UnicodeAttribute(null=True)

    # Internal fields
    UserInstantiated = UnicodeAttribute(null=True)

    def __init__(self, *args, **kwargs):
        """
        Initialize ClientFacts instance with automatic key conversion.

        :param args: Positional arguments for model initialization
        :param kwargs: Keyword arguments with automatic snake_case/kebab-case conversion
        """
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        """
        Return string representation of ClientFacts.

        :returns: String representation showing Client identifier
        :rtype: str
        """
        return f"ClientFacts({self.Client})"

    def get_resource_prefix(self) -> str:
        """
        Get the resource prefix for this client including scope.

        :returns: Resource prefix combining scope and client identifier
        :rtype: str
        """
        scope = self.Scope or ""
        return f"{scope}{self.Client}"

    def get_bucket_name(self, bucket_type: str = "automation") -> str:
        """
        Get the appropriate bucket name for the specified type.

        :param bucket_type: Type of bucket ("automation", "docs", "artefacts", "ui")
        :type bucket_type: str
        :returns: Full bucket name with scope prefix
        :rtype: str
        :raises ValueError: If bucket_type is not recognized
        """
        bucket_mapping = {
            "automation": self.BucketName,
            "docs": self.DocsBucketName,
            "artefacts": self.ArtefactBucketName,
            "ui": self.UiBucketName or self.UiBucket,
        }

        if bucket_type not in bucket_mapping:
            raise ValueError(f"Unknown bucket type: {bucket_type}")

        return bucket_mapping[bucket_type]

    def is_multi_account(self) -> bool:
        """
        Check if this client uses a multi-account AWS setup.

        :returns: True if multiple distinct AWS accounts are configured
        :rtype: bool
        """
        accounts = {
            self.OrganizationAccount,
            self.IamAccount,
            self.AuditAccount,
            self.AutomationAccount,
            self.SecurityAccount,
            self.NetworkAccount,
        }
        # Remove None values and check if more than one unique account
        accounts.discard(None)
        return len(accounts) > 1


ClientFactsType = type[ClientFacts]


class ClientFactsFactory:

    _cache_models = {}

    @classmethod
    def get_model(cls, client: str = "global", auto_create_table: bool = False) -> ClientFactsType:
        """
        Get a ClientFacts model class for a specific client.

        :param client: Client identifier (slug)
        :type client: str
        :param auto_create_table: Whether to auto-create the table if it doesn't exist
        :type auto_create_table: bool
        :returns: A ClientFacts model class configured for the specified client
        :rtype: type[ClientFacts]
        """

        if not client in cls._cache_models:
            model_class = cls._create_client_model(client)
            cls._cache_models[client] = model_class

            # Auto-create table if requested
            if auto_create_table:
                cls._ensure_table_exists(model_class)

        return cls._cache_models[client]

    @classmethod
    def create_table(cls, client: str = None) -> None:
        """
        Create the ClientFacts table if it does not exist.

        :param cls: The ClientFacts model class to create the table for
        :type cls: type[ClientFacts]
        :param wait: Whether to wait until the table is created
        :type wait: bool
        """
        if not client:
            client = "global"
        model = cls.get_model(client, True)

    @classmethod
    def _ensure_table_exists(cls, model_class: ClientFactsType) -> None:
        """
        Ensure the table exists, create it if it doesn't.

        :param model_class: The ClientFacts model class to check/create
        :type model_class: type[ClientFacts]
        """
        try:
            if not model_class.exists():
                log.info("Creating client facts table: %s", model_class.Meta.table_name)
                model_class.create_table(wait=True)
                log.info(
                    "Successfully created client facts table: %s",
                    model_class.Meta.table_name,
                )
        except Exception as e:
            log.error(
                "Failed to create client facts table %s: %s",
                model_class.Meta.table_name,
                str(e),
            )

    @classmethod
    def _create_client_model(cls, client: str) -> ClientFactsType:
        """
        Create a new ClientFacts model class for a specific client.

        :param client: Client identifier (slug)
        :type client: str
        :returns: A new ClientFacts model class configured for the specified client
        :rtype: type[ClientFacts]
        """

        class ClientFactsModel(ClientFacts):
            class Meta(ClientFacts.Meta):
                table_name = get_table_name(CLIENT_FACTS)

        return ClientFactsModel
