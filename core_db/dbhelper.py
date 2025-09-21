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

from typing import Any

import os
import core_logging as log

import core_framework as util

from core_framework.constants import (
    DD_ENVIRONMENT,
    DD_SCOPE,
    ENV_ENVIRONMENT,
    SCOPE_BRANCH,
    SCOPE_BUILD,
    SCOPE_COMPONENT,
    TR_STATUS,
    TR_RESPONSE,
)

from .actions import TableActions

from .item.portfolio.actions import PortfolioActions
from .item.app.actions import AppActions
from .item.branch.actions import BranchActions
from .item.build.actions import BuildActions
from .item.component.actions import ComponentActions

from .event.actions import EventActions

from .registry.client.actions import ClientActions as RegClientActions
from .registry.portfolio.actions import PortfolioActions as RegPortfolioActions
from .registry.app.actions import AppActions as RegAppActions
from .registry.zone.actions import ZoneActions as RegZoneActions

from .facter.actions import FactsActions

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


def update_status(prn: str, status: str, message: str | None = None, details: dict = {}) -> dict:
    """Updates the status of a PRN in the database.

    This function performs a comprehensive status update by:
    1. Logging the status change with structured logging
    2. Creating an event record in the events table
    3. Updating the item's status in the items table
    4. Adding environment information to the details

    Args:
        prn (str): Pipeline Reference Number identifying the item to update.
            Must be a valid PRN format (e.g., "build:acme:web-services:user-api:main:123")
        status (str): Status code from BuildStatus or other status constants.
            Common values include "success", "failure", "in_progress", "pending"
        message (str, optional): Text message describing the status change.
            Defaults to None.
        details (dict, optional): Additional item details to include with the status.
            Defaults to empty dict. Environment information is automatically added.

    Returns:
        dict: Result dictionary containing:
            - TR_STATUS: "ok" if successful, "error" if failed
            - TR_RESPONSE: Human-readable response message
            - MESSAGE: Error message if an exception occurred

    Examples:
        >>> # Update build status to success
        >>> result = update_status(
        ...     prn="build:acme:web-services:user-api:main:123",
        ...     status="success",
        ...     message="Build completed successfully",
        ...     details={"duration": "2m30s", "artifacts": ["lambda.zip"]}
        ... )
        >>> print(result)
        {'TR_STATUS': 'ok', 'TR_RESPONSE': 'Status updated'}

        >>> # Update component deployment status
        >>> result = update_status(
        ...     prn="component:acme:web-services:user-api:main:123:lambda",
        ...     status="deployed",
        ...     message="Lambda function deployed to production"
        ... )

        >>> # Update with failure status
        >>> result = update_status(
        ...     prn="build:acme:web-services:user-api:main:124",
        ...     status="failure",
        ...     message="Build failed due to test failures",
        ...     details={"failed_tests": 3, "error_log": "tests/output.log"}
        ... )
    """
    environment = os.getenv(ENV_ENVIRONMENT)

    # Try and set environment from config if not already set
    try:
        if DD_ENVIRONMENT not in details and environment:
            details[DD_ENVIRONMENT] = environment
    except Exception:
        pass

    log.status(
        status=status,
        reason=message,
        details={DD_SCOPE: util.get_prn_scope(prn), **details},
        identity=prn,
    )

    __api_put_event(prn, status, message)
    __api_update_status(prn, status, message)

    return {TR_STATUS: OK, TR_RESPONSE: "Status updated"}


def update_item(prn: str, **kwargs) -> dict:
    """Add or update an item in the database.

    This function updates an existing item or creates a new one if it doesn't exist.
    The appropriate table action class is determined from the PRN scope, and the
    update operation is delegated to that class.

    Args:
        prn (str): The Pipeline Reference Number identifying the item.
            Must be a valid PRN format that can be parsed to determine scope
        **kwargs: The item details to update. Available fields depend on the item type:
            - status (str): Current status of the item
            - name (str): Display name of the item
            - contact_email (str): Contact email for the item owner
            - Additional fields specific to the item type

    Returns:
        dict: The response from the update operation, typically containing:
            - TR_STATUS: "ok" if successful, "error" if failed
            - TR_RESPONSE: Human-readable response message
            - data: The updated item data (if successful)
            - MESSAGE: Error message (if failed)

    Raises:
        ValueError: If the PRN format is invalid or the scope cannot be determined
        ValueError: If the PRN scope is not supported by any registered action class

    Examples:
        >>> # Update a portfolio item
        >>> result = update_item(
        ...     prn="portfolio:acme:web-services",
        ...     status="active",
        ...     name="Web Services Portfolio",
        ...     contact_email="devops@acme.com"
        ... )

        >>> # Update a build with deployment info
        >>> result = update_item(
        ...     prn="build:acme:web-services:user-api:main:123",
        ...     status="deployed",
        ...     deployed_at="2025-01-01T12:00:00Z",
        ...     version="1.2.3"
        ... )

        >>> # Update component configuration
        >>> result = update_item(
        ...     prn="component:acme:web-services:user-api:main:123:lambda",
        ...     status="configured",
        ...     component_type="lambda",
        ...     runtime="python3.9"
        ... )

        >>> # Check result
        >>> if result["TR_STATUS"] == "ok":
        ...     print("Item updated successfully")
        ...     updated_data = result.get("data", {})
        ... else:
        ...     print(f"Update failed: {result.get('MESSAGE')}")
    """
    try:
        scope = util.get_prn_scope(prn)
        if not scope:
            raise ValueError(f"Cannot determine scope from PRN: '{prn}'")

        log.debug(f"(API) Updating item '{prn}' - {kwargs}")

        klazz = actions_routes.get(scope)
        if not klazz:
            raise ValueError(f"Unsupported PRN '{prn}', cannot determine DB class")

        kwargs[PRN] = prn
        result = klazz.update(**kwargs)

        if result.status != OK:
            log.error(f"Failed to update item '{prn}': {result.data}", identity=prn)

        return result.model_dump()

    except Exception as e:
        log.error(f"Failed to update item '{prn}'", identity=prn)
        return {TR_STATUS: ERROR, TR_RESPONSE: "Failed to update item", MESSAGE: str(e)}


