"""
The Factor object is the "FACTS" database.  This object is DEPRECATED and should not be used.
This FACTS database should come from DynamoDB.  Not 'accounts.yaml' and 'apps.yaml' files.

(In re-rewrite.  We need to use DynamoDB instead of FACTS YAML files)
"""

import re
import core_framework as util
import core_logging as log

from core_framework.constants import (
    DD_TAGS,
    FACTS_ACCOUNT,
    FACTS_REGION,
    FACTS_TAGS,
    TAG_ENVIRONMENT,
    TAG_OWNER,
    TAG_REGION,
    TAG_CONTACTS,
    V_DEFAULT_BRANCH,
    V_DEFAULT_ENVIRONMENT,
    V_DEFAULT_REGION_ALIAS,
    V_EMPTY,
)

from core_framework.models import DeploymentDetails

from ..constants import APPROVERS, CONTACTS, OWNER, REGION, ENVIRONMENT, ZONE_KEY

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


def get_zone_facts(client: str, portfolio: str, zone: str) -> dict | None:
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

        zone_key = f"{client}:{portfolio}"
        zone_facts = ZoneFacts.get(zone_key, zone)

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


def get_deployment_details_facts(deployment_details: DeploymentDetails):
    """
    Retreives the Facs for DeploymentDetails that can be used in the Jinja2 Renederer
    to generate final Cloudformation Templates.

    Args:
        deployment_details (DeploymentDetails): The deployment Details of the TaskPayload

    Returns:
        _type_: _description_
    """
    if deployment_details.Client is None:
        raise ValueError("Client must be valid in DeploymentDetails")

    if deployment_details.App is None:
        raise ValueError("App field must be popluated in DeploymentDetails")

    return get_app_facts(
        deployment_details.Client,
        deployment_details.Portfolio,
        deployment_details.App,
        deployment_details.BranchShortName,
        deployment_details.Build,
    )


def get_app_facts(
    client: str,
    portfolio: str,
    app: str,
    branch: str | None = None,
    build: str | None = None,
) -> dict | None:
    """
    Retrieves the AppFacts data stored in the registry that match the sepecified deployment details.

    .. warning::

        Matches are performed by searching the AppRegEx in the App Registry table core-automation-apps
        to the value f"prn:{portfolio}:{app}:{branch}:{build}"

        This function will return the FIRST match and order is NOT guaranteed.


    Args:
        client (str): The client that the facts are stored in
        portfolio (str): The portfolio within the specified client
        app (str): The app deployment unit within the portfolio
        branch (str | None, optional): The branch name of the app repository. Defaults to None.
        build (str | None, optional): The current version, build ID, or commit Id. Defaults to None.

    Returns:
        dict | None: The FACTS context ready for Jinja2 rendering.
    """

    if branch is None:
        branch = "*"

    if build is None:
        build = "*"

    portfolio_key = f"{client}:{portfolio}"
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


# Why don't we use botocore deep_merge instead of util.merge.deep_merge?  It's the same thing. Is it?
# from botocore.utils import deep_merge as deep_merge


def get_facts_by_identity(client: str, identity: str) -> dict:
    """
    Retreives Facts based on the supplied client and Pipeline Reference Number

    Args:
        client (str): The cilent where this portfilio is deployed
        identity (str): The Pipeline Reference Number

    Returns:
        dict: The Facts context ready for Jinja2 rendering.
    """
    portfolio, app, branch, build, _ = util.split_prn(identity)
    return get_facts(client, portfolio or "unknown", app or "unknown", branch, build)


def format_contact(contact: dict) -> str:
    """
    Format the contact details for the Jinja2 template context.

    Args:
        contact (dict): The contact details

    Returns:
        dict: The formatted contact details
    """
    name = contact.get("name", "")
    email = contact.get("email", "")
    if not name and not email:
        return V_EMPTY
    if not name:
        return email
    if not email:
        return name
    return f"{name} <{email}>"


