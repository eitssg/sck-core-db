"""A set of helper functions that write and update item records status values in the DB.

The class also provides a mapping of names to classes to allow for the development of
a single interface to the DB for all the different types of items that can be stored in the DB.

This module serves as a high-level abstraction layer over the core-db table actions,
providing simplified functions for common database operations like status updates,
item registration, and event creation.

Functions:
    update_status: Updates the status of a PRN in the database
    update_item: Add or update an item in the database
    register_item: Creates a new item in the database

Action Routing:
    The module includes an action routing dictionary that maps action prefixes to their
    corresponding TableActions implementation classes. This enables dynamic routing
    of database operations based on the item type or table scope.

Examples:
    >>> # Update status of a build
    >>> result = update_status(
    ...     prn="build:acme:web-services:user-api:main:123",
    ...     status="success",
    ...     message="Build completed successfully"
    ... )

    >>> # Register a new branch
    >>> result = register_item(
    ...     prn="branch:acme:web-services:user-api:feature-auth",
    ...     name="feature-auth",
    ...     short_name="feature-auth"
    ... )

    >>> # Update item data
    >>> result = update_item(
    ...     prn="component:acme:web-services:user-api:main:123:lambda",
    ...     status="deployed",
    ...     component_type="lambda"
    ... )
"""

from typing import Any, ChainMap

import core_logging as log

from core_framework.models import DeploymentDetails

from core_framework.constants import (
    SCOPE_PORTFOLIO,
    SCOPE_APP,
    SCOPE_BRANCH,
    SCOPE_BUILD,
    SCOPE_COMPONENT,
)

from .actions import TableActions

from .item.portfolio.actions import PortfolioActions
from .item.app.actions import AppActions
from .item.branch.actions import BranchActions
from .item.build.actions import BuildActions
from .item.component.actions import ComponentActions
from .item.models import ItemModelRecord

from .event.actions import EventActions
from .event.models import EventItem

from .registry.client.actions import ClientActions as RegClientActions
from .registry.portfolio.actions import PortfolioActions as RegPortfolioActions
from .registry.app.actions import AppActions as RegAppActions
from .registry.zone.actions import ZoneActions as RegZoneActions

from .facter.actions import FactsActions

from .exceptions import NotFoundException, ConflictException

PRN = "prn"
STATUS = "status"
ERROR = "error"
OK = "ok"
MESSAGE = "message"

# the key to this dictionary is an "action prefix name"
# Actions will come n as "prefix:action" and the prefix will be used to route the action
# to the correct class
TableActionType = dict[str, TableActions | Any]

actions_routes: TableActionType = {
    # Old Names
    "portfolio": PortfolioActions,
    "app": AppActions,
    "branch": BranchActions,
    "build": BuildActions,
    "component": ComponentActions,
    # New Names
    "item:portfolio": PortfolioActions,
    "item:app": AppActions,
    "item:branch": BranchActions,
    "item:build": BuildActions,
    "item:component": ComponentActions,
    # Events and Status
    "event": EventActions,
    # Facts.  Think of Facts as a DB "View" on the registry
    "facts": FactsActions,
    # Registry
    "registry:client": RegClientActions,
    "registry:portfolio": RegPortfolioActions,
    "registry:app": RegAppActions,
    "registry:zone": RegZoneActions,
}
"""A dictionary that maps the action prefix to the class that will handle the action.

Values are classes that implement the TableActions interface for different table types:

**Items Table or Schema Names:**
- portfolio: Portfolio deployment items
- app: Application deployment items  
- branch: Branch deployment items
- build: Build deployment items
- component: Component deployment items

**Event Table or Schema Names:**
- event: Deployment events and status updates

**Registry Table or Schema Names:**
- registry:client: Client organization registry
- registry:portfolio: Portfolio configuration registry
- registry:app: Application configuration registry
- registry:zone: Zone configuration registry

**Facts View Name:**
- facts: Database "view" on the registry for consolidated queries

**Action Routing:**
This name, concatenated with list, get, create, update, delete, will be used to route 
the action to the correct class.

Examples:
    >>> # Portfolio operations
    >>> actions_routes["portfolio"].list()  # PortfolioActions.list()
    >>> actions_routes["portfolio"].get()   # PortfolioActions.get()
    
    >>> # Registry operations  
    >>> actions_routes["registry:client"].create()  # RegClientActions.create()
    >>> actions_routes["registry:zone"].update()    # RegZoneActions.update()
    
    >>> # Event operations
    >>> actions_routes["event"].create()  # EventActions.create()

Note:
    The class must implement the TableActions interface to be compatible with this routing system.
"""


