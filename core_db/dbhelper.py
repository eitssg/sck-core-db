"""A set of helper functions that write and update item records status values in the DB

THe class also provides a mapping of names to classes to allow for the development of
a single interface to the DB for all the different types of items that can be stored in the DB.

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
    # Evants and Status
    "event": EventActions,
    # Facts.  Think of Facts as a DB "View" on the registry
    "facts": FactsActions,
    # Registry
    "registry:client": RegClientActions,
    "registry:portfolio": RegPortfolioActions,
    "registry:app": RegAppActions,
    "registry:zone": RegZoneActions,
}
""" TableActionType: A dictionary that maps the action prefix to the class that will handle the action

Values are classes that implement the TableActions interface:

    Items Table or Schema Names:

        * portfolio
        * app
        * branch
        * build
        * component

    Event Table or Schema Names:
        * event

    Registry Table or Schema Names:

        * registry:client
        * registry:portfolio
        * registry:app
        * registry:zone

    Facts View Name:

        * facts

    This name, concatenated with list, get, create, update, delete, will be used to route the action to the correct class.

    For example, to get a list of items from the portfolio table, the action would be:

        * "portfolio:list"  -> PortfolioActions.list()
        * "portfolio:get"   -> PortfolioActions.get()

    The class must implement the TableActions interface.

"""


def update_status(
    prn: str, status: str, message: str | None = None, details={}
) -> dict:
    """
    Updates the status of a PRN in the DB.

    :param prn: Pipeline Reference Number.
    :type prn: str
    :param status: Status Code from :class:`BuildStatus`.
    :type status: str
    :param message: Text Message. Defaults to None.
    :type message: str or None
    :param details: Item Details. Defaults to {}.
    :type details: dict
    :return: The item's details after the update.
    :rtype: dict
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
    """
    Add or update an item in the DB.

    :param prn: The Pipeline Reference Number.
    :type prn: str
    :param kwargs: The item details.
    :type kwargs: dict
    :raises ValueError: If the data is invalid.
    :return: The item after it has been updated/saved.
    :rtype: dict
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
    """
    Creates a new item in the DB.

    :param prn: The Pipeline Reference Number.
    :type prn: str
    :param name: The Name of the item.
    :type name: str
    :param kwargs: Additional item data.
    :type kwargs: dict
    :raises ValueError: If the item data is invalid.
    :return: The item after it has been created.
    :rtype: dict
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
            raise ValueError(
                f"Unsupported SCOPE '{scope}'. Must be branch, build or component"
            )

        if kwargs:
            data = {**data, **kwargs}

        # Register the branch (may not be required)
        log.debug(
            f"(API) registering {scope} '{prn}' {kwargs.get(STATUS, '')}", identity=prn
        )

        klazz = actions_routes.get(scope)
        if not klazz:
            raise ValueError(f"Unsupported PRN '{prn}', cannot determine DB class")

        data[PRN] = prn
        result = klazz.create(**data)

        if result.status != OK:
            log.error(
                f"Failed to register item '{prn}':", details=result.data, identity=prn
            )

        return result.model_dump()

    except Exception as e:
        log.error(f"Failed to register item '{prn}'", identity=prn)
        return {
            TR_STATUS: ERROR,
            TR_RESPONSE: "Failed to register item",
            MESSAGE: str(e),
        }


def __api_update_status(prn: str, status: str, message: str | None = None) -> dict:
    """
    Internal helper to update the status of an item via the API.

    :param prn: Pipeline Reference Number.
    :type prn: str
    :param status: Status Code.
    :type status: str
    :param message: Optional message.
    :type message: str or None
    :return: The result of the update.
    :rtype: dict
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
            log.error(
                f"Failed to update status of '{prn}': {result.data}", identity=prn
            )

        return result.model_dump()

    except Exception as e:
        log.error(f"Failed to create event '{prn}'", identity=prn)
        return {
            TR_STATUS: ERROR,
            TR_RESPONSE: "Failed to create event",
            MESSAGE: str(e),
        }


def __api_put_event(prn: str, status: str, message: str | None = None) -> dict:
    """
    Internal helper to create a new event in the DB via the API.

    :param prn: Pipeline Reference Number.
    :type prn: str
    :param status: Status Code.
    :type status: str
    :param message: Optional message.
    :type message: str or None
    :return: The result of the event creation.
    :rtype: dict
    """
    try:
        log.debug(f"(API) New event: {prn} - {status} - {message}", identity=prn)

        data = {PRN: prn, STATUS: status, MESSAGE: message}

        klazz = actions_routes["event"]

        result = klazz.create(**data)

        if result.status != OK:
            log.error(
                f"Failed to create event '{prn}':", details=result.data, identity=prn
            )

        return result.model_dump()

    except Exception as e:

        log.error(f"Failed to create event '{prn}'", identity=prn)
        return {
            TR_STATUS: ERROR,
            TR_RESPONSE: "Failed to create event",
            MESSAGE: str(e),
        }