def get_facts(  # noqa: C901
    client: str,
    portfolio: str,
    app: str,
    branch: str | None = None,
    build: str | None = None,
    zone: str | None = None,
) -> dict:
    """
    Get the facts for a given app, portfolio, and zone.

    TODO: This function is too long and should be refactored.  And, portfolio and app should bo optional.

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

    if branch is None:
        branch = V_DEFAULT_BRANCH

    app_facts = get_app_facts(client, portfolio, app, branch, build)

    if app_facts is None:
        raise ValueError(
            f"App facts not found for prn:{client}:{portfolio}:{app}:{branch}:{build}"
        )

    # If the app facts do not contain a region, use the default region alias
    region_alias = app_facts.get(REGION, None)

    # if environment is not set, try to derrive it from the branch.  But facts ALWAYS come first.
    environment = app_facts.get(ENVIRONMENT, None)
    branch_region_alias = V_DEFAULT_REGION_ALIAS
    if not environment:
        environment, branch_region_alias = derrive_environment_from_branch(branch)

    # FACTS always override user input.  So, don't use the user input if FACTS are present.
    if region_alias is None:
        region_alias = branch_region_alias

    # If the app doen't have an environment tag or a region tag, add it
    app_tags = app_facts.get(DD_TAGS, {})
    if TAG_ENVIRONMENT not in app_tags:
        app_tags[TAG_ENVIRONMENT] = environment
    if TAG_REGION not in app_tags:
        app_tags[TAG_REGION] = region_alias

    portfolio_facts = get_portfolio_facts(client, portfolio)
    if portfolio_facts is None:
        raise ValueError(f"Portfolio facts not found for {client}-{portfolio}")

    if "owner" in portfolio_facts and TAG_OWNER not in app_tags:
        app_tags[TAG_OWNER] = format_contact(portfolio_facts["owner"])
    if "contacts" in portfolio_facts:
        app_tags[TAG_CONTACTS] = ",".join(
            [format_contact(c) for c in portfolio_facts["contacts"]]
        )

    # If a zone is not explicitely provded, we will generate the zone name from the portfolio and environment
    # Remember, all "apps/deployments" go inside the same environment of the portfololiw (a.k.a landing zone)
    zone = app_facts.get(ZONE_KEY, None)

    # if the app facts have a zone, use it. It really must. It's required.
    if zone is None:
        zone = f"{portfolio}-{environment}"

    # If your zone has not been registered, contact DevOps to register it.  Retrieve the facts from the registry.
    zone_facts = get_zone_facts(client, portfolio, zone)

    if zone_facts is None or app_facts is None:
        raise ValueError(
            f"Account or app facts not found for {client}-{portfolio}-{app}"
        )

    # Merge in the zone tags into the app tags
    zone_tags = zone_facts.get(FACTS_TAGS, {})
    for key, value in zone_tags.items():
        if key not in app_tags:
            app_tags[key] = value

    if FACTS_ACCOUNT not in zone_facts or FACTS_REGION not in zone_facts:
        raise ValueError(f"Account or region facts not found for {zone}")

    # Extract account facts and region-specific facts
    account_facts = zone_facts[FACTS_ACCOUNT]
    region_facts = zone_facts[FACTS_REGION].get(region_alias, None)

    if region_facts is None:
        raise ValueError(f"Region {region_alias} has not been enabled for {zone}")

    # Merge account facts and region-specific facts into facts dict
    facts = util.merge.deep_merge(account_facts, region_facts, merge_lists=True)

    # Merge app facts into facts dict
    facts = util.merge.deep_merge(facts, app_facts, merge_lists=True)

    if APPROVERS not in facts:
        facts[APPROVERS] = portfolio_facts.get("approvers", [])
    if CONTACTS not in facts:
        facts[CONTACTS] = portfolio_facts.get("contacts", [])
    if OWNER not in facts and "owner" in portfolio_facts:
        facts[OWNER] = portfolio_facts.get("owner")

    return facts
