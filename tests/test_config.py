import pytest

import core_framework as util

from core_db.config import V_CORE_AUTOMATION, get_table_name

from core_db.registry.client import ClientFactsModel
from core_db.registry.zone import ZoneFactsModel
from core_db.registry.portfolio import PortfolioFactsModel
from core_db.registry.app import AppFactsModel

from core_db.item import ItemModel, PortfolioModel, AppModel, BranchModel, BuildModel, ComponentModel

from core_db.event import EventModel
from core_db.oauth import AuthorizationsModel, RateLimitsModel, OAuthTableModel, ForgotPasswordModel
from core_db.passkey import PassKeysModel
from core_db.profile import ProfileModel
from core_db.audit import AuthAuditModel


client = "core"

prefix = util.get_automation_scope() or ""

tables = {
    #
    # Global tables
    #
    # OAuth Authorizations Table
    AuthorizationsModel: f"{prefix}core-{V_CORE_AUTOMATION}-oauth",
    RateLimitsModel: f"{prefix}core-{V_CORE_AUTOMATION}-oauth",
    OAuthTableModel: f"{prefix}core-{V_CORE_AUTOMATION}-oauth",
    ForgotPasswordModel: f"{prefix}core-{V_CORE_AUTOMATION}-oauth",
    # Passkeys / WebAuthn Table
    PassKeysModel: f"{prefix}core-{V_CORE_AUTOMATION}-passkeys",
    # Client Facts is the base tenant registration table (no "client" prefix)
    ClientFactsModel: f"{prefix}core-{V_CORE_AUTOMATION}-clients",
    #
    # Tenant aware tables
    #
    # Profiles for user-defined configurations
    ProfileModel: f"{prefix}{client}-{V_CORE_AUTOMATION}-profiles",
    # Authorization audit events
    AuthAuditModel: f"{prefix}{client}-{V_CORE_AUTOMATION}-auth-audit",
    # AWS Account(s) and zone names
    ZoneFactsModel: f"{prefix}{client}-{V_CORE_AUTOMATION}-zones",
    # Portfolio BizApps / Deployment App targets
    PortfolioFactsModel: f"{prefix}{client}-{V_CORE_AUTOMATION}-portfolios",
    # The application zone selectors (App Registry)
    AppFactsModel: f"{prefix}{client}-{V_CORE_AUTOMATION}-apps",
    # Components and Items deployed to AWS
    ItemModel: f"{prefix}{client}-{V_CORE_AUTOMATION}-items",
    # All the portfolio deployment items
    PortfolioModel: f"{prefix}{client}-{V_CORE_AUTOMATION}-items",
    # All the app deployments items
    AppModel: f"{prefix}{client}-{V_CORE_AUTOMATION}-items",
    # All branch deployment items
    BranchModel: f"{prefix}{client}-{V_CORE_AUTOMATION}-items",
    # All build deployment items
    BuildModel: f"{prefix}{client}-{V_CORE_AUTOMATION}-items",
    # All component deployment items
    ComponentModel: f"{prefix}{client}-{V_CORE_AUTOMATION}-items",
    # All the events that are generated during deployment
    EventModel: f"{prefix}{client}-{V_CORE_AUTOMATION}-events",
}


# setup the test environment variables
@pytest.fixture(autouse=True)
def setup_module():
    """Setup the module for testing"""
    import os

    # Set environment variables for testing
    os.environ["CLIENT"] = "test-client"
    os.environ["CORE_AUTOMATION_SCOPE"] = "scope-test"
    os.environ["CORE_AUTOMATION_VERSION"] = "v1"


def test_get_clients_table_name():
    """Get the name of the client table"""
    table = get_table_name(ClientFactsModel, client="test-client")
    assert table is not None, "Client table name should not be None"
    assert table == "core-automation-clients", f"Expected 'core-automation-clients', got {table}"


def test_get_apps_table_name():
    """Get the name of the app table"""
    table = get_table_name(AppFactsModel, client="test-client")
    assert table is not None, "App table name should not be None"
    assert table == f"test-client-{V_CORE_AUTOMATION}-apps", f"Expected 'test-client-{V_CORE_AUTOMATION}-apps', got {table}"


def test_get_zones_table_name():
    """Get the name of the zone table"""
    table = get_table_name(ZoneFactsModel, client="test-client")
    assert table is not None, "Zone table name should not be None"
    assert table == f"test-client-{V_CORE_AUTOMATION}-zones", f"Expected 'test-client-{V_CORE_AUTOMATION}-zones', got {table}"


def test_get_portfolios_table_name():
    """Get the name of the portfolio table"""
    table = get_table_name(PortfolioFactsModel, client="test-client")
    assert table is not None, "Portfolio table name should not be None"
    assert (
        table == f"test-client-{V_CORE_AUTOMATION}-portfolios"
    ), f"Expected 'test-client-{V_CORE_AUTOMATION}-portfolios', got {table}"


def test_get_items_table_name():
    """Get the name of the item table"""
    table = get_table_name(ItemModel, client="test-client")
    assert table is not None, "Item table name should not be None"
    assert table == f"test-client-{V_CORE_AUTOMATION}-items", f"Expected 'test-client-{V_CORE_AUTOMATION}-items', got {table}"


def test_get_events_table_name():
    """Get the name of the event table"""
    table = get_table_name(EventModel, client="test-client")
    assert table is not None, "Event table name should not be None"
    assert table == f"test-client-{V_CORE_AUTOMATION}-events", f"Expected 'test-client-{V_CORE_AUTOMATION}-events', got {table}"


def table_names():
    for model, expected in tables.items():
        name = get_table_name(model, client="core")
        assert name == expected, f"Expected {expected}, got {name}"
