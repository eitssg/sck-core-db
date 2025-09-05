"""The Facter module provides a comprehensive facts database for deployment contexts.

This module retrieves and merges facts from multiple sources (client, portfolio, app, zone)
stored in DynamoDB to create complete Jinja2 template contexts for CloudFormation generation.

The facts system replaces the deprecated YAML-based configuration files and provides
dynamic, scalable configuration management for cloud deployments.
"""

from collections import ChainMap
from http import client
import os
from pydoc import cli
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
        model_class = ClientFact.model_class(client)
        item = model_class.get(client)
        data = ClientFact.from_model(item).model_dump()

        return data

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

        data = PortfolioFact.from_model(item).model_dump()

        return data

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

        data = ZoneFact.from_model(item).model_dump()

        return data

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
                data.append(ZoneFact.from_model(item).model_dump())

        if not data:
            log.warning(f"No zones found for account ID: {account_id} in client: {client}")
            return None

        return data

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

    app_facts_list = model_class.query(portfolio, scan_index_forward=True)

    data = []
    for app_facts in app_facts_list:
        if isinstance(app_facts, model_class) and app_facts.app_regex and re.match(app_facts.app_regex, identity):
            data.append(AppFact.from_model(app_facts).model_dump(mode="json"))

    if not data:
        log.warning(f"No app facts found for client: {client}, portfolio: {portfolio}, app: {app}")
        return None

    return data


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
    """Generate storage URL for artifact buckets based on deployment environment.

    Creates appropriate storage URLs for both cloud (S3) and local development
    environments. The URL format depends on the configured storage backend.

    Args:
        bucket_name (str): The storage bucket name (e.g., "acme-artifacts").
        bucket_region (str): The AWS region for the bucket (e.g., "us-east-1").

    Returns:
        str: The complete storage URL:
            - S3 environments: "s3://bucket-name"
            - Local environments: "/path/to/bucket-name" (Unix) or "C:\\path\\to\\bucket-name" (Windows)

    Examples:
        >>> # S3 storage URL (production/cloud environments)
        >>> url = get_store_url("my-bucket", "us-east-1")
        >>> print(url)  # "s3://my-bucket"

        >>> # Local storage URL (development environments)
        >>> # On Unix/Linux/macOS:
        >>> url = get_store_url("local-bucket", "us-west-2")
        >>> print(url)  # "/tmp/artifacts/local-bucket" (or similar local path)
        >>>
        >>> # On Windows:
        >>> url = get_store_url("local-bucket", "us-west-2")
        >>> print(url)  # "C:\\temp\\artifacts\\local-bucket" (or similar local path)

        >>> # Real-world usage with client artifacts
        >>> client = "ACME001"
        >>> bucket = f"{client.lower()}-artifacts"
        >>> region = "us-west-2"
        >>> store_url = get_store_url(bucket, region)
        >>> print(store_url)  # "s3://acme001-artifacts" (in cloud)
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
    """Generate comprehensive deployment facts for CloudFormation template rendering.

    Aggregates and merges facts from multiple sources (client, portfolio, app, zone)
    to create a complete Jinja2 template context dictionary. The facts provide all
    necessary configuration for infrastructure provisioning, resource tagging,
    security settings, and operational parameters.

    This is the primary entry point for fact retrieval and should be used by
    template compilers, deployment orchestrators, and configuration generators.

    Args:
        deployment_details (DeploymentDetails): Complete deployment context containing:
            - client (str): Client identifier
            - portfolio (str): Portfolio identifier
            - app (str): Application name
            - branch (str, optional): Git branch
            - build (str, optional): Build version
            - environment (str, optional): Override environment
            - data_center (str, optional): Override region

    Returns:
        dict: Comprehensive facts dictionary with PascalCase keys containing:

            Core Identity:
            - Client: str - Client identifier
            - Portfolio: str - Portfolio name
            - App: str - Application name
            - Branch: str - Git branch
            - Build: str - Build version
            - Environment: str - Deployment environment
            - DataCenter: str - Target region

            AWS Infrastructure:
            - AwsAccountId: str - Target AWS account
            - AwsRegion: str - Primary AWS region
            - OrganizationalUnit: str - AWS Organization OU
            - ResourceNamespace: str - Resource naming prefix

            Networking & Security:
            - VpcAliases: list[str] - VPC identifier mappings
            - SubnetAliases: list[str] - Subnet identifier mappings
            - SecurityAliases: dict - CIDR blocks and access controls
            - SecurityGroupAliases: dict - Security group mappings
            - ProxyHost/ProxyPort: str/int - Corporate proxy settings
            - NameServers: list[str] - DNS server configurations

            KMS & Encryption:
            - Kms: dict - KMS key configuration and delegation

            Application Configuration:
            - Zone: str - Target deployment zone
            - Repository: str - Source code repository
            - ImageAliases: dict - Container/AMI mappings
            - Metadata: dict - Deployment parameters and scaling

            Organizational:
            - Owner: dict - Portfolio owner contact information
            - Contacts: list[dict] - Team contact directory
            - Approvers: list[dict] - Approval workflow configuration

            Resource Management:
            - Tags: dict - Merged resource tags from all levels
            - ArtifactKeyPrefix: str - Artifact storage path
            - BuildFilesPrefix: str - Build files storage path
            - SharedFilesPrefix: str - Shared resources path

    Raises:
        ValueError: If any required facts are missing or invalid:
            - Client facts not found
            - Portfolio facts not found
            - App facts not found or multiple matches
            - Zone facts not found
            - Account facts missing in zone
            - Region not enabled in zone

    Examples:
        >>> # Standard deployment context
        >>> dd = DeploymentDetails(
        ...     client="ACME001",
        ...     portfolio="acme-enterprise-platform",
        ...     app="acme-platform-core",
        ...     branch="main",
        ...     build="1.2.0"
        ... )
        >>> facts = get_facts(dd)
        >>>
        >>> # Access core identification
        >>> print(facts["Client"])       # "ACME001"
        >>> print(facts["Portfolio"])    # "acme-enterprise-platform"
        >>> print(facts["App"])         # "acme-platform-core"
        >>> print(facts["Environment"]) # "production" (derived from main branch)
        >>>
        >>> # Access AWS infrastructure
        >>> print(facts["AwsAccountId"])  # "123456789012"
        >>> print(facts["AwsRegion"])     # "us-east-1"
        >>> print(facts["Zone"])         # "prod-east-primary"
        >>>
        >>> # Access networking configuration
        >>> vpc_aliases = facts["VpcAliases"]
        >>> print(vpc_aliases[0])        # "vpc-prod-main"
        >>>
        >>> security_groups = facts["SecurityGroupAliases"]
        >>> print(security_groups["WebTierSg"])  # "sg-web-prod-east-12345"
        >>>
        >>> # Access image mappings
        >>> images = facts["ImageAliases"]
        >>> print(images["ApiGateway"])  # "ami-0c02fb55956c7d316"
        >>> print(images["Ubuntu22"])   # "ami-0c02fb55956c7d316"
        >>>
        >>> # Access security configuration
        >>> kms = facts["Kms"]
        >>> print(kms["KmsKeyArn"])      # "arn:aws:kms:us-east-1:123456789012:key/..."
        >>>
        >>> # Access merged resource tags
        >>> tags = facts["Tags"]
        >>> print(tags["Environment"])  # "production"
        >>> print(tags["Team"])         # "platform-engineering"
        >>> print(tags["CostCenter"])   # "CC-IT-001"
        >>>
        >>> # Access organizational contacts
        >>> owner = facts["Owner"]
        >>> print(f"{owner['Name']} <{owner['Email']}>")  # "Sarah Johnson <sarah@acme.com>"
        >>>
        >>> contacts = facts["Contacts"]
        >>> print(f"Team size: {len(contacts)}")  # 4
        >>>
        >>> # Access artifact storage paths
        >>> print(facts["ArtifactKeyPrefix"])    # "artifacts/acme001/acme-enterprise-platform/acme-platform-core/main/1.2.0"
        >>> print(facts["BuildFilesPrefix"])     # "files/acme001/acme-enterprise-platform/acme-platform-core/main/1.2.0"

        >>> # Environment derivation from branch
        >>> dd_dev = DeploymentDetails(
        ...     client="ACME001",
        ...     portfolio="acme-enterprise-platform",
        ...     app="acme-platform-core",
        ...     branch="dev-usw2"
        ... )
        >>> facts = get_facts(dd_dev)
        >>> print(facts["Environment"])  # "dev" (derived from branch)
        >>> print(facts["Region"])       # "usw2" (derived from branch)

        >>> # Error handling examples
        >>> try:
        ...     dd_invalid = DeploymentDetails(client="nonexistent")
        ...     get_facts(dd_invalid)
        ... except ValueError as e:
        ...     print(f"Error: {e}")  # "Client facts not found for nonexistent"
        >>>
        >>> try:
        ...     dd_no_app = DeploymentDetails(
        ...         client="ACME001",
        ...         portfolio="acme-enterprise-platform",
        ...         app="nonexistent-app"
        ...     )
        ...     get_facts(dd_no_app)
        ... except ValueError as e:
        ...     print(f"Error: {e}")  # "App facts not found for prn:acme-enterprise-platform:nonexistent-app:*:*"
    """
    client_facts = _get_client_facts(deployment_details)

    scope = deployment_details.get_scope()

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

    log.debug(f"Compiler facts:", details=compiler_facts)

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

    # Next, merge the portfolio facts into the facts
    facts = util.merge.deep_merge_in_place(facts, portfolio_facts, merge_lists=True)

    # Next, merge the app facts into the facts
    facts = util.merge.deep_merge_in_place(facts, app_facts, merge_lists=True)

    # Finally, we merge in the deployment details facts
    facts = util.merge.deep_merge_in_place(facts, deployment_facts, merge_lists=True)

    # Lastly, we merge in the storage volume facts
    facts = util.merge.deep_merge_in_place(facts, compiler_facts, merge_lists=True)

    log.debug(f"Merged facts before cleanup:", details=facts)

    return facts


def _get_client_facts(deployment_details: DeploymentDetails) -> dict:

    log.debug(f"Getting facts for client: %s", deployment_details.client)

    # Get the dictionary of client facts dictionary for this deployment
    client = deployment_details.client
    client_facts = get_client_facts(client)
    if not client_facts:
        log.info(f"No client facts found for {client}. Contact DevOps to register this client.")
        return {"Client": client, "ClientStatus": "UNREGISTERED"}

    log.debug(f"Client facts:", details=client_facts)

    return client_facts


def _get_portfolio_facts(deployment_details: DeploymentDetails) -> dict:
    # Get the portfolio facts dictionary for this deployment
    log.debug(f"Getting portfolio facts for portfolio: %s", deployment_details.portfolio)

    portfolio = deployment_details.portfolio
    client = deployment_details.client
    portfolio_facts = get_portfolio_facts(client, portfolio)
    if not portfolio_facts:
        log.info(f"No portfolio facts found for {client}:{portfolio}. Contact DevOps to register this portfolio.")
        portfolio_facts = {"Portfolio": portfolio, "Client": client, "PortfolioStatus": "UNREGISTERED"}

    log.debug(f"Portfolio facts:", details=portfolio_facts)

    return portfolio_facts


def _get_app_facts(deployment_details: DeploymentDetails) -> dict:
    # Get the app facts dictionary for this deployment
    log.debug(
        f"Getting app facts for client:portfolio:app: %s:%s:%s",
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

    return app_facts_list[0]


def _get_zone_facts(deployment_details: DeploymentDetails, app_facts: dict) -> dict:

    client = deployment_details.client
    log.debug(f"Getting zone facts for client: %s", client)

    identity = deployment_details.get_identity()

    zone = app_facts.get(ZONE_KEY, None)
    if not zone:
        log.info(f"No zone information defined in the application registration for {identity}.")
        return {"Zone": "<not defined>", "ZoneStatus": "UNREGISTERED"}

    # Get the zone facts dictionary for this deployment and environment
    zone_facts = get_zone_facts(client, zone)

    log.debug(f"Zone facts:", details=zone_facts)

    if not zone_facts:
        log.info(f"No zone facts found for {client}:{zone}. Contact DevOps to register this zone.")
        return {"Zone": zone, "ZoneStatus": "UNREGISTERED"}

    return zone_facts


def _get_region_facts(deployment_details: DeploymentDetails, app_facts: dict, zone_facts: dict) -> dict:

    client = deployment_details.client
    zone = app_facts.get(ZONE_KEY, None)
    app = app_facts.get("Name", None)

    log.debug(f"Getting region facts for client:zone, app: %s:%s, %s", client, zone, app)

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

    client = deployment_details.client
    zone = zone_facts.get("Zone", None)

    log.debug(f"Getting account facts for client:zone %s:%s", client, zone)

    account_facts = dict(zone_facts.get(FACTS_ACCOUNT, {}))
    if not account_facts:
        log.info(f"No account facts found for {client}:{zone}. Contact DevOps to register this account.")
        return {"AccountStatus": "UNREGISTERED"}

    log.debug(f"Account facts:", details=account_facts)

    return account_facts
