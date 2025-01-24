"""
The Factor object is the "FACTS" database.  This object is DEPRECATED and should not be used.
This FACTS database should come from DynamoDB.  Not 'accounts.yaml' and 'apps.yaml' files.

(In re-rewrite.  We need to use DynamoDB instead of FACTS YAML files)
"""

from typing import Any
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

from ..registry.client.models import ClientFacts
from ..registry.portfolio.models import PortfolioFacts
from ..registry.zone.models import ZoneFacts
from ..registry.app.models import AppFacts


def get_client_facts(client: str) -> dict | None:
    """
    Uses the logic within the :class:`Clientfacts` class to retrieve the Client Details.

    This is a helper frunction and you can call ClientFacts.get(client) directly without
    using this helper.

    Args:
        client (str): The client name to retreive from the

    Return:
        (dict): The dictionary representing the ClientFacts database table record.

    """
    try:

        facts = ClientFacts.get(client)
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

    Args:
        client (str): The client name (slug)
        portfolio (str): The portfolio name (slug)

    Returns:
        dict | None: The dictionary representing PortFolioFacts database table record.
    """
    try:

        portfolio_facts = PortfolioFacts.get(client, portfolio)
        if portfolio_facts is None:
            return None
        return portfolio_facts.to_simple_dict()

    except Exception as e:
        log.error(f"Error getting portfolio facts: {e}")
        return None


def get_zone_facts(client: str, zone: str) -> dict | None:
    """
    Uses the logic with the :class:`ZoneFacts` class to retrieve the Zone Details.

    This is a helper function and you can call ZoneFacts.get(zone_key, zone_name) directly
    without using this helper.

    zone_key = client + ':' + portfolio

    Args:
        client (str): The client name
        portfolio (str): The portfoio name
        zone (str): The one label

    Returns:
        dict | None: The dictionary represeting the ZoneFacts database table record.
    """
    try:

        zone_facts = ZoneFacts.get(client, zone)

        if zone_facts is None:
            return None
        return zone_facts.to_simple_dict()

    except Exception as e:
        log.error(f"Error getting zone facts: {e}")
        return None


def get_zone_facts_by_account_id(account_id: str) -> list[dict] | None:
    """
    Uses the logic with the :class:`ZoneFacts` class to retrieve the Zone Details.

    This is a helper function and you can call ZoneFacts.query(account_id) directly
    without using this helper.

    zone_key = client + ':' + portfolio

    Args:
        account_id (str): The aws account ID

    Returns:
        list[dict] | None: The list of Zone Facts that are registered with this AWS Account ID.
    """
    try:
        zone_facts = ZoneFacts.query(account_id)
        if zone_facts is None:
            return None
        return [zf.to_simple_dict() for zf in zone_facts]

    except Exception as e:
        log.error(f"Error getting zone facts by account ID: {e}")
        return None


def get_app_facts(deployment_details: DeploymentDetails):
    """
    Retreives the Facs for DeploymentDetails that can be used in the Jinja2 Renederer
    to generate final Cloudformation Templates.

    Args:
        deployment_details (DeploymentDetails): The deployment Details of the TaskPayload

    Returns:
        _type_: _description_
    """
    client = deployment_details.Client
    if not client:
        raise ValueError("Client must be valid in DeploymentDetails")

    portfolio = deployment_details.Portfolio
    if not portfolio:
        raise ValueError("Portfolio must be valid in DeploymentDetails")

    app = deployment_details.App
    if not app:
        raise ValueError("App field must be popluated in DeploymentDetails")

    branch = deployment_details.BranchShortName
    if not branch:
        branch = "*"

    build = deployment_details.Build
    if not build:
        build = "*"

    portfolio_key = deployment_details.get_client_portfolio_key()
    app_test_string = f"prn:{portfolio}:{app}:{branch}:{build}"

    app_facts_list = AppFacts.query(portfolio_key)

    for app_facts in app_facts_list:
        arx = app_facts.AppRegex
        if re.match(arx, app_test_string):
            return app_facts.to_simple_dict()

    return None


def derrive_environment_from_branch(branch: str) -> tuple[str, str]:
    """Derrive the environmet and region alias from the branch name.

    Example of a branch name is **dev-sin** or **feature1/dev-sin**

    Where *dev* is the environment and *sin* is the region alias.

    Args:
        branch (str): The application deployment git repository branch name.

    Returns:
        (environmet, region_alias): The environment and region alias tuple
    """
    parts = branch.split("-")

    if len(parts) >= 2:
        branch = parts[0]

        # split the branch by '/' and retreive the last part
        branch_parts = branch.split("/")
        environment = branch_parts[
            -1
        ]  # in this format, the branch name is the environment (master, main, dev, feature1/dev, etc)
        region_alias = parts[
            1
        ]  # override region_alias fact with the branch region alias definition
    else:
        environment = branch
        region_alias = V_DEFAULT_REGION_ALIAS

    # If you are deploying a master branch, you are definitly PRODUCTION
    if environment == "master" or environment == "main":
        environment = V_DEFAULT_ENVIRONMENT

    return environment, region_alias


def format_contact(contact: dict) -> str:
    """
    Format the contact details for the Jinja2 template context.

    Args:
        contact (dict): The contact details

    Returns:
        dict: The formatted contact details
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


