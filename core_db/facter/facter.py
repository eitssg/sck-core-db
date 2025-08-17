"""The Facter object is the "FACTS" database. This object is DEPRECATED and should not be used.
This FACTS database should come from DynamoDB. Not 'accounts.yaml' and 'apps.yaml' files.

(In re-rewrite. We need to use DynamoDB instead of FACTS YAML files)
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

from ..constants import REGION, ENVIRONMENT, ZONE_KEY

from ..registry.client.models import ClientFactsModel, ClientFactsFactory
from ..registry.portfolio.models import PortfolioFactsModel, PortfolioFactsFactory
from ..registry.zone.models import ZoneFactsModel, ZoneFactsFactory
from ..registry.app.models import AppFactsModel, AppFactsFactory


def get_client_model(client) -> ClientFactsModel:
    """Returns the ClientFactsModel class from the ClientFactsFactory.

    This is a helper function to avoid circular imports.

    Args:
        client: The client identifier for model creation

    Returns:
        ClientFactsModel: The client facts model instance for the specified client

    Examples:
        >>> model = get_client_model("acme")
        >>> print(model.Meta.table_name)  # "acme-core-automation-clients"
    """
    return ClientFactsFactory.get_model(client)


def get_portfolio_model(client) -> PortfolioFactsModel:
    """Returns the PortfolioFactsModel class from the PortfolioFactsFactory.

    This is a helper function to avoid circular imports.

    Args:
        client: The client identifier for model creation

    Returns:
        PortfolioFactsModel: The portfolio facts model instance for the specified client

    Examples:
        >>> model = get_portfolio_model("acme")
        >>> print(model.Meta.table_name)  # "acme-core-automation-portfolios"
    """
    return PortfolioFactsFactory.get_model(client)


def get_zone_model(client) -> ZoneFactsModel:
    """Returns the ZoneFactsModel class.

    This is a helper function to avoid circular imports.

    Args:
        client: The client identifier for model creation

    Returns:
        ZoneFactsModel: The zone facts model instance for the specified client

    Examples:
        >>> model = get_zone_model("acme")
        >>> print(model.Meta.table_name)  # "acme-core-automation-zones"
    """
    return ZoneFactsFactory.get_model(client)


def get_app_model(client) -> AppFactsModel:
    """Returns the AppFactsModel class.

    This is a helper function to avoid circular imports.

    Args:
        client: The client identifier for model creation

    Returns:
        AppFactsModel: The app facts model instance for the specified client

    Examples:
        >>> model = get_app_model("acme")
        >>> print(model.Meta.table_name)  # "acme-core-automation-apps"
    """
    return AppFactsFactory.get_model(client)


def get_client_facts(client: str) -> dict | None:
    """Uses the logic within the ClientFactsModel class to retrieve the Client Details.

    This is a helper function and you can call ClientFactsModel.get(client) directly without
    using this helper.

    Args:
        client (str): The client name to retrieve from the database

    Returns:
        dict | None: The dictionary representing the ClientFactsModel database table record,
            or None if the client is not found

    Examples:
        >>> client_facts = get_client_facts("acme")
        >>> if client_facts:
        ...     print(f"Client: {client_facts['name']}")
        ...     print(f"Namespace: {client_facts['ResourceNamespace']}")
        ...     print(f"Tags: {client_facts['Tags']}")

        >>> # Handle missing client
        >>> facts = get_client_facts("nonexistent")
        >>> print(facts)  # None
    """
    try:
        model = get_client_model(client)
        facts = model.get(client)
        if facts is None:
            return None
        return facts.to_simple_dict()

    except Exception as e:
        log.error(f"Error getting client facts: {str(e)}")
        return None


def get_portfolio_facts(client: str, portfolio: str) -> dict | None:
    """Uses the logic within the PortfolioFactsModel class to retrieve the Portfolio Details.

    This is a helper function and you can call PortfolioFactsModel.get(client, portfolio) directly
    without using this helper.

    Args:
        client (str): The client name (slug)
        portfolio (str): The portfolio name (slug)

    Returns:
        dict | None: The dictionary representing PortfolioFactsModel database table record,
            or None if the portfolio is not found

    Examples:
        >>> portfolio_facts = get_portfolio_facts("acme", "core")
        >>> if portfolio_facts:
        ...     print(f"Portfolio: {portfolio_facts['name']}")
        ...     print(f"Owner: {portfolio_facts['Owner']['Email']}")
        ...     print(f"Contacts: {len(portfolio_facts['Contacts'])}")

        >>> # Handle missing portfolio
        >>> facts = get_portfolio_facts("acme", "nonexistent")
        >>> print(facts)  # None
    """
    try:
        model = get_portfolio_model(client)
        portfolio_facts = model.get(client, portfolio)
        if portfolio_facts is None:
            return None
        return portfolio_facts.to_simple_dict()

    except Exception as e:
        log.error(f"Error getting portfolio facts: {e}")
        return None


def get_zone_facts(client: str, zone: str) -> dict | None:
    """Uses the logic within the ZoneFactsModel class to retrieve the Zone Details.

    This is a helper function and you can call ZoneFactsModel.get(zone_key, zone_name) directly
    without using this helper.

    zone_key = client + ':' + portfolio

    Args:
        client (str): The client name
        zone (str): The zone label

    Returns:
        dict | None: The dictionary representing the ZoneFactsModel database table record,
            or None if the zone is not found

    Examples:
        >>> zone_facts = get_zone_facts("acme", "production")
        >>> if zone_facts:
        ...     print(f"Zone: {zone_facts['name']}")
        ...     print(f"Account ID: {zone_facts['Account']['AwsAccountId']}")
        ...     print(f"Environment: {zone_facts['Environment']}")

        >>> # Handle missing zone
        >>> facts = get_zone_facts("acme", "nonexistent")
        >>> print(facts)  # None
    """
    try:
        model = get_zone_model(client)
        zone_facts = model.get(client, zone)
        if zone_facts is None:
            return None
        return zone_facts.to_simple_dict()

    except Exception as e:
        log.error(f"Error getting zone facts: {e}")
        return None


def get_zone_facts_by_account_id(client: str, account_id: str) -> list[dict] | None:
    """Uses the logic within the ZoneFactsModel class to retrieve the Zone Details.

    This is a helper function and you can call ZoneFactsModel.query(account_id) directly
    without using this helper.

    zone_key = client + ':' + portfolio

    Args:
        client (str): The client name
        account_id (str): The AWS account ID

    Returns:
        list[dict] | None: The list of Zone Facts that are registered with this AWS Account ID,
            or None if no zones are found

    Examples:
        >>> zone_facts_list = get_zone_facts_by_account_id("acme", "123456789012")
        >>> if zone_facts_list:
        ...     for zone in zone_facts_list:
        ...         print(f"Zone: {zone['name']}")
        ...         print(f"Environment: {zone['Environment']}")

        >>> # Handle no zones found
        >>> facts = get_zone_facts_by_account_id("acme", "999999999999")
        >>> print(facts)  # None or empty list
    """
    try:
        model = get_zone_model(client)
        zone_facts = model.query(account_id)
        if zone_facts is None:
            return None
        return [zf.to_simple_dict() for zf in zone_facts]

    except Exception as e:
        log.error(f"Error getting zone facts by account ID: {e}")
        return None


def get_app_facts(deployment_details: DeploymentDetails) -> dict | None:
    """Retrieves the Facts for DeploymentDetails that can be used in the Jinja2 Renderer
    to generate final CloudFormation Templates.

    Args:
        deployment_details (DeploymentDetails): The deployment details of the TaskPayload

    Returns:
        dict | None: The app facts dictionary or None if not found

    Raises:
        ValueError: If required fields are missing from deployment_details

    Examples:
        >>> dd = DeploymentDetails(
        ...     client="acme",
        ...     portfolio="core",
        ...     app="api",
        ...     branch="master",
        ...     build="1234"
        ... )
        >>> app_facts = get_app_facts(dd)
        >>> if app_facts:
        ...     print(f"App: {app_facts['name']}")
        ...     print(f"Repository: {app_facts['Repository']}")
        ...     print(f"Zone: {app_facts['Zone']}")

        >>> # Handle missing app facts
        >>> dd_invalid = DeploymentDetails(client="acme", portfolio="invalid", app="nonexistent")
        >>> facts = get_app_facts(dd_invalid)
        >>> print(facts)  # None

        >>> # Error handling for missing fields
        >>> try:
        ...     dd_incomplete = DeploymentDetails(client="acme")  # Missing portfolio and app
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

    branch = deployment_details.branch_short_name
    if not branch:
        branch = "*"

    build = deployment_details.build
    if not build:
        build = "*"

    portfolio_key = deployment_details.get_client_portfolio_key()
    app_test_string = f"prn:{portfolio}:{app}:{branch}:{build}"

    model = get_app_model(client)
    app_facts_list = model.query(portfolio_key)

    for app_facts in app_facts_list:
        arx = app_facts.AppRegex
        if re.match(arx, app_test_string):
            return app_facts.to_simple_dict()

    return None


