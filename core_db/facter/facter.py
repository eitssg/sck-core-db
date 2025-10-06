"""Comprehensive fact aggregation for deployment contexts.

This module retrieves and merges configuration "facts" from multiple registry
domains (client, portfolio, application, zone, region, account) stored in
DynamoDB and synthesizes them into a single dictionary consumed by Jinja2
template rendering and deployment orchestration.

Key Responsibilities:
        * Provide strongly structured fact dictionaries (PascalCase keys) that feed
            the compilation pipeline (see ``core_component.handler`` / preprocessor).
        * Derive environment & region alias fallbacks from branch naming
            conventions when not explicitly defined in app facts.
        * Generate storage / artefact path facts used for build output upload.
        * Normalize and merge resource tags from all hierarchy levels (client →
            zone → region → portfolio → app) with runtime overrides (environment,
            region alias, owner, contacts).

Data Sources:
        * ClientFact, PortfolioFact, AppFact, ZoneFact models (PynamoDB backed).
        * DeploymentDetails (runtime invocation context).
        * Derived environment & region alias (branch parsing heuristics).

Error Handling Strategy:
        * Retrieval helpers return ``None`` (or minimal UNREGISTERED stubs for
            internal helpers) when facts are absent; public ``get_facts`` escalates
            to ``ValueError`` only for strictly required domains when composing the
            final dictionary.
        * PynamoDB errors are logged with context and converted to safe fallbacks.

Extension Points:
        * Additional hierarchical sources (e.g., TeamFact) can be merged by
            extending ``get_facts`` before the final deep merge phase.
        * Custom tag injection can be performed by altering the ChainMap ordering
            or adding post‑merge transformations.

All public and internal helpers below use Google/Napoleon docstrings for Sphinx
generation and IDE assistance.
"""

from collections import ChainMap
import os
import re
import core_framework as util
import core_logging as log

from core_framework.constants import (
    FACTS_REGION,
    FACTS_TAGS,
    FACTS_ACCOUNT,
    TAG_ENVIRONMENT,
    TAG_OWNER,
    TAG_REGION,
    TAG_CONTACTS,
    V_DEFAULT_ENVIRONMENT,
    V_DEFAULT_REGION_ALIAS,
    V_EMPTY,
    SCOPE_BUILD,
    SCOPE_APP,
    SCOPE_BRANCH,
    SCOPE_PORTFOLIO,
)

from core_framework.models import DeploymentDetails
from pynamodb.exceptions import GetError, QueryError, ScanError, DoesNotExist

from ..constants import REGION, ENVIRONMENT, ZONE_KEY

from ..registry.client.models import ClientFact
from ..registry.portfolio.models import PortfolioFact
from ..registry.zone.models import ZoneFact
from ..registry.app.models import AppFact


def get_client_facts(client: str) -> dict | None:
    """Retrieve client configuration facts from the DynamoDB registry.

    Fetches comprehensive client details including organization configuration,
    AWS account mappings, regional settings, and S3 bucket configurations.

    Args:
        client (str): The client identifier (slug) to retrieve from the database.
            Must be a non-empty string representing a registered client.

    Returns:
        dict | None: The client facts dictionary containing:
            - ClientId: str - Unique client identifier
            - ClientName: str - Display name of the client
            - OrganizationId: str - AWS Organization ID
            - OrganizationAccount: str - Root AWS account ID
            - Domain: str - Primary domain name
            - IamAccount: str - IAM management account ID
            - AuditAccount: str - Security audit account ID
            - MasterRegion: str - Primary control plane region
            - BucketName: str - Artifacts storage bucket
            - Scope: str - Resource naming prefix
            - Tags: dict - Default client-level resource tags

            Returns None if the client is not found in the registry.

    Raises:
        ValueError: If client parameter is empty, None, or not a string.

    Examples:
        >>> # Retrieve client facts for ACME Corporation
        >>> client_facts = get_client_facts("ACME001")
        >>> if client_facts:
        ...     print(f"Client: {client_facts['ClientName']}")  # "ACME Corporation"
        ...     print(f"Domain: {client_facts['Domain']}")      # "acme.com"
        ...     print(f"Org ID: {client_facts['OrganizationId']}")  # "o-acme123456789"
        ...     print(f"Master Region: {client_facts['MasterRegion']}")  # "us-east-1"

        >>> # Handle missing client gracefully
        >>> facts = get_client_facts("nonexistent")
        >>> print(facts)  # None

        >>> # Access nested configurations
        >>> if client_facts:
        ...     tags = client_facts.get('Tags', {})
        ...     print(f"Environment: {tags.get('Environment')}")  # "production"
        ...     bucket = client_facts.get('BucketName')
        ...     print(f"Artifacts Bucket: {bucket}")  # "acme-automation-artifacts"
    """
    if not client:
        raise ValueError("Client must be a valid string")

    try:
        model_class = ClientFact.model_class()

        item = model_class.get(client)

        return ClientFact.from_model(item).model_dump(by_alias=True)

    except GetError:
        log.error(f"Client not found: {client}")
        return None
    except Exception as e:
        log.error(f"Error getting client facts: {str(e)}")
        return None