def update_status(
    scope: str,
    deployment_details: DeploymentDetails,
    *,
    status: str | None = None,
    message: str | None = None,
    details: dict | None = None,
) -> None:
    """Updates the status of a PRN in the database.  If it doesn't throw an expection, it worked."""

    __api_put_event(scope, deployment_details, status=status, message=message, details=details)
    __api_update_status(scope, deployment_details, status=status, message=message)


def update_item(scope: str, deployment_details: DeploymentDetails, metadata: dict | None = None, **kwargs) -> ItemModelRecord:
    """Add or update an item in the database.

    This function updates an existing item or creates a new one if it doesn't exist.
    The appropriate table action class is determined from the PRN scope, and the
    update operation is delegated to that class.

    Args:
        scope (str): The scope of the item to update. Must be one of:
            - portfolio
            - app
            - branch
            - build
            - component
        deployment_details (DeploymentDetails): The deployment details containing client, portfolio, app, branch,
        status (str): Current status of the item
        name (str): Display name of the item
        contact_email (str): Contact email for the item owner
        metadata (dict): Medatadata data
        **kwargs: Additional item data specific to the item type

    Returns:
        ItemModelRecord: The updated item record

    Raises:
        ValueError: If the PRN format is invalid or the scope cannot be determined
        ValueError: If the PRN scope is not supported by any registered action class


    """
    try:
        client = deployment_details.client

        prn, _ = __get_prn_and_name(scope, deployment_details)

        log.debug(f"(API) Updating item '{prn}'")

        klazz = actions_routes.get(f"item:{scope}")
        if not klazz:
            raise ValueError(f"Unsupported PRN '{prn}', cannot determine DB class")

        try:
            log.debug(f"Checking if item '{prn}' exists")
            result: ItemModelRecord = klazz.get(client=client, prn=prn)
            if metadata:
                log.debug(f"Updating metadata for item '{prn}'", details=metadata)
                result.metadata = metadata
            data = result.model_dump(by_alias=False, mode="json")  # dates will be converted to ISO strings
            data.update(kwargs)  # update only top-level keys.  no deep merge.
            log.debug(f"Item '{prn}' exists, updating")
            result = klazz.update(client=client, **data)
            log.debug(f"Item '{prn}' updated")
            return result
        except NotFoundException:
            log.debug(f"Item '{prn}' does not exist, bailing out...")
            return None

    except Exception as e:
        log.error(f"Failed to update item '{prn}'")
        raise


def __get_prn_and_name(scope: str, deployment_details: DeploymentDetails) -> tuple[str, str]:
    """Helper to get the PRN and name from the deployment details based on scope."""
    if scope == SCOPE_PORTFOLIO:
        return deployment_details.get_portfolio_prn(), deployment_details.portfolio
    elif scope == SCOPE_APP:
        return deployment_details.get_app_prn(), deployment_details.app
    elif scope == SCOPE_BRANCH:
        return deployment_details.get_branch_prn(), deployment_details.branch
    elif scope == SCOPE_BUILD:
        return deployment_details.get_build_prn(), deployment_details.build
    elif scope == SCOPE_COMPONENT:
        return deployment_details.get_component_prn(), deployment_details.component
    else:
        raise ValueError(f"Unsupported SCOPE '{scope}'. Must be branch, build or component")