def derive_environment_from_branch(branch: str) -> tuple[str, str]:
    """Derive the environment and region alias from the branch name.

    Example of a branch name is **dev-sin** or **feature1/dev-sin**

    Where *dev* is the environment and *sin* is the region alias.

    Args:
        branch (str): The application deployment git repository branch name

    Returns:
        tuple[str, str]: The environment and region alias tuple

    Examples:
        >>> env, region = derive_environment_from_branch("dev-sin")
        >>> print((env, region))  # ("dev", "sin")

        >>> env, region = derive_environment_from_branch("feature1/dev-sin")
        >>> print((env, region))  # ("dev", "sin")

        >>> env, region = derive_environment_from_branch("master")
        >>> print((env, region))  # ("production", "use1")  # or whatever V_DEFAULT_ENVIRONMENT is

        >>> # Complex feature branch
        >>> env, region = derive_environment_from_branch("feature/new-auth/staging-usw2")
        >>> print((env, region))  # ("staging", "usw2")

        >>> # Single part branch (no region)
        >>> env, region = derive_environment_from_branch("development")
        >>> print((env, region))  # ("development", "use1")  # uses default region
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
    """Format the contact details for the Jinja2 template context.

    Args:
        contact (dict): The contact details dictionary containing Name and/or Email

    Returns:
        str: The formatted contact string

    Examples:
        >>> contact = {"Name": "John Doe", "Email": "john@example.com"}
        >>> formatted = format_contact(contact)
        >>> print(formatted)  # "John Doe <john@example.com>"

        >>> contact = {"Email": "john@example.com"}
        >>> formatted = format_contact(contact)
        >>> print(formatted)  # "john@example.com"

        >>> contact = {"Name": "John Doe"}
        >>> formatted = format_contact(contact)
        >>> print(formatted)  # "John Doe"

        >>> contact = {}
        >>> formatted = format_contact(contact)
        >>> print(formatted)  # "" (empty string)

        >>> # Real-world usage in template context
        >>> portfolio_facts = {"Owner": {"Name": "Jane Smith", "Email": "jane@acme.com"}}
        >>> owner_formatted = format_contact(portfolio_facts["Owner"])
        >>> print(owner_formatted)  # "Jane Smith <jane@acme.com>"
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
    """Get the storage URL for the specified bucket and region.

    Args:
        bucket_name (str): The S3 bucket name
        bucket_region (str): The AWS region for the bucket

    Returns:
        str: The storage URL

    Examples:
        >>> # S3 storage (production)
        >>> url = get_store_url("my-bucket", "us-east-1")
        >>> print(url)  # "s3://my-bucket"

        >>> # Local storage (development)
        >>> url = get_store_url("local-bucket", "us-west-2")
        >>> print(url)  # "/path/to/local-bucket" (on Windows: "C:\\path\\to\\local-bucket")

        >>> # Real-world usage
        >>> client = "acme"
        >>> bucket = f"{client}-artifacts"
        >>> region = "us-west-2"
        >>> store_url = get_store_url(bucket, region)
        >>> print(store_url)  # "s3://acme-artifacts"
    """
    store = util.get_storage_volume(bucket_region)
    sep = "/" if util.is_use_s3() else os.path.sep
    return sep.join([store, bucket_name])