def get_portfolio_facts(client: str, portfolio: str) -> dict | None:
    """Retrieve portfolio configuration facts from the DynamoDB registry.

    Fetches comprehensive portfolio details including project metadata, business application
    information, ownership details, contact lists, approval workflows, and resource tags.

    Args:
        client (str): The client identifier (slug). Must be a registered client name.
        portfolio (str): The portfolio identifier (slug). Must be a registered portfolio
            within the specified client.

    Returns:
        dict | None: The portfolio facts dictionary containing:
            - Portfolio: str - Portfolio identifier
            - Domain: str - Portfolio-specific domain (e.g., "platform.acme.com")
            - Project: dict - Software project details (name, code, repository, attributes)
            - Bizapp: dict - Business application metadata (criticality, compliance, RTO/RPO)
            - Owner: dict - Portfolio owner contact information and attributes
            - Contacts: list[dict] - Team contact list with roles and escalation levels
            - Approvers: list[dict] - Approval workflow with sequence and dependencies
            - Tags: dict - Portfolio-level resource tags
            - Metadata: dict - Technical configuration (deployment model, monitoring, etc.)
            - Attributes: dict - Software attributes (version, licensing, SLAs, compliance)

            Returns None if the portfolio is not found in the registry.

    Raises:
        ValueError: If client or portfolio parameters are empty, None, or not strings.

    Examples:
        >>> # Retrieve portfolio facts for enterprise platform
        >>> portfolio_facts = get_portfolio_facts("ACME001", "acme-enterprise-platform")
        >>> if portfolio_facts:
        ...     # Access project information
        ...     project = portfolio_facts['Project']
        ...     print(f"Project: {project['Name']}")  # "ACME Enterprise Platform"
        ...     print(f"Repository: {project['Repository']}")  # "https://github.com/acme/..."
        ...
        ...     # Access ownership and contacts
        ...     owner = portfolio_facts['Owner']
        ...     print(f"Owner: {owner['Name']} <{owner['Email']}>")  # "Sarah Johnson <sarah@acme.com>"
        ...
        ...     contacts = portfolio_facts['Contacts']
        ...     print(f"Team Size: {len(contacts)} contacts")  # 4 contacts
        ...
        ...     # Access approval workflow
        ...     approvers = portfolio_facts['Approvers']
        ...     for approver in approvers:
        ...         print(f"Sequence {approver['Sequence']}: {approver['Name']}")

        >>> # Handle missing portfolio
        >>> facts = get_portfolio_facts("ACME001", "nonexistent")
        >>> print(facts)  # None

        >>> # Access business application details
        >>> if portfolio_facts:
        ...     bizapp = portfolio_facts.get('Bizapp', {})
        ...     print(f"Criticality: {bizapp.get('Attributes', {}).get('Criticality')}")  # "high"
        ...     print(f"RTO: {bizapp.get('Attributes', {}).get('Rto')}")  # "4_hours"
    """
    if not client or not portfolio:
        raise ValueError("Client and portfolio must be valid strings")

    try:
        model_class = PortfolioFact.model_class(client)

        item = model_class.get(portfolio)

        return PortfolioFact.from_model(item).model_dump(by_alias=True)

    except DoesNotExist:
        log.error(f"Portfolio not found: {client} / {portfolio}")
        return None
    except GetError:
        log.error(f"Portfolio not found: {client} / {portfolio}")
        return None

    except Exception as e:
        log.error(f"Error getting portfolio facts: {e}")
        return None


def get_zone_facts(client: str, zone: str) -> dict | None:
    """Retrieve deployment zone configuration facts from the DynamoDB registry.

    Fetches comprehensive zone details including AWS account configuration, regional
    settings, networking topology, security configurations, and infrastructure aliases.

    Args:
        client (str): The client identifier (slug). Must be a registered client name.
        zone (str): The zone identifier (slug). Must be a registered deployment zone
            within the specified client (e.g., "prod-east-primary", "dev-west-secondary").

    Returns:
        dict | None: The zone facts dictionary containing:
            - Zone: str - Zone identifier
            - AccountFacts: dict - AWS account configuration and KMS settings
            - RegionFacts: dict - Multi-region configuration with image and security aliases
            - Tags: dict - Zone-level resource tags for governance and compliance
            - Environment-specific configurations per region including:
              - AwsRegion: str - AWS region identifier
              - AzCount: int - Number of availability zones
              - ImageAliases: dict - AMI mappings by operating system
              - SecurityAliases: dict - CIDR blocks for network access control
              - SecurityGroupAliases: dict - Security group identifier mappings
              - Proxy settings and DNS configurations

            Returns None if the zone is not found in the registry.

    Raises:
        ValueError: If client or zone parameters are empty, None, or not strings.

    Examples:
        >>> # Retrieve production zone facts
        >>> zone_facts = get_zone_facts("ACME001", "prod-east-primary")
        >>> if zone_facts:
        ...     # Access account configuration
        ...     account = zone_facts['AccountFacts']
        ...     print(f"Account ID: {account['AwsAccountId']}")  # "123456789012"
        ...     print(f"Environment: {account['Environment']}")  # "production"
        ...
        ...     # Access regional configuration
        ...     regions = zone_facts['RegionFacts']
        ...     us_east = regions['us-east-1']
        ...     print(f"AZ Count: {us_east['AzCount']}")  # 3
        ...
        ...     # Access infrastructure aliases
        ...     images = us_east['ImageAliases']
        ...     print(f"Ubuntu 22: {images['Ubuntu22']}")  # "ami-0c02fb55956c7d316"
        ...
        ...     # Access security configuration
        ...     security = us_east['SecurityAliases']
        ...     corp_cidrs = security['CorporateCidrs']
        ...     for cidr in corp_cidrs:
        ...         print(f"CIDR: {cidr['Value']} - {cidr['Description']}")

        >>> # Handle missing zone
        >>> facts = get_zone_facts("ACME001", "nonexistent")
        >>> print(facts)  # None

        >>> # Access KMS configuration
        >>> if zone_facts:
        ...     kms = zone_facts['AccountFacts']['Kms']
        ...     print(f"KMS Key: {kms['KmsKeyArn']}")
        ...     print(f"Delegate Accounts: {kms['DelegateAwsAccountIds']}")
    """

    if not client or not zone:
        raise ValueError("Client and zone must be valid strings")

    try:
        model_class = ZoneFact.model_class(client)

        item = model_class.get(zone)

        return ZoneFact.from_model(item).model_dump(by_alias=True)

    except GetError:
        log.error(f"Zone not found: {client} / {zone}")
        return None
    except Exception as e:
        log.error(f"Error getting zone facts: {e}")
        return None