def register_item(
    scope: str, deployment_details: DeploymentDetails, *, status: str | None = None, component_type: str | None = None, **kwargs
) -> ItemModelRecord | None:
    """Creates (Or Updates) an item in the database.

    This function registers a new deployment item based on the PRN scope. It automatically
    sets up the hierarchical relationships (parent_prn, app_prn, etc.) based on the PRN
    format and item type.

    Parameters:
        prn (str): The Pipeline Reference Number for the new item.
            Must be a valid PRN format that indicates the item type and hierarchy
        name (str): The display name of the item.
            Human-readable name for identification in UIs and logs
        **kwargs: Additional item data specific to the item type:
            - component_type (str): Required for component items (e.g., "lambda", "api")
            - status (str): Initial status of the item
            - contact_email (str): Contact email for the item owner
            - Additional fields as supported by the item type

    Returns:
        dict: The response from the creation operation, containing:
            - TR_STATUS: "ok" if successful, "error" if failed
            - TR_RESPONSE: Human-readable response message
            - data: The created item data (if successful)
            - MESSAGE: Error message (if failed)

    Raises:
        ValueError: If the PRN format is invalid or scope cannot be determined
        ValueError: If the scope is not supported (must be branch, build, or component)
        ValueError: If required fields are missing (e.g., component_type for components)

    Note:
        **Supported Scopes:**
        - **branch**: Creates a branch item with app_prn reference
        - **build**: Creates a build item with branch_prn reference
        - **component**: Creates a component item with build_prn reference (requires component_type)

        **Automatic Relationships:**
        The function automatically sets up parent relationships:
        - Branch: Sets app_prn from first 3 PRN segments
        - Build: Sets branch_prn from first 4 PRN segments
        - Component: Sets build_prn from first 5 PRN segments


    """
    try:
        client = deployment_details.client

        prn, name = __get_prn_and_name(scope, deployment_details)

        data = {"prn": prn, "name": name}
        if status is not None:
            data["status"] = status
        if component_type is not None and scope == SCOPE_COMPONENT:
            data["component_type"] = component_type
        data = ChainMap(data, kwargs)

        # Register the item (may not be required if it already exists)
        log.debug(f"(API) registering {scope} '{prn}' {kwargs.get(STATUS, '')}", identity=prn)

        klazz = actions_routes.get(f"item:{scope}")
        if not klazz:
            raise ValueError(f"Unsupported PRN '{prn}', cannot determine DB class")

        try:
            log.debug(f"Checking if item '{prn}' exists")
            item_record: ItemModelRecord = klazz.get(client=client, prn=prn)
            log.debug(f"Item '{prn}' exists, updating")
            item_record = klazz.update(client=client, prn=prn, **data)
        except NotFoundException:
            log.debug(f"Item '{prn}' does not exist, creating")
            item_record = klazz.create(client=client, **data)
            log.debug(f"Item '{prn}' created")

        return item_record

    except ConflictException as e:
        log.warning(f"Conflict when registering item '{prn}': {e}", identity=prn)
        raise
    except Exception as e:
        log.error(f"Failed to register item '{prn}'", identity=prn)
        raise


def __api_update_status(
    scope, deployment_details: DeploymentDetails, *, status: str | None, message: str | None = None, **kwargs
) -> ItemModelRecord:
    """Internal helper to update the status of an item via the API.

    This is a private function used internally by update_status() to handle the
    actual item status update in the database.

    Args:
        prn (str): Pipeline Reference Number identifying the item
        status (str): Status code to set on the item
        message (str, optional): Optional status message. Defaults to None.

    Returns:
        dict: The result of the update operation containing TR_STATUS and TR_RESPONSE

    Examples:
        >>> # This is an internal function, typically called by update_status()
        >>> result = __api_update_status(
        ...     prn="build:acme:web-services:user-api:main:123",
        ...     status="success",
        ...     message="Build completed"
        ... )
    """
    client = deployment_details.client

    prn, _ = __get_prn_and_name(scope, deployment_details)

    log.debug(f"(API) Setting status of {scope} '{prn}' to {status} ({message})")

    data = {"prn": prn}
    if status:
        data["status"] = status
    if message:
        data["message"] = message  # message will be saved if the recordType (klazz) has the attribute.  or it is ignored.

    klazz = actions_routes.get(f"item:{scope}")
    if not klazz:
        log.error(f"Unsupported scope '{scope}' for PRN '{prn}'")
        raise ValueError(f"Unsupported PRN '{prn}', cannot determine DB class")

    try:
        log.debug(f"Updating item '{prn}' to status '{status}'")
        result = klazz.patch(client=client, **data)
        log.debug(f"Item '{prn}' updated to status '{status}'")
        return result
    except NotFoundException:
        log.error(f"Item '{prn}' not found when updating status to '{status}'", identity=prn)
        return None
    except Exception:
        log.error(f"Failed to update status of item '{prn}' to '{status}'", identity=prn)
        raise


def __api_put_event(
    scope: str, deployment_details: DeploymentDetails, status: str, message: str | None = None, details: dict | None = None
) -> EventItem | None:
    """Internal helper to create a new event in the database via the API.

    This is a private function used internally by update_status() to create
    an event record in the events table for audit and monitoring purposes.

    Args:
        prn (str): Pipeline Reference Number for the event
        status (str): Status code for the event
        message (str, optional): Optional event message. Defaults to None.

    Returns:
        dict: The result of the event creation containing TR_STATUS and TR_RESPONSE

    Examples:
        >>> # This is an internal function, typically called by update_status()
        >>> result = __api_put_event(
        ...     prn="build:acme:web-services:user-api:main:123",
        ...     status="success",
        ...     message="Build completed successfully"
        ... )
    """
    try:
        client = deployment_details.client

        prn, name = __get_prn_and_name(scope, deployment_details)

        log.debug(f"(API) New event: {prn} - {status} - {message}")

        data = {"prn": prn, "status": status.upper()}
        if message:
            data["message"] = message

        return EventActions.create(client=client, **data)

    except Exception:
        log.error(f"Failed to create event '{prn}'")
        raise