def get_compiler_facts(dd: DeploymentDetails) -> dict:
    """Get compiler-specific facts for artifact and file storage.

    Args:
        dd (DeploymentDetails): The deployment details

    Returns:
        dict: Dictionary containing compiler facts for template rendering

    Examples:
        >>> dd = DeploymentDetails(
        ...     client="acme",
        ...     portfolio="core",
        ...     app="api",
        ...     branch="main",
        ...     build="123"
        ... )
        >>> facts = get_compiler_facts(dd)
        >>> print(facts['ArtefactsBucketName'])  # "acme-artifacts"
        >>> print(facts['ArtifactKeyPrefix'])    # "artifacts/acme/core/api/main/123"
        >>> print(facts['BuildFilesPrefix'])    # "files/acme/core/api/main/123"

        >>> # Access different storage prefixes
        >>> print(facts['PortfolioFilesPrefix'])  # "files/acme/core"
        >>> print(facts['AppFilesPrefix'])       # "files/acme/core/api"
        >>> print(facts['BranchFilesPrefix'])    # "files/acme/core/api/main"

        >>> # Both spelling variants
        >>> print(facts['ArtefactsBucketName'])  # British spelling
        >>> print(facts['ArtifactBucketName'])   # American spelling (same value)
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
    """Get the facts for a given deployment context.

    Combines facts from multiple sources (client, portfolio, app, zone) to create
    a complete Jinja2 template context for CloudFormation generation.

    Args:
        deployment_details (DeploymentDetails): The deployment details containing client,
            portfolio, app, etc.

    Returns:
        dict: The Jinja2 template context dictionary (a.k.a FACTS)

    Raises:
        ValueError: For any inconsistency or missing required facts

    Examples:
        >>> dd = DeploymentDetails(
        ...     client="acme",
        ...     portfolio="core",
        ...     app="api",
        ...     branch="master",
        ...     build="1234"
        ... )
        >>> facts = get_facts(dd)
        >>>
        >>> # Access basic identification
        >>> print(facts["Client"])       # "acme"
        >>> print(facts["Portfolio"])    # "core"
        >>> print(facts["App"])         # "api"
        >>> print(facts["Build"])       # "1234"
        >>>
        >>> # Access AWS configuration
        >>> print(facts["AwsAccountId"])  # "123456789012"
        >>> print(facts["AwsRegion"])     # "us-west-2"
        >>> print(facts["Environment"])   # "production"
        >>>
        >>> # Access networking configuration
        >>> print(facts["VpcAliases"]["public"])     # "Vpc1"
        >>> print(facts["SubnetAliases"]["private"]) # "PrivateSubnet"
        >>>
        >>> # Access security configuration
        >>> print(facts["SecurityAliases"]["intranet"][0]["Value"])  # "10.0.0.0/8"
        >>>
        >>> # Access KMS configuration
        >>> print(facts["Kms"]["KmsKeyArn"])  # "arn:aws:kms:us-west-2:..."
        >>>
        >>> # Access tags for resource tagging
        >>> print(facts["Tags"]["Environment"])  # "production"
        >>> print(facts["Tags"]["CostCenter"])   # "COST123"
        >>>
        >>> # Access contact information
        >>> print(facts["Owner"]["Email"])       # "owner@acme.com"
        >>> print(facts["Contacts"][0]["Email"]) # "contact@acme.com"
        >>>
        >>> # Access artifact paths
        >>> print(facts["ArtifactKeyPrefix"])    # "artifacts/acme/core/api/master/1234"
        >>> print(facts["BuildFilesPrefix"])     # "files/acme/core/api/master/1234"

        >>> # Error handling
        >>> try:
        ...     dd_invalid = DeploymentDetails(client="nonexistent")
        ...     get_facts(dd_invalid)
        ... except ValueError as e:
        ...     print(f"Error: {e}")  # "Client facts not found for nonexistent"

        >>> # Branch-based environment derivation
        >>> dd_dev = DeploymentDetails(
        ...     client="acme",
        ...     portfolio="core",
        ...     app="api",
        ...     branch="dev-usw2"
        ... )
        >>> facts = get_facts(dd_dev)
        >>> print(facts["Environment"])  # "dev" (derived from branch)
        >>> print(facts["Region"])       # "usw2" (derived from branch)
    """
    client = deployment_details.client

    # Get the dictionary of client facts dictionary for this deployment
    client_facts = get_client_facts(client)
    if not client_facts:
        raise ValueError(f"Client facts not found for {client}")

    # Get the portfolio facts dictionary for this deployment
    portfolio = deployment_details.portfolio
    portfolio_facts = get_portfolio_facts(client, portfolio)
    if not portfolio_facts:
        raise ValueError(f"Portfolio facts not found for {client}:{portfolio}")

    # Get the app facts dictionary for this deployment
    identity = deployment_details.get_identity()
    app_facts = get_app_facts(deployment_details)
    if app_facts is None:
        raise ValueError(f"App facts not found for {identity}. Contact DevOps to register this app.")

    # If the app facts do not contain a zone, throw an error
    zone = app_facts.get(ZONE_KEY, None)
    if not zone:
        raise ValueError(f"Zone not found for {identity}")

    # If the app facts do not contain a region, use the default region alias
    region_alias = app_facts.get(REGION, None)
    if not region_alias:
        raise ValueError(f"Region alias not found for {identity}")

    # if environment is not set, try to derive it from the branch. But facts ALWAYS come first.
    environment = app_facts.get(ENVIRONMENT, None)
    branch_region_alias = V_DEFAULT_REGION_ALIAS
    if not environment:
        environment, branch_region_alias = derive_environment_from_branch(deployment_details.branch or V_DEFAULT_REGION_ALIAS)

    # FACTS always override user input. So, don't use the user input if FACTS are present.
    if region_alias is None:
        region_alias = branch_region_alias

    # Get the zone facts dictionary for this deployment and environment
    zone_facts = get_zone_facts(client, zone)
    if not zone_facts:
        raise ValueError(f"Zone facts not found for {client}:{zone}")

    account_facts = zone_facts.get(FACTS_ACCOUNT, None)
    if account_facts is None:
        raise ValueError(f"Account facts not found for {zone}")

    # Get the region facts
    region_facts = zone_facts.get(FACTS_REGION, {}).get(region_alias, None)
    if region_facts is None:
        raise ValueError(f"Region {region_alias} has not been enabled for {zone}")

    compiler_facts = get_compiler_facts(deployment_details)

    # Now that we have ALL the facts, let's gather all the Tags for this deployment starting top down
    # Client -> Zone -> Region -> Portfolio -> App
    tags = ChainMap(
        client_facts.get(FACTS_TAGS, {}),
        zone_facts.get(FACTS_TAGS, {}),
        region_facts.get(FACTS_TAGS, {}),
        portfolio_facts.get(FACTS_TAGS, {}),
        app_facts.get(FACTS_TAGS, {}),
        {
            TAG_ENVIRONMENT: environment,
            TAG_REGION: region_alias,
            TAG_OWNER: format_contact(portfolio_facts.get("Owner", {})),
            TAG_CONTACTS: ",".join([format_contact(c) for c in portfolio_facts.get("Contacts", [])]),
        },
    )
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

    return facts