def get_zone_facts_by_account_id(client: str, account_id: str) -> list[dict] | None:
    """Retrieve all deployment zones associated with a specific AWS account ID.

    Scans the zone registry to find all zones that are configured to deploy into
    the specified AWS account. This is useful for account-wide operations and
    cross-zone queries.

    Args:
        client (str): The client identifier (slug). Must be a registered client name.
        account_id (str): The AWS account ID to search for (12-digit string).
            Must match the account_facts.aws_account_id field in zone configurations.

    Returns:
        list[dict] | None: List of zone facts dictionaries that deploy to the specified
            AWS account. Each dictionary contains the same structure as get_zone_facts().
            Returns None if no zones are found for the account ID.

    Raises:
        ValueError: If client or account_id parameters are empty, None, or not strings.

    Examples:
        >>> # Find all zones deploying to production account
        >>> zone_facts_list = get_zone_facts_by_account_id("ACME001", "123456789012")
        >>> if zone_facts_list:
        ...     print(f"Found {len(zone_facts_list)} zones in account 123456789012")
        ...     for zone in zone_facts_list:
        ...         print(f"Zone: {zone['Zone']}")  # "prod-east-primary", "prod-west-secondary"
        ...         print(f"Environment: {zone['AccountFacts']['Environment']}")

        >>> # Handle account with no zones
        >>> facts = get_zone_facts_by_account_id("ACME001", "999999999999")
        >>> print(facts)  # None

        >>> # Cross-zone analysis
        >>> if zone_facts_list:
        ...     primary_zones = [z for z in zone_facts_list if 'primary' in z['Zone']]
        ...     dr_zones = [z for z in zone_facts_list if 'secondary' in z['Zone']]
        ...     print(f"Primary zones: {len(primary_zones)}, DR zones: {len(dr_zones)}")
    """
    if not client or not account_id:
        raise ValueError("Client and account_id must be valid strings")

    try:
        model_class = ZoneFact.model_class(client)

        result = model_class.scan()

        data = []
        for item in result:
            if isinstance(item, ZoneFact) and item.account_facts.aws_account_id == account_id:
                data.append(ZoneFact.from_model(item).model_dump(by_alias=True))

        if not data:
            log.warning(f"No zones found for account ID: {account_id} in client: {client}")
            return None

        return data

    except ScanError as e:
        log.error(f"Zone facts scan error: {e}")
        return None

    except Exception as e:
        log.error(f"Error getting zone facts by account ID: {e}")
        return None


def get_app_facts(deployment_details: DeploymentDetails) -> list[dict] | None:
    """Retrieve application configuration facts matching deployment context.

    Searches the app registry for applications that match the deployment details
    using regex pattern matching against the PRN (Portfolio Resource Name) identity.
    Returns application-specific configuration including image aliases, deployment
    metadata, and operational parameters.

    Args:
        deployment_details (DeploymentDetails): The deployment context containing:
            - client: str - Client identifier (required)
            - portfolio: str - Portfolio identifier (required)
            - app: str - Application name (required)
            - branch: str - Git branch name (optional)
            - build: str - Build version (optional)

    Returns:
        list[dict] | None: List of matching application facts dictionaries containing:
            - Portfolio: str - Portfolio identifier
            - AppRegex: str - PRN pattern for matching deployments
            - Name: str - Application display name
            - Environment: str - Target deployment environment
            - Account: str - AWS account ID for deployment
            - Zone: str - Target deployment zone
            - Region: str - Primary AWS region
            - Repository: str - Source code repository URL
            - ImageAliases: dict - Container/AMI mappings by component
            - Tags: dict - Application-level resource tags
            - Metadata: dict - Deployment configuration (scaling, networking, security)

            Returns None if no matching applications are found.

    Raises:
        ValueError: If required fields (client, portfolio, app) are missing from
            deployment_details.

    Examples:
        >>> # Create deployment context
        >>> dd = DeploymentDetails(
        ...     client="ACME001",
        ...     portfolio="acme-enterprise-platform",
        ...     app="acme-platform-core",
        ...     branch="main",
        ...     build="1.2.0"
        ... )
        >>>
        >>> # Retrieve matching app facts
        >>> app_facts = get_app_facts(dd)
        >>> if app_facts:
        ...     app = app_facts[0]  # First matching app
        ...     print(f"App: {app['Name']}")  # "ACME Enterprise Platform Core"
        ...     print(f"Zone: {app['Zone']}")  # "prod-east-primary"
        ...     print(f"Repository: {app['Repository']}")  # "https://github.com/acme/..."
        ...
        ...     # Access image aliases
        ...     images = app['ImageAliases']
        ...     print(f"API Gateway: {images['ApiGateway']}")  # "ami-0c02fb55956c7d316"
        ...
        ...     # Access deployment metadata
        ...     metadata = app['Metadata']
        ...     print(f"Strategy: {metadata['DeploymentStrategy']}")  # "blue_green"
        ...     print(f"Min Capacity: {metadata['MinCapacity']}")  # "3"

        >>> # Handle missing app facts
        >>> dd_invalid = DeploymentDetails(
        ...     client="ACME001",
        ...     portfolio="invalid",
        ...     app="nonexistent"
        ... )
        >>> facts = get_app_facts(dd_invalid)
        >>> print(facts)  # None

        >>> # Error handling for incomplete deployment details
        >>> try:
        ...     dd_incomplete = DeploymentDetails(client="ACME001")  # Missing portfolio/app
        ...     get_app_facts(dd_incomplete)
        ... except ValueError as e:
        ...     print(f"Error: {e}")  # "Portfolio must be valid in DeploymentDetails"
    """
    client = deployment_details.client
    if not client:
        raise ValueError("Client must be valid in DeploymentDetails")

    portfolio = deployment_details.portfolio
    if not portfolio:
        raise ValueError("Portfolio must be valid in DeploymentDetails")

    app = deployment_details.app
    if not app:
        raise ValueError("App field must be populated in DeploymentDetails")

    identity = deployment_details.get_identity()

    model_class = AppFact.model_class(client)

    try:

        app_facts_list = model_class.query(portfolio, scan_index_forward=True)

        data = []
        for app_facts in app_facts_list:
            if isinstance(app_facts, model_class) and app_facts.app_regex and re.match(app_facts.app_regex, identity):
                data.append(AppFact.from_model(app_facts).model_dump(by_alias=True))

        if not data:
            log.warning(f"No app facts found for client: {client}, portfolio: {portfolio}, app: {app}")
            return []

        return data

    except QueryError as e:
        log.error(f"App facts query error: {e}")
        return None

    except Exception as e:
        log.error(f"Error getting app facts: {e}")
        return None


