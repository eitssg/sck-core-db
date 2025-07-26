from typing import Optional
import core_framework as util
from core_framework.constants import V_CORE_AUTOMATION
from .constants import (
    CLIENT_FACTS,
    PORTFOLIO_FACTS,
    ZONE_FACTS,
    APP_FACTS,
    ITEMS,
    EVENTS,
)


def get_table_name(name: str, client: str = None, default: Optional[str] = None) -> str:
    """Get the name of a table from the tables dictionary"""

    if not client:
        client = util.get_client() or "client"
    prefix = util.get_automation_scope() or ""

    tables = {
        # These tables or for the CORE system automation engine
        CLIENT_FACTS: f"{prefix}{V_CORE_AUTOMATION}-clients",
        PORTFOLIO_FACTS: f"{prefix}{V_CORE_AUTOMATION}-portfolios",
        ZONE_FACTS: f"{prefix}{V_CORE_AUTOMATION}-zones",
        APP_FACTS: f"{prefix}{V_CORE_AUTOMATION}-apps",
        # WARNING:You must isolate item/events by client and each client
        # must have their own table.  Cilent should come in on the API
        # call.  So, you don't want to use these defaults.
        ITEMS: f"{prefix}{client}-{V_CORE_AUTOMATION}-items",
        EVENTS: f"{prefix}{client}-{V_CORE_AUTOMATION}-events",
    }

    # We may also want to first check if an environment variable is set
    # and if so, use that value instead of the default

    table = tables.get(name, default)
    if table is None:
        raise ValueError(f"Table name not found for {name}")

    return table


def get_clients_table_name() -> str:
    """Get the name of the client table"""
    return get_table_name(CLIENT_FACTS)


def get_apps_table_name() -> str:
    """Get the name of the app table"""
    return get_table_name(APP_FACTS)


def get_zones_table_name() -> str:
    """Get the name of the zone table"""
    return get_table_name(ZONE_FACTS)


def get_portfolios_table_name() -> str:
    """Get the name of the portfolio table"""
    return get_table_name(PORTFOLIO_FACTS)


def get_items_table_name() -> str:
    """Get the name of the item table"""
    return get_table_name(ITEMS)


def get_events_table_name() -> str:
    """Get the name of the event table"""
    return get_table_name(EVENTS)