def register_item(prn: str, name: str, **kwargs) -> dict:
    """Creates a new item in the database.

    This function registers a new deployment item based on the PRN scope. It automatically
    sets up the hierarchical relationships (parent_prn, app_prn, etc.) based on the PRN
    format and item type.

    Args:
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

    Examples:
        >>> # Register a new branch
        >>> result = register_item(
        ...     prn="branch:acme:web-services:user-api:feature-auth",
        ...     name="feature-auth",
        ...     short_name="feature-auth",
        ...     status="active"
        ... )

        >>> # Register a new build
        >>> result = register_item(
        ...     prn="build:acme:web-services:user-api:main:125",
        ...     name="Build #125",
        ...     status="building",
        ...     commit_sha="abc123def456"
        ... )

        >>> # Register a new component
        >>> result = register_item(
        ...     prn="component:acme:web-services:user-api:main:125:lambda",
        ...     name="User API Lambda",
        ...     component_type="lambda",
        ...     status="pending"
        ... )

        >>> # Check registration result
        >>> if result["TR_STATUS"] == "ok":
        ...     print("Item registered successfully")
        ...     item_data = result.get("data", {})
        ... else:
        ...     print(f"Registration failed: {result.get('MESSAGE')}")

        >>> # Register with additional metadata
        >>> result = register_item(
        ...     prn="component:acme:web-services:user-api:main:125:api",
        ...     name="User API Gateway",
        ...     component_type="api",
        ...     contact_email="api-team@acme.com",
        ...     runtime="nodejs18.x"
        ... )
    """
    try:
        scope = util.get_prn_scope(prn)
        if not scope:
            raise ValueError(f"Cannot determine scope from PRN: '{prn}'")

        if scope == SCOPE_BRANCH:
            data = {"app_prn": ":".join(prn.split(":")[0:3]), "name": name}
        elif scope == SCOPE_BUILD:
            data = {"branch_prn": ":".join(prn.split(":")[0:4]), "name": name}
        elif scope == SCOPE_COMPONENT:
            data = {
                "build_prn": ":".join(prn.split(":")[0:5]),
                "name": name,
                "component_type": kwargs["component_type"],
            }
        else:
            raise ValueError(f"Unsupported SCOPE '{scope}'. Must be branch, build or component")

        if kwargs:
            data = {**data, **kwargs}

        # Register the item (may not be required if it already exists)
        log.debug(f"(API) registering {scope} '{prn}' {kwargs.get(STATUS, '')}", identity=prn)

        klazz = actions_routes.get(scope)
        if not klazz:
            raise ValueError(f"Unsupported PRN '{prn}', cannot determine DB class")

        data[PRN] = prn
        result = klazz.create(**data)

        if result.status != OK:
            log.error(f"Failed to register item '{prn}':", details=result.data, identity=prn)

        return result.model_dump()

    except Exception as e:
        log.error(f"Failed to register item '{prn}'", identity=prn)
        return {
            TR_STATUS: ERROR,
            TR_RESPONSE: "Failed to register item",
            MESSAGE: str(e),
        }


def __api_update_status(prn: str, status: str, message: str | None = None) -> dict:
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
    try:
        scope = util.get_prn_scope(prn)
        if not scope:
            raise ValueError(f"Cannot determine scope from PRN '{prn}'")

        if not scope:
            raise ValueError(f"Unsupported PRN '{prn}', cannot update API")

        log.debug(
            f"(API) Setting status of {scope} '{prn}' to {status} ({message})",
            identity=prn,
        )

        data = {PRN: prn, STATUS: status, "message": message}

        klazz = actions_routes.get(scope)
        if not klazz:
            log.error(f"Unsupported PRN '{prn}', cannot update API", identity=prn)
            return {TR_STATUS: ERROR, TR_RESPONSE: "Unsupported PRN"}

        result = klazz.update(**data)

        if result.status != OK:
            log.error(f"Failed to update status of '{prn}': {result.data}", identity=prn)

        return result.model_dump()

    except Exception as e:
        log.error(f"Failed to create event '{prn}'", identity=prn)
        return {
            TR_STATUS: ERROR,
            TR_RESPONSE: "Failed to create event",
            MESSAGE: str(e),
        }


def __api_put_event(prn: str, status: str, message: str | None = None) -> dict:
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
        log.debug(f"(API) New event: {prn} - {status} - {message}", identity=prn)

        data = {PRN: prn, STATUS: status, MESSAGE: message}

        klazz = actions_routes["event"]

        result = klazz.create(**data)

        if result.status != OK:
            log.error(f"Failed to create event '{prn}':", details=result.data, identity=prn)

        return result.model_dump()

    except Exception as e:
        log.error(f"Failed to create event '{prn}'", identity=prn)
        return {
            TR_STATUS: ERROR,
            TR_RESPONSE: "Failed to create event",
            MESSAGE: str(e),
        }