def derive_environment_from_branch(branch: str) -> tuple[str, str]:
    """Derive deployment environment and region from Git branch naming conventions.

    Parses Git branch names to extract environment and region information using
    standard naming patterns. Supports feature branches, environment branches,
    and region-specific deployments.

    Branch Naming Patterns:
        - "environment-region" → (environment, region)
        - "feature/path/environment-region" → (environment, region)
        - "master" or "main" → (production, default_region)
        - "environment" → (environment, default_region)

    Args:
        branch (str): The Git repository branch name. Can include forward slashes
            for feature branch paths and dashes for environment-region separation.

    Returns:
        tuple[str, str]: A tuple containing:
            - environment (str): The target deployment environment
            - region_alias (str): The target region alias

    Examples:
        >>> # Standard environment-region format
        >>> env, region = derive_environment_from_branch("dev-sin")
        >>> print((env, region))  # ("dev", "sin")

        >>> # Feature branch with environment-region
        >>> env, region = derive_environment_from_branch("feature1/dev-sin")
        >>> print((env, region))  # ("dev", "sin")

        >>> # Complex nested feature branch
        >>> env, region = derive_environment_from_branch("feature/new-auth/staging-usw2")
        >>> print((env, region))  # ("staging", "usw2")

        >>> # Master branch defaults to production
        >>> env, region = derive_environment_from_branch("master")
        >>> print((env, region))  # ("production", "use1")  # uses V_DEFAULT_ENVIRONMENT

        >>> # Main branch defaults to production
        >>> env, region = derive_environment_from_branch("main")
        >>> print((env, region))  # ("production", "use1")  # uses V_DEFAULT_ENVIRONMENT

        >>> # Environment only (no region specified)
        >>> env, region = derive_environment_from_branch("development")
        >>> print((env, region))  # ("development", "use1")  # uses V_DEFAULT_REGION_ALIAS

        >>> # Feature branch without region
        >>> env, region = derive_environment_from_branch("feature/auth/development")
        >>> print((env, region))  # ("development", "use1")  # uses V_DEFAULT_REGION_ALIAS
    """
    parts = branch.split("-")

    if len(parts) >= 2:
        branch = parts[0]

        # split the branch by '/' and retrieve the last part
        branch_parts = branch.split("/")
        environment = branch_parts[-1]  # in this format, the branch name is the environment (master, main, dev, feature1/dev, etc)
        region_alias = parts[1]  # override region_alias fact with the branch region alias definition
    else:
        environment = branch
        region_alias = V_DEFAULT_REGION_ALIAS

    # If you are deploying a master branch, you are definitely PRODUCTION
    if environment == "master" or environment == "main":
        environment = V_DEFAULT_ENVIRONMENT

    return environment, region_alias


