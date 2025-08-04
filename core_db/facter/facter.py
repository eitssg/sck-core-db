"""
The Facter object is the "FACTS" database. This object is DEPRECATED and should not be used.
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

from ..registry.client.models import ClientFacts, ClientFactsFactory
from ..registry.portfolio.models import PortfolioFacts, PortfolioFactsFactory
from ..registry.zone.models import ZoneFacts, ZoneFactsFactory
from ..registry.app.models import AppFacts, AppFactsFactory


def get_client_model(client) -> ClientFacts:
    """
    Returns the ClientFacts class from the ClientFactsFactory.
    This is a helper function to avoid circular imports.
    """
    return ClientFactsFactory.get_model(client)


def get_portfolio_model(client) -> PortfolioFacts:
    """
    Returns the PortfolioFacts class from the PortfolioFactsFactory.
    This is a helper function to avoid circular imports.
    """
    return PortfolioFactsFactory.get_model(client)


def get_zone_model(client) -> ZoneFacts:
    """
    Returns the ZoneFacts class.
    This is a helper function to avoid circular imports.
    """
    return ZoneFactsFactory.get_model(client)


def get_app_model(client) -> AppFacts:
    """
    Returns the AppFacts class.
    This is a helper function to avoid circular imports.
    """
    return AppFactsFactory.get_model(client)


def get_client_facts(client: str) -> dict | None:
    """
    Uses the logic within the :class:`ClientFacts` class to retrieve the Client Details.

    This is a helper function and you can call ClientFacts.get(client) directly without
    using this helper.

    :param client: The client name to retrieve from the database
    :type client: str
    :returns: The dictionary representing the ClientFacts database table record
    :rtype: dict | None

    Examples
    --------
    >>> client_facts = get_client_facts("acme")
    >>> if client_facts:
    ...     print(f"Client: {client_facts['name']}")
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
    """
    Uses the logic within the :class:`PortfolioFacts` class to retrieve the Portfolio Details.

    This is a helper function and you can call PortfolioFacts.get(client, portfolio) directly
    without using this helper.

    :param client: The client name (slug)
    :type client: str
    :param portfolio: The portfolio name (slug)
    :type portfolio: str
    :returns: The dictionary representing PortfolioFacts database table record
    :rtype: dict | None

    Examples
    --------
    >>> portfolio_facts = get_portfolio_facts("acme", "core")
    >>> if portfolio_facts:
    ...     print(f"Portfolio: {portfolio_facts['name']}")
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
    """
    Uses the logic within the :class:`ZoneFacts` class to retrieve the Zone Details.

    This is a helper function and you can call ZoneFacts.get(zone_key, zone_name) directly
    without using this helper.

    zone_key = client + ':' + portfolio

    :param client: The client name
    :type client: str
    :param zone: The zone label
    :type zone: str
    :returns: The dictionary representing the ZoneFacts database table record
    :rtype: dict | None

    Examples
    --------
    >>> zone_facts = get_zone_facts("acme", "production")
    >>> if zone_facts:
    ...     print(f"Zone: {zone_facts['name']}")
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
    """
    Uses the logic within the :class:`ZoneFacts` class to retrieve the Zone Details.

    This is a helper function and you can call ZoneFacts.query(account_id) directly
    without using this helper.

    zone_key = client + ':' + portfolio

    :param account_id: The AWS account ID
    :type account_id: str
    :returns: The list of Zone Facts that are registered with this AWS Account ID
    :rtype: list[dict] | None

    Examples
    --------
    >>> zone_facts_list = get_zone_facts_by_account_id(client, "123456789012")
    >>> if zone_facts_list:
    ...     for zone in zone_facts_list:
    ...         print(f"Zone: {zone['name']}")
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
    """
    Retrieves the Facts for DeploymentDetails that can be used in the Jinja2 Renderer
    to generate final CloudFormation Templates.

    :param deployment_details: The deployment details of the TaskPayload
    :type deployment_details: DeploymentDetails
    :returns: The app facts dictionary or None if not found
    :rtype: dict | None
    :raises ValueError: If required fields are missing from deployment_details

    Examples
    --------
    >>> dd = DeploymentDetails(client="acme", portfolio="core", app="api", branch="master", build="1234")
    >>> app_facts = get_app_facts(dd)
    >>> if app_facts:
    ...     print(f"App: {app_facts['name']}")
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
    """
    Derive the environment and region alias from the branch name.

    Example of a branch name is **dev-sin** or **feature1/dev-sin**

    Where *dev* is the environment and *sin* is the region alias.

    :param branch: The application deployment git repository branch name
    :type branch: str
    :returns: The environment and region alias tuple
    :rtype: tuple[str, str]

    Examples
    --------
    >>> env, region = derive_environment_from_branch("dev-sin")
    >>> # Returns: ("dev", "sin")

    >>> env, region = derive_environment_from_branch("feature1/dev-sin")
    >>> # Returns: ("dev", "sin")

    >>> env, region = derive_environment_from_branch("master")
    >>> # Returns: ("production", "use1")  # or whatever V_DEFAULT_ENVIRONMENT is
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
    """
    Format the contact details for the Jinja2 template context.

    :param contact: The contact details dictionary
    :type contact: dict
    :returns: The formatted contact string
    :rtype: str

    Examples
    --------
    >>> contact = {"Name": "John Doe", "Email": "john@example.com"}
    >>> formatted = format_contact(contact)
    >>> # Returns: "John Doe <john@example.com>"

    >>> contact = {"Email": "john@example.com"}
    >>> formatted = format_contact(contact)
    >>> # Returns: "john@example.com"
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
    """
    Get the storage URL for the specified bucket and region.

    :param bucket_name: The S3 bucket name
    :type bucket_name: str
    :param bucket_region: The AWS region for the bucket
    :type bucket_region: str
    :returns: The storage URL
    :rtype: str

    Examples
    --------
    >>> url = get_store_url("my-bucket", "us-east-1")
    >>> # Returns: "s3://my-bucket" or "/path/to/my-bucket" depending on storage type
    """
    store = util.get_storage_volume(bucket_region)
    sep = "/" if util.is_use_s3() else os.path.sep
    return sep.join([store, bucket_name])


def get_compiler_facts(dd: DeploymentDetails) -> dict:
    """
    Get compiler-specific facts for artifact and file storage.

    :param dd: The deployment details
    :type dd: DeploymentDetails
    :returns: Dictionary containing compiler facts for template rendering
    :rtype: dict

    Examples
    --------
    >>> dd = DeploymentDetails(client="acme", portfolio="core", app="api")
    >>> facts = get_compiler_facts(dd)
    >>> print(facts['ArtefactsBucketName'])
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
    """
    Get the facts for a given deployment context.

    Combines facts from multiple sources (client, portfolio, app, zone) to create
    a complete Jinja2 template context for CloudFormation generation.

    :param deployment_details: The deployment details containing client, portfolio, app, etc.
    :type deployment_details: DeploymentDetails
    :returns: The Jinja2 template context dictionary (a.k.a FACTS)
    :rtype: dict
    :raises ValueError: For any inconsistency or missing required facts

    Examples
    --------
    >>> dd = DeploymentDetails(
    ...     client="acme",
    ...     portfolio="core",
    ...     app="api",
    ...     branch="master",
    ...     build="1234"
    ... )
    >>> facts = get_facts(dd)
    >>> # Returns merged facts from all sources
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
