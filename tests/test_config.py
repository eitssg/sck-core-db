import pytest

from core_db.config import get_table_name
from core_db.constants import (
    CLIENT_FACTS,
    PORTFOLIO_FACTS,
    ZONE_FACTS,
    APP_FACTS,
    ITEMS,
    EVENTS,
)


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
    table = get_table_name(CLIENT_FACTS)
    assert table is not None, "Client table name should not be None"
    assert table == "core-automation-clients", f"Expected 'core-automation-clients', got {table}"


def test_get_apps_table_name():
    """Get the name of the app table"""
    table = get_table_name(APP_FACTS)
    assert table is not None, "App table name should not be None"
    assert table == "test-client-core-automation-apps", f"Expected 'core-automation-apps', got {table}"


def test_get_zones_table_name():
    """Get the name of the zone table"""
    table = get_table_name(ZONE_FACTS)
    assert table is not None, "Zone table name should not be None"
    assert table == "test-client-core-automation-zones", f"Expected 'test-client-core-automation-zones', got {table}"


def test_get_portfolios_table_name():
    """Get the name of the portfolio table"""
    table = get_table_name(PORTFOLIO_FACTS)
    assert table is not None, "Portfolio table name should not be None"
    assert table == "test-client-core-automation-portfolios", f"Expected 'test-client-core-automation-portfolios', got {table}"


def test_get_items_table_name():
    """Get the name of the item table"""
    table = get_table_name(ITEMS)
    assert table is not None, "Item table name should not be None"
    assert table == "test-client-core-automation-items", f"Expected 'test-client-core-automation-items', got {table}"


def test_get_events_table_name():
    """Get the name of the event table"""
    table = get_table_name(EVENTS)
    assert table is not None, "Event table name should not be None"
    assert table == "test-client-core-automation-events", f"Expected 'test-client-core-automation-events', got {table}"


def test_get_table_name_invalid():
    """Test getting a table name with an invalid name"""
    with pytest.raises(ValueError, match="Table name not found for invalid_name"):
        get_table_name("invalid_name")