def format_contact(contact: dict) -> str:
    """Format contact dictionary into a standardized string representation.

    Converts contact information dictionaries into consistent string formats
    suitable for template rendering, resource tagging, and notification systems.

    Args:
        contact (dict): Contact information dictionary that may contain:
            - Name (str, optional): Contact's full name
            - Email (str, optional): Contact's email address
            - Additional fields are ignored for formatting

    Returns:
        str: Formatted contact string using these rules:
            - Both name and email: "Name <email@domain.com>"
            - Email only: "email@domain.com"
            - Name only: "Name"
            - Neither: "" (empty string)

    Examples:
        >>> # Complete contact information
        >>> contact = {"Name": "John Doe", "Email": "john@example.com"}
        >>> formatted = format_contact(contact)
        >>> print(formatted)  # "John Doe <john@example.com>"

        >>> # Email only
        >>> contact = {"Email": "john@example.com"}
        >>> formatted = format_contact(contact)
        >>> print(formatted)  # "john@example.com"

        >>> # Name only
        >>> contact = {"Name": "John Doe"}
        >>> formatted = format_contact(contact)
        >>> print(formatted)  # "John Doe"

        >>> # Empty contact
        >>> contact = {}
        >>> formatted = format_contact(contact)
        >>> print(formatted)  # ""

        >>> # Real-world usage in template context
        >>> portfolio_facts = {
        ...     "Owner": {"Name": "Jane Smith", "Email": "jane@acme.com"},
        ...     "Contacts": [
        ...         {"Name": "Tech Lead", "Email": "tech@acme.com"},
        ...         {"Name": "DevOps", "Email": "devops@acme.com"}
        ...     ]
        ... }
        >>> owner_formatted = format_contact(portfolio_facts["Owner"])
        >>> print(owner_formatted)  # "Jane Smith <jane@acme.com>"
        >>>
        >>> contacts_formatted = [format_contact(c) for c in portfolio_facts["Contacts"]]
        >>> print(",".join(contacts_formatted))  # "Tech Lead <tech@acme.com>,DevOps <devops@acme.com>"
    """
    name = contact.get("Name", "")
    email = contact.get("Email", "")
    if not name and not email:
        return V_EMPTY
    if not name:
        return email
    if not email:
        return name
    return f"{name} <{email}>"


def get_store_url(bucket_name: str, bucket_region: str) -> str:
    """Return a canonical bucket storage URL for the current execution mode.

    In S3 mode (``util.is_use_s3()`` true) this returns an ``s3://`` style
    URL; in local mode it returns a filesystem path rooted at the configured
    storage volume. No network calls are performed; the value is a purely
    derived convenience string used in facts and logging.

    Args:
        bucket_name (str): Logical artefact bucket name.
        bucket_region (str): AWS region (forwarded to ``util.get_storage_volume`` for
            potential region-specific local volume selection).

    Returns:
        str: ``s3://{bucket_name}`` in S3 mode or ``<volume>/<bucket_name>`` in local mode.

    Example:
        >>> get_store_url("acme-artifacts", "us-east-1")  # doctest: +ELLIPSIS
        's3://acme-artifacts'

    Contract:
        * Always returns a string (never ``None``).
        * Does not verify bucket existence.
        * Path separator normalized based on storage backend.
    """
    store = util.get_storage_volume(bucket_region)
    sep = "/" if util.is_use_s3() else os.path.sep
    return sep.join([store, bucket_name])


