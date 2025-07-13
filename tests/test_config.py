import pytest

from core_db.config import (
    get_table_name,
    get_clients_table_name,
    get_apps_table_name,
    get_zones_table_name,
    get_portfolios_table_name,
    get_items_table_name,
    get_events_table_name,
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
    table = get_clients_table_name()
    assert table is not None, "Client table name should not be None"
    assert (
        table == "core-automation-clients"
    ), f"Expected 'core-automation-clients', got {table}"


def test_get_apps_table_name():
    """Get the name of the app table"""
    table = get_apps_table_name()
    assert table is not None, "App table name should not be None"
    assert (
        table == "core-automation-apps"
    ), f"Expected 'core-automation-apps', got {table}"


def test_get_zones_table_name():
    """Get the name of the zone table"""
    table = get_zones_table_name()
    assert table is not None, "Zone table name should not be None"
    assert (
        table == "core-automation-zones"
    ), f"Expected 'core-automation-zones', got {table}"


def test_get_portfolios_table_name():
    """Get the name of the portfolio table"""
    table = get_portfolios_table_name()
    assert table is not None, "Portfolio table name should not be None"
    assert (
        table == "core-automation-portfolios"
    ), f"Expected 'core-automation-port, got {table}"


def test_get_items_table_name():
    """Get the name of the item table"""
    table = get_items_table_name()
    assert table is not None, "Item table name should not be None"
    assert (
        table == "test-client-core-automation-items"
    ), f"Expected 'test-client-core-automation-items', got {table}"


def test_get_events_table_name():
    """Get the name of the event table"""
    table = get_events_table_name()
    assert table is not None, "Event table name should not be None"
    assert (
        table == "test-client-core-automation-events"
    ), f"Expected 'test-client-core-automation-events', got {table}"


def test_get_table_name_invalid():
    """Test getting a table name with an invalid name"""
    with pytest.raises(ValueError, match="Table name not found for invalid_name"):
        get_table_name("invalid_name")
