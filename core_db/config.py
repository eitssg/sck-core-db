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
        # Client Facts is the base tenant registration table (no "client" prefix)
        CLIENT_FACTS: f"{prefix}{V_CORE_AUTOMATION}-clients",
        # AWS Account(s) and zone names
        ZONE_FACTS: f"{prefix}{client}-{V_CORE_AUTOMATION}-zones",
        # Portflio BizApps / Deploypment App targets
        PORTFOLIO_FACTS: f"{prefix}{client}-{V_CORE_AUTOMATION}-portfolios",
        # The application zone selectors (App Registry)
        APP_FACTS: f"{prefix}{client}-{V_CORE_AUTOMATION}-apps",
        # Components and Items deployed to AWS
        ITEMS: f"{prefix}{client}-{V_CORE_AUTOMATION}-items",
        # All the events that are generated duing deployment
        EVENTS: f"{prefix}{client}-{V_CORE_AUTOMATION}-events",
    }

    # We may also want to first check if an environment variable is set
    # and if so, use that value instead of the default

    table = tables.get(name, default)
    if table is None:
        raise ValueError(f"Table name not found for {name}")

    return table