def get_compiler_facts(dd: DeploymentDetails) -> dict:
    """Generate compiler-specific facts for artifact storage and file management.

    Creates a comprehensive dictionary of storage paths, bucket configurations,
    and file prefixes used by the template compiler for artifact management,
    deployment tracking, and resource organization.

    Args:
        dd (DeploymentDetails): The deployment context containing client, portfolio,
            app, branch, and build information used to construct storage paths.

    Returns:
        dict: Compiler facts dictionary containing storage configuration:

            Artifact Storage (British spelling):
            - ArtefactsBucketName: str - Artifact storage bucket name
            - ArtefactsBucketRegion: str - Bucket AWS region
            - ArtefactsBucketUrl: str - Complete bucket URL
            - ArtefactsPrefix: str - Base artifact path prefix
            - ArtefactKeyBuildPrefix: str - Build-specific artifact prefix

            Artifact Storage (American spelling):
            - ArtifactBucketName: str - Same as ArtefactsBucketName
            - ArtifactBucketRegion: str - Same as ArtefactsBucketRegion
            - ArtifactBaseUrl: str - Same as ArtefactsBucketUrl
            - ArtifactKeyPrefix: str - Same as ArtefactsPrefix
            - ArtifactKeyBuildPrefix: str - Same as ArtefactKeyBuildPrefix

            File Storage Hierarchy:
            - FilesBucketName: str - Files storage bucket
            - FilesBucketRegion: str - Files bucket region
            - FilesBucketUrl: str - Files bucket URL
            - PortfolioFilesPrefix: str - Portfolio-level files path
            - AppFilesPrefix: str - Application-level files path
            - BranchFilesPrefix: str - Branch-level files path
            - BuildFilesPrefix: str - Build-specific files path
            - SharedFilesPrefix: str - Shared/common files path

            Artifact Key Hierarchy:
            - ArtifactKeyPortfolioPrefix: str - Portfolio-level artifacts
            - ArtifactKeyAppPrefix: str - Application-level artifacts
            - ArtifactKeyBranchPrefix: str - Branch-level artifacts

    Examples:
        >>> # Create deployment context
        >>> dd = DeploymentDetails(
        ...     client="ACME001",
        ...     portfolio="core",
        ...     app="api",
        ...     branch="main",
        ...     build="123"
        ... )
        >>>
        >>> # Generate compiler facts
        >>> facts = get_compiler_facts(dd)
        >>>
        >>> # Access bucket configuration
        >>> print(facts['ArtefactsBucketName'])  # "acme001-artifacts"
        >>> print(facts['ArtefactsBucketRegion'])  # "us-east-1"
        >>> print(facts['ArtefactsBucketUrl'])  # "s3://acme001-artifacts"
        >>>
        >>> # Access artifact paths
        >>> print(facts['ArtifactKeyPrefix'])    # "artifacts/acme001/core/api/main/123"
        >>> print(facts['BuildFilesPrefix'])    # "files/acme001/core/api/main/123"
        >>>
        >>> # Access hierarchical prefixes
        >>> print(facts['PortfolioFilesPrefix'])  # "files/acme001/core"
        >>> print(facts['AppFilesPrefix'])       # "files/acme001/core/api"
        >>> print(facts['BranchFilesPrefix'])    # "files/acme001/core/api/main"
        >>>
        >>> # Both spelling variants available
        >>> assert facts['ArtefactsBucketName'] == facts['ArtifactBucketName']
        >>> assert facts['ArtefactsPrefix'] == facts['ArtifactKeyPrefix']
        >>>
        >>> # Shared files for common resources
        >>> print(facts['SharedFilesPrefix'])    # "files/shared"
    """
    # Shared Files path separator
    sep = "/" if util.is_use_s3() else os.path.sep

    client = dd.client

    artefacts_bucket_name = util.get_artefact_bucket_name(client)
    artefacts_bucket_region = util.get_artefact_bucket_region()

    s3_bucket_url = get_store_url(artefacts_bucket_name, artefacts_bucket_region)

    # Construct the compilation context
    compiler_facts = {
        # Artefacts
        "ArtefactsBucketName": artefacts_bucket_name,
        "ArtefactsBucketRegion": artefacts_bucket_region,
        "ArtefactsBucketUrl": s3_bucket_url,
        "ArtefactsPrefix": dd.get_artefacts_key(),
        "ArtefactKeyBuildPrefix": dd.get_artefacts_key(scope=SCOPE_BUILD),
        # Artifacts (spelling)
        "ArtifactBucketName": artefacts_bucket_name,
        "ArtifactBucketRegion": artefacts_bucket_region,
        "ArtifactBaseUrl": s3_bucket_url,
        "ArtifactKeyPrefix": dd.get_artefacts_key(),
        "ArtifactKeyBuildPrefix": dd.get_artefacts_key(scope=SCOPE_BUILD),
        # Files
        "FilesBucketName": artefacts_bucket_name,
        "FilesBucketRegion": artefacts_bucket_region,
        "FilesBucketUrl": s3_bucket_url,
        # Files Prefix
        "PortfolioFilesPrefix": dd.get_files_key(scope=SCOPE_PORTFOLIO),
        "AppFilesPrefix": dd.get_files_key(scope=SCOPE_APP),
        "BranchFilesPrefix": dd.get_files_key(scope=SCOPE_BRANCH),
        "BuildFilesPrefix": dd.get_files_key(scope=SCOPE_BUILD),
        # ArtifactKey
        "ArtifactKeyPortfolioPrefix": dd.get_artefacts_key(scope=SCOPE_PORTFOLIO),
        "ArtifactKeyAppPrefix": dd.get_artefacts_key(scope=SCOPE_APP),
        "ArtifactKeyBranchPrefix": dd.get_artefacts_key(scope=SCOPE_BRANCH),
        # Shared Files
        "SharedFilesPrefix": f"files{sep}shared",
    }

    return compiler_facts