def get_store_url(
    bucket_name: str,
    bucket_region: str,
) -> str:

    store = util.get_storage_volume(bucket_region)

    sep = "/" if util.is_use_s3() else os.path.sep

    return sep.join([store, bucket_name])


def get_compiler_facts(dd: DeploymentDetails) -> dict:

    # Shared Files path separator
    sep = "/" if util.is_use_s3() else os.path.sep

    client = dd.Client

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
    Get the facts for a given app, portfolio, and zone.

    Args:
        client (str): The client FACTS database to query.
        portfolio (str): BizApp (Business Applicatino) slug/id
        app (str): BizApp Deployment unit slug/id
        branch (str | None, optional): Repository branch name of the Deployment Unit. Defaults to None.
        build (str | None, optional): Repository Tag or Commit ID of the Deployment Unit. Defaults to None.
        zone (str | None, optional): Landing Zone for the Deployment. Defaults to None.

    Raises:
        ValueError: For any inconsistency

    Returns:
        dict: The Jinja2 template context dictionary. (a.k.a FACTS)
    """
    client = deployment_details.Client

    # Get the dictionary of client facts dictionary for this deployment
    client_facts = get_client_facts(client)
    if not client_facts:
        raise ValueError(f"Client facts not found for {client}")

    # Get the portfolio facts dictionary for this deployment
    portfolio = deployment_details.Portfolio
    portfolio_facts = get_portfolio_facts(client, portfolio)
    if not portfolio_facts:
        raise ValueError(f"Portfolio facts not found for {client}:{portfolio}")

    # Get the app facts dictionary for this deployment
    identity = deployment_details.get_identity()
    app_facts = get_app_facts(deployment_details)
    if app_facts is None:
        raise ValueError(
            f"App facts not found for {identity}.  Contact DevOps to register this app."
        )

    # If the app facts do not contain a zone, throw an error
    zone = app_facts.get(ZONE_KEY, None)
    if not zone:
        raise ValueError(f"Zone not found for {identity}")

    # If the app facts do not contain a region, use the default region alias
    region_alias = app_facts.get(REGION, None)
    if not region_alias:
        raise ValueError(f"Region alias not found for {identity}")

    # if environment is not set, try to derrive it from the branch.  But facts ALWAYS come first.
    environment = app_facts.get(ENVIRONMENT, None)
    branch_region_alias = V_DEFAULT_REGION_ALIAS
    if not environment:
        environment, branch_region_alias = derrive_environment_from_branch(
            deployment_details.Branch or V_DEFAULT_REGION_ALIAS
        )

    # FACTS always override user input.  So, don't use the user input if FACTS are present.
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

    # Now that we ALL the facts, let's gather all the Tags for this deployment starting top down
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
            TAG_CONTACTS: ",".join(
                [format_contact(c) for c in portfolio_facts["Contacts"]]
            ),
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


def get_facts_flatend(deploymet_details: DeploymentDetails) -> dict[str, Any]:
    """
    Flatten the nested dictionary into a flat dictionary.

    NEW: TODO: This function is not used.  It is in incubtion to evaluate if it is needed.

    Args:
        facts (dict): The nested dictionary

    Returns:
        dict: The flat dictionary
    """
    flat_facts: dict[str, Any] = {}

    def flatten(d: dict, parent_key: str = ""):
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                flatten(v, new_key)
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    flatten(item, f"{new_key}.{i}")
            else:
                flat_facts[new_key] = v

    flatten(get_facts(deploymet_details))

    return flat_facts