def get_facts(deployment_details: DeploymentDetails) -> dict:  # noqa: C901
    """Assemble a merged deployment fact map for template rendering & orchestration.

    High-level process:
        1. Retrieve hierarchical registry facts (client → portfolio → app → zone → region → account)
        2. Derive environment / region alias from branch if not specified in app facts
        3. Build compiler (artefact & files) storage facts
        4. Merge dictionaries in precedence order (account/region < portfolio < app < deployment < compiler)
        5. Inject normalized & aggregated resource tags (top‑down override + runtime owner/contact enrichment)

    Merge Order (later overrides earlier):
        account_facts, region_facts → portfolio_facts → app_facts → deployment_details → compiler_facts

    Args:
        deployment_details (DeploymentDetails): Deployment context. Required fields vary by scope but
            full (client, portfolio, app) identity is needed for application/zone resolution.

    Returns:
        dict: PascalCase key fact mapping including (non-exhaustive categories):
            Identity: Client, Portfolio, App, Branch, Build, Environment, Region, Zone
            Infrastructure: AwsAccountId, AwsRegion, ResourceNamespace, OrganizationalUnit
            Networking/Security: VpcAliases, SubnetAliases, SecurityAliases, SecurityGroupAliases, ProxyHost, NameServers
            Artefacts & Files: ArtifactKeyPrefix, ArtifactKeyBuildPrefix, BuildFilesPrefix, SharedFilesPrefix, FilesBucketName
            Application: Repository, ImageAliases, Metadata, Kms
            Organizational: Owner, Contacts, Approvers, Tags

    Raises:
        ValueError: If mandatory upstream facts are missing or ambiguous (e.g. multiple app facts).

    Notes:
        * All returned values are merged shallow/deep with list merging enabled.
        * Tag precedence: client < zone < region < portfolio < app < runtime injections.
        * The return value is always a dict (never ``None``); missing domains contribute UNREGISTERED stubs.

    Example:
        >>> dd = DeploymentDetails(client="acme", portfolio="core", app="api", branch="main", build="1")
        >>> facts = get_facts(dd)
        >>> sorted(set(["Client", "App"]).issubset(facts.keys()))
        True

    Contract:
        * Output is side‑effect free except for logging.
        * No network calls after individual registry fetches complete.
        * Keys are stable PascalCase; additions are backwards compatible.
    """
    client_facts = _get_client_facts(deployment_details)

    scope = deployment_details.scope

    if scope in [SCOPE_PORTFOLIO, SCOPE_APP, SCOPE_BRANCH, SCOPE_BUILD]:
        portfolio_facts = _get_portfolio_facts(deployment_details)
    else:
        portfolio_facts = {}

    if scope in [SCOPE_APP, SCOPE_BRANCH, SCOPE_BUILD]:
        app_facts = _get_app_facts(deployment_details)
        zone_facts = _get_zone_facts(deployment_details, app_facts)
        region_facts = _get_region_facts(deployment_details, app_facts, zone_facts)
        account_facts = _get_account_facts(deployment_details, zone_facts)

        # if environment is not set, try to derive it from the branch. But facts ALWAYS come first.
        environment = app_facts.get(ENVIRONMENT, None)
        if not environment:
            environment, branch_region_alias = derive_environment_from_branch(deployment_details.branch or "us-east-1")

        # FACTS always override user input. So, don't use the user input if FACTS are present.
        region_alias = app_facts.get(REGION, None)
        if region_alias is None:
            region_alias = branch_region_alias

    else:
        app_facts = {}
        zone_facts = {}
        region_facts = {}
        account_facts = {}
        environment = deployment_details.environment
        region_alias = app_facts.get(REGION, None)

    compiler_facts = get_compiler_facts(deployment_details)

    log.debug("Compiler facts:", details=compiler_facts)

    owner = format_contact(portfolio_facts.get("Owner", {}))

    contacts = ",".join([format_contact(c) for c in portfolio_facts.get("Contacts", [])])

    # Now that we have ALL the facts, let's gather all the Tags for this deployment starting top down
    # Client -> Zone -> Region -> Portfolio -> App
    tags = ChainMap(
        client_facts.get(FACTS_TAGS, {}),
        zone_facts.get(FACTS_TAGS, {}),
        region_facts.get(FACTS_TAGS, {}),
        portfolio_facts.get(FACTS_TAGS, {}),
        app_facts.get(FACTS_TAGS, {}),
    )
    if environment:
        tags[TAG_ENVIRONMENT] = environment
    if region_alias:
        tags[TAG_REGION] = region_alias
    if owner:
        tags[TAG_OWNER] = owner
    if contacts:
        tags[TAG_CONTACTS] = contacts

    app_facts[FACTS_TAGS] = dict(tags)

    deployment_facts = deployment_details.model_dump()

    # Merge account facts and region-specific facts into the facts
    facts = util.merge.deep_merge(account_facts, region_facts, merge_lists=True)

    # Get all the zone details next
    facts = util.merge.deep_merge_in_place(facts, zone_facts, merge_lists=True)

    # Next, merge the portfolio facts into the facts
    facts = util.merge.deep_merge_in_place(facts, portfolio_facts, merge_lists=True)

    # Next, merge the app facts into the facts
    facts = util.merge.deep_merge_in_place(facts, app_facts, merge_lists=True)

    # Finally, we merge in the deployment details facts
    facts = util.merge.deep_merge_in_place(facts, deployment_facts, merge_lists=True)

    # Next, we merge in the storage volume facts
    facts = util.merge.deep_merge_in_place(facts, compiler_facts, merge_lists=True)

    # Next, we merge the client facts into the facts
    facts = util.merge.deep_merge_in_place(facts, client_facts, merge_lists=True)

    log.debug("Merged facts before cleanup:", details=facts)

    return facts


def _get_client_facts(deployment_details: DeploymentDetails) -> dict:
    """Internal helper to retrieve client-level facts.

    Wraps :func:`get_client_facts` adding UNREGISTERED stub handling so the
    downstream merge logic can rely on required identity keys always being
    present (at least minimally).

    Args:
        deployment_details (DeploymentDetails): Deployment context providing
            the ``client`` identifier.

    Returns:
        dict: Raw client fact dictionary (PascalCase keys) or an
        ``UNREGISTERED`` stub containing ``Client`` and ``ClientStatus``.
    """

    log.debug("Getting facts for client: %s", deployment_details.client)

    # Get the dictionary of client facts dictionary for this deployment
    client = deployment_details.client
    client_facts = get_client_facts(client)
    if not client_facts:
        log.info(f"No client facts found for {client}. Contact DevOps to register this client.")
        return ClientFact(Client=client, ClientStatus="UNREGISTERED", OrganizationEmail="help@core.net").model_dump(by_alias=True)

    log.debug("Client facts:", details=client_facts)

    return client_facts


def _get_portfolio_facts(deployment_details: DeploymentDetails) -> dict:
    """Internal helper to retrieve portfolio-level facts.

    Adds UNREGISTERED stub handling to ensure merge safety when a portfolio
    has not yet been registered in the fact registry.

    Args:
        deployment_details (DeploymentDetails): Deployment context with
            ``client`` and ``portfolio`` identifiers.

    Returns:
        dict: Portfolio fact dictionary or an ``UNREGISTERED`` stub with
        ``PortfolioStatus``.
    """
    # Get the portfolio facts dictionary for this deployment
    log.debug("Getting portfolio facts for portfolio: %s", deployment_details.portfolio)

    portfolio = deployment_details.portfolio
    client = deployment_details.client
    portfolio_facts = get_portfolio_facts(client, portfolio)
    if not portfolio_facts:
        log.info(f"No portfolio facts found for {client}:{portfolio}. Contact DevOps to register this portfolio.")
        portfolio_facts = {
            "Portfolio": portfolio,
            "Client": client,
            "PortfolioStatus": "UNREGISTERED",
        }

    log.debug("Portfolio facts:", details=portfolio_facts)

    return portfolio_facts


def _get_app_facts(deployment_details: DeploymentDetails) -> dict:
    """Internal helper to retrieve single application fact record.

    Enforces uniqueness of app registration (raises ``ValueError`` if more
    than one matching fact exists) and returns an empty dict if absent so
    subsequent logic can proceed with zone/region discovery guarded by scope.

    Args:
        deployment_details (DeploymentDetails): Deployment context specifying
            client / portfolio / app identity.

    Returns:
        dict: Application fact mapping or empty dict when not registered.

    Raises:
        ValueError: If multiple app fact records match the identity.
    """
    # Get the app facts dictionary for this deployment
    log.debug(
        "Getting app facts for client:portfolio:app: %s:%s:%s",
        deployment_details.client,
        deployment_details.portfolio,
        deployment_details.app,
    )

    identity = deployment_details.get_identity()

    app_facts_list = get_app_facts(deployment_details)
    if not app_facts_list:
        app_facts_list = []
        log.info(f"No app facts found for {identity}. Contact DevOps to register this app.")

    if len(app_facts_list) > 1:
        log.info(f"Multiple app facts found for {identity}. Abort!!!")
        raise ValueError(f"Multiple app facts found for {identity}. Please refine your deployment details.")

    return app_facts_list[0] if app_facts_list else {}


def _get_zone_facts(deployment_details: DeploymentDetails, app_facts: dict) -> dict:
    """Internal helper to retrieve zone facts for the application.

    Resolves the zone identifier from ``app_facts``; if absent returns an
    ``UNREGISTERED`` stub. Provides consistent structure for downstream region
    and account fact extraction.

    Args:
        deployment_details (DeploymentDetails): Deployment context (client used
            for model resolution).
        app_facts (dict): Application fact dictionary possibly containing the
            zone key.

    Returns:
        dict: Zone fact mapping or stub with ``ZoneStatus`` when missing.
    """

    client = deployment_details.client
    log.debug("Getting zone facts for client: %s", client)

    identity = deployment_details.get_identity()

    zone = app_facts.get(ZONE_KEY, None)
    if not zone:
        log.info(f"No zone information defined in the application registration for {identity}.")
        return {"Zone": "<not defined>", "ZoneStatus": "UNREGISTERED"}

    # Get the zone facts dictionary for this deployment and environment
    zone_facts = get_zone_facts(client, zone)

    log.debug("Zone facts:", details=zone_facts)

    if not zone_facts:
        log.info(f"No zone facts found for {client}:{zone}. Contact DevOps to register this zone.")
        return {"Zone": zone, "ZoneStatus": "UNREGISTERED"}

    return zone_facts


def _get_region_facts(deployment_details: DeploymentDetails, app_facts: dict, zone_facts: dict) -> dict:
    """Internal helper to resolve region-specific facts within a zone.

    Chooses the region alias from ``app_facts`` or defaults, then extracts the
    corresponding region entry from the zone fact structure. Provides an
    ``UNREGISTERED`` stub if the region is not configured.

    Args:
        deployment_details (DeploymentDetails): Deployment context for logging.
        app_facts (dict): Application facts (may include region alias).
        zone_facts (dict): Zone facts mapping containing region collections.

    Returns:
        dict: Region fact mapping or stub with ``RegionStatus`` when missing.
    """

    client = deployment_details.client
    zone = app_facts.get(ZONE_KEY, None)
    app = app_facts.get("Name", None)

    log.debug("Getting region facts for client:zone, app: %s:%s, %s", client, zone, app)

    identity = deployment_details.get_identity()

    # If the app facts do not contain a region, use the default region alias
    region_alias = app_facts.get(REGION, None)
    if not region_alias:
        log.info(f"No region alias found for {identity}. Using default.")
        region_alias = V_DEFAULT_REGION_ALIAS

    # Get the region facts
    region_facts = dict(zone_facts.get(FACTS_REGION, {})).get(region_alias, None)
    if not region_facts:
        log.info(f"No region facts found for {client}:{zone}:{region_alias}. Contact DevOps to register this region.")
        return {"RegionStatus": "UNREGISTERED"}

    log.debug(f"Region facts for {region_alias}:", details=region_facts)

    return region_facts


def _get_account_facts(deployment_details: DeploymentDetails, zone_facts: dict) -> dict:
    """Internal helper to extract account-level facts from zone facts.

    Provides an ``UNREGISTERED`` stub when account configuration is missing so
    that subsequent deep merges maintain expected keys without raising.

    Args:
        deployment_details (DeploymentDetails): Deployment context (client +
            for logging + identity hints).
        zone_facts (dict): Zone fact mapping potentially containing account facts.

    Returns:
        dict: Account fact mapping or stub with ``AccountStatus`` when absent.
    """

    client = deployment_details.client
    zone = zone_facts.get("Zone", None)

    log.debug("Getting account facts for client:zone %s:%s", client, zone)

    account_facts = dict(zone_facts.get(FACTS_ACCOUNT, {}))
    if not account_facts:
        log.info(f"No account facts found for {client}:{zone}. Contact DevOps to register this account.")
        return {"AccountStatus": "UNREGISTERED"}

    log.debug("Account facts:", details=account_facts)

    return account_facts
