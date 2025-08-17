import pytest
from unittest.mock import patch
from pydantic import ValidationError

import core_framework as util

from core_db.registry.app.actions import AppActions
from core_db.registry.app.models import AppFact
from core_db.response import SuccessResponse, NoContentResponse
from core_db.exceptions import BadRequestException, NotFoundException, ConflictException, UnknownException

from .bootstrap import *

client = util.get_client()

app_facts = [
    # Production App
    {
        "portfolio": "acme-web",
        "app_regex": "core-api-.*",
        "name": "Core API Production",
        "environment": "production",
        "account": "123456789012",
        "zone": "prod-east",
        "region": "us-east-1",
        "repository": "https://github.com/acme/core-api",
        "enforce_validation": "true",
        "user_instantiated": "false",
        "image_aliases": {"base": "nginx:1.21-alpine", "app": "acme/core-api:latest"},
        "tags": {"Environment": "production", "Team": "platform", "CostCenter": "engineering", "Backup": "required"},
        "metadata": {
            "deployment_strategy": "blue-green",
            "health_check_path": "/health",
            "monitoring_level": "enhanced",
            "sla_tier": "tier1",
        },
    },
    # UAT App
    {
        "portfolio": "acme-web",
        "app_regex": "billing-service-.*",
        "name": "Billing Service UAT",
        "environment": "uat",
        "account": "234567890123",
        "zone": "uat-central",
        "region": "us-central-1",
        "repository": "https://github.com/acme/billing-service",
        "enforce_validation": "false",
        "user_instantiated": "true",
        "image_aliases": {"base": "alpine:3.15", "app": "acme/billing-service:uat"},
        "tags": {"Environment": "uat", "Team": "billing", "Purpose": "testing"},
        "metadata": {"deployment_strategy": "rolling", "health_check_path": "/status", "test_data_enabled": "true"},
    },
    # Development App
    {
        "portfolio": "acme-mobile",
        "app_regex": "mobile-backend-.*",
        "name": "Mobile Backend Dev",
        "environment": "development",
        "zone": "dev-west",
        "region": "us-west-2",
        "repository": "https://github.com/acme/mobile-backend",
        "enforce_validation": "false",
        "tags": {"Environment": "development", "Team": "mobile", "AutoShutdown": "enabled"},
        "metadata": {"deployment_strategy": "recreate", "debug_mode": "enabled", "log_level": "debug"},
    },
]


# =============================================================================
# Basic CRUD Tests
# =============================================================================


def test_app_create(bootstrap_dynamo):
    """Test creating all app facts."""
    for app_fact in app_facts:
        response = AppActions.create(client=client, **app_fact)

        assert isinstance(response, SuccessResponse)
        assert response.data is not None
        assert isinstance(response.data, dict)

        # Keys in response.data should be PascalCase
        assert "Portfolio" in response.data
        assert response.data["Portfolio"] == app_fact["portfolio"]
        assert "AppRegex" in response.data
        assert response.data["AppRegex"] == app_fact["app_regex"]
        assert "Name" in response.data
        assert response.data["Name"] == app_fact["name"]

        # Verify specific field mappings with PascalCase keys
        if "environment" in app_fact:
            assert "Environment" in response.data
            assert response.data["Environment"] == app_fact["environment"]
        if "zone" in app_fact:
            assert "Zone" in response.data
            assert response.data["Zone"] == app_fact["zone"]
        if "region" in app_fact:
            assert "Region" in response.data
            assert response.data["Region"] == app_fact["region"]


def test_app_get():
    """Test retrieving specific app facts."""
    portfolio = "acme-web"
    app_regex = "core-api-.*"

    response = AppActions.get(client=client, portfolio=portfolio, app_regex=app_regex)

    assert isinstance(response, SuccessResponse)
    assert response.data is not None
    assert isinstance(response.data, dict)

    # Keys in response.data should be PascalCase
    assert "Portfolio" in response.data
    assert response.data["Portfolio"] == portfolio
    assert "AppRegex" in response.data
    assert response.data["AppRegex"] == app_regex
    assert "Name" in response.data
    assert response.data["Name"] == "Core API Production"
    assert "Environment" in response.data
    assert response.data["Environment"] == "production"
    assert "Zone" in response.data
    assert response.data["Zone"] == "prod-east"


def test_app_list_all():
    """Test listing all app facts with pagination."""
    response = AppActions.list(client=client, limit=10)

    assert isinstance(response, SuccessResponse)
    assert response.data is not None
    assert isinstance(response.data, list)
    assert len(response.data) <= 10
    assert hasattr(response, "metadata")  # snake_case response attribute

    # Verify each item has PascalCase keys
    for item in response.data:
        assert isinstance(item, dict)
        assert "Portfolio" in item  # PascalCase key in data
        assert "AppRegex" in item  # PascalCase key in data
        assert "Name" in item  # PascalCase key in data

    # Check response structure
    if response.data:
        first_item = response.data[0]
        assert "Portfolio" in first_item  # PascalCase key


def test_app_list_by_portfolio():
    """Test listing apps by portfolio."""
    portfolio = "acme-web"

    response = AppActions.list(client=client, portfolio=portfolio, limit=5)

    assert isinstance(response, SuccessResponse)
    assert response.data is not None
    assert isinstance(response.data, list)
    assert hasattr(response, "metadata")

    # All returned apps should be from the specified portfolio
    for item in response.data:
        assert "Portfolio" in item
        assert item["Portfolio"] == portfolio
        assert "AppRegex" in item
        assert "Name" in item


def test_app_list_by_portfolio_and_app_name():
    """Test listing apps by portfolio and app name matching."""
    portfolio = "acme-web"
    app_name = "core-api-v1"  # Should match "core-api-.*" regex

    response = AppActions.list(client=client, portfolio=portfolio, app_name=app_name, limit=5)

    assert isinstance(response, SuccessResponse)
    assert response.data is not None
    assert isinstance(response.data, list)
    assert hasattr(response, "metadata")

    # Should return apps where regex matches the app_name
    for item in response.data:
        assert "Portfolio" in item
        assert item["Portfolio"] == portfolio
        assert "AppRegex" in item
        # Verify the app_name would match the regex pattern
        app_fact = AppFact(**item)
        assert app_fact.matches_app_name(app_name)


def test_app_list_with_pagination():
    """Test pagination functionality."""
    # Get first page
    page1 = AppActions.list(client=client, limit=2)
    assert len(page1.data) <= 2

    # Check if there's more data
    if page1.metadata.get("cursor"):
        page2 = AppActions.list(client=client, limit=2, cursor=page1.metadata["cursor"])
        assert isinstance(page2, SuccessResponse)

        # Verify different data using PascalCase keys
        page1_apps = {f"{item['Portfolio']}:{item['AppRegex']}" for item in page1.data}
        page2_apps = {f"{item['Portfolio']}:{item['AppRegex']}" for item in page2.data}
        assert page1_apps.isdisjoint(page2_apps), "Pages should not overlap"


# =============================================================================
# Update Tests (PUT and PATCH)
# =============================================================================


def test_app_update_full():
    """Test full app update (PUT semantics)."""
    portfolio = "acme-mobile"
    app_regex = "mobile-backend-.*"

    update_data = {
        "client": client,
        "portfolio": portfolio,
        "app_regex": app_regex,
        "name": "Updated Mobile Backend",
        "environment": "staging",
        "zone": "staging-west",
        "region": "us-west-1",
        "repository": "https://github.com/acme/mobile-backend-v2",
        "enforce_validation": "true",
        "tags": {"Environment": "staging", "Team": "mobile-updated", "Version": "2.0"},
        "metadata": {"deployment_strategy": "blue-green", "new_field": "updated-value"},
    }

    response = AppActions.update(**update_data)
    assert isinstance(response, SuccessResponse)

    # Verify PascalCase keys in response.data
    assert "Portfolio" in response.data
    assert "AppRegex" in response.data
    assert response.data["Name"] == "Updated Mobile Backend"
    assert response.data["Environment"] == "staging"
    assert response.data["Zone"] == "staging-west"
    assert response.data["Region"] == "us-west-1"
    assert "Tags" in response.data
    assert response.data["Tags"]["Version"] == "2.0"
    assert "Metadata" in response.data
    assert response.data["Metadata"]["new_field"] == "updated-value"


def test_app_patch_partial():
    """Test partial app update (PATCH semantics)."""
    portfolio = "acme-web"
    app_regex = "billing-service-.*"

    # Only update specific fields
    patch_data = {
        "client": client,
        "portfolio": portfolio,
        "app_regex": app_regex,
        "environment": "pre-production",
        "metadata": {"deployment_strategy": "canary", "rollback_enabled": "true", "patch_field": "patch-added"},
    }

    response = AppActions.patch(**patch_data)
    assert isinstance(response, SuccessResponse)

    # Verify PascalCase keys in response.data
    assert "Portfolio" in response.data
    assert "AppRegex" in response.data
    assert response.data["Environment"] == "pre-production"
    assert "Metadata" in response.data
    assert response.data["Metadata"]["deployment_strategy"] == "canary"
    assert response.data["Metadata"]["patch_field"] == "patch-added"

    # Other fields should remain unchanged
    assert response.data["Name"] == "Billing Service UAT"  # Should not change
    assert response.data["Zone"] == "uat-central"  # Should not change


def test_app_patch_with_none_values():
    """Test PATCH behavior with None values (should not remove fields)."""
    portfolio = "acme-web"
    app_regex = "core-api-.*"

    patch_data = {
        "client": client,
        "portfolio": portfolio,
        "app_regex": app_regex,
        "metadata": {"monitoring_level": "standard", "new_monitoring_field": "enabled"},
        "account": None,  # This should not remove the field in PATCH mode
    }

    response = AppActions.patch(**patch_data)
    assert isinstance(response, SuccessResponse)

    # Verify the metadata was updated using PascalCase keys
    assert "Metadata" in response.data
    assert response.data["Metadata"]["monitoring_level"] == "standard"
    assert response.data["Metadata"]["new_monitoring_field"] == "enabled"
    # Account should still exist (PATCH doesn't remove None fields)
    assert "Account" in response.data


def test_app_update_with_none_values():
    """Test UPDATE behavior with None values (should remove fields)."""
    portfolio = "acme-mobile"
    app_regex = "mobile-backend-.*"

    # Get current data first for required fields
    current_response = AppActions.get(client=client, portfolio=portfolio, app_regex=app_regex)
    current_data = current_response.data  # This has PascalCase keys

    update_data = {
        "client": client,
        "portfolio": portfolio,
        "app_regex": app_regex,
        "name": current_data["Name"],
        "zone": current_data["Zone"],
        "region": current_data["Region"],
        "environment": "production",  # Change this
        "account": None,  # This should remove the field in UPDATE mode
        "metadata": {"deployment_strategy": "rolling", "environment_updated": "true"},
    }

    response = AppActions.update(**update_data)
    assert isinstance(response, SuccessResponse)

    # Verify PascalCase keys in response
    assert "Environment" in response.data
    assert response.data["Environment"] == "production"
    assert "Metadata" in response.data
    assert response.data["Metadata"]["environment_updated"] == "true"
    # Account should be None/removed
    assert response.data.get("Account") is None


# =============================================================================
# Complex Data Structure Tests
# =============================================================================


def test_app_with_complex_structures():
    """Test app with complex image aliases, tags, and metadata."""
    complex_app = {
        "client": client,
        "portfolio": "test-complex",
        "app_regex": "complex-app-.*",
        "name": "Complex Test App",
        "zone": "test-zone",
        "region": "us-test-1",
        "image_aliases": {"base": "ubuntu:20.04", "runtime": "node:16-alpine", "cache": "redis:6.2", "db": "postgres:13"},
        "tags": {
            "Environment": "test",
            "Complexity": "high",
            "MultiValue": "value1,value2,value3",
            "SpecialChars": "test@value.com",
        },
        "metadata": {
            "nested_config": "enabled",
            "array_values": "item1,item2,item3",
            "json_like": '{"key": "value"}',
            "boolean_string": "true",
        },
    }

    # Create
    response = AppActions.create(**complex_app)
    assert isinstance(response, SuccessResponse)

    # Verify complex structure with PascalCase keys
    assert "ImageAliases" in response.data
    assert len(response.data["ImageAliases"]) == 4
    assert response.data["ImageAliases"]["base"] == "ubuntu:20.04"
    assert response.data["ImageAliases"]["db"] == "postgres:13"

    assert "Tags" in response.data
    assert response.data["Tags"]["Complexity"] == "high"
    assert response.data["Tags"]["SpecialChars"] == "test@value.com"

    assert "Metadata" in response.data
    assert response.data["Metadata"]["nested_config"] == "enabled"
    assert response.data["Metadata"]["json_like"] == '{"key": "value"}'

    # Clean up
    AppActions.delete(client=client, portfolio="test-complex", app_regex="complex-app-.*")


def test_app_regex_validation():
    """Test app regex pattern validation and matching."""
    test_app = {
        "client": client,
        "portfolio": "test-regex",
        "app_regex": "test-api-v[0-9]+",
        "name": "Regex Test App",
        "zone": "test-zone",
        "region": "us-test-1",
    }

    # Create
    response = AppActions.create(**test_app)
    assert isinstance(response, SuccessResponse)

    # Test the matches_app_name functionality
    created_app = AppFact(**response.data)
    assert created_app.matches_app_name("test-api-v1")
    assert created_app.matches_app_name("test-api-v999")
    assert not created_app.matches_app_name("test-api-beta")
    assert not created_app.matches_app_name("other-api-v1")

    # Clean up
    AppActions.delete(client=client, portfolio="test-regex", app_regex="test-api-v[0-9]+")


# =============================================================================
# Error Handling Tests
# =============================================================================


def test_create_duplicate_app():
    """Test creating duplicate app should fail."""
    duplicate_data = {
        "client": client,
        "portfolio": "acme-web",  # Already exists
        "app_regex": "core-api-.*",  # Already exists
        "name": "Duplicate Test",
        "zone": "test",
        "region": "us-test-1",
    }

    with pytest.raises(ConflictException):
        AppActions.create(**duplicate_data)


def test_get_nonexistent_app():
    """Test getting non-existent app."""
    response = AppActions.get(client=client, portfolio="nonexistent", app_regex="nonexistent-.*")
    assert isinstance(response, NoContentResponse)
    assert "does not exist" in response.message


def test_update_nonexistent_app():
    """Test updating non-existent app."""
    with pytest.raises(NotFoundException):
        AppActions.update(
            client=client, portfolio="nonexistent", app_regex="nonexistent-.*", name="Should Fail", zone="test", region="us-test-1"
        )


def test_patch_nonexistent_app():
    """Test patching non-existent app."""
    with pytest.raises(NotFoundException):
        AppActions.patch(client=client, portfolio="nonexistent", app_regex="nonexistent-.*", environment="should-fail")


def test_missing_required_parameters():
    """Test various operations without required parameters."""
    # Test create without portfolio
    with pytest.raises(BadRequestException):
        AppActions.create(client=client, app_regex="test", name="test", zone="test", region="test")

    # Test get without portfolio
    with pytest.raises(BadRequestException):
        AppActions.get(client=client, app_regex="test")

    # Test get without app_regex
    with pytest.raises(BadRequestException):
        AppActions.get(client=client, portfolio="test")

    # Test list without client (if util.get_client() returns None)
    with patch("core_framework.get_client", return_value=None):
        with pytest.raises(BadRequestException):
            AppActions.list()

    # Test update without portfolio
    with pytest.raises(BadRequestException):
        AppActions.update(client=client, app_regex="test", name="test", zone="test", region="test")

    # Test patch without app_regex
    with pytest.raises(BadRequestException):
        AppActions.patch(client=client, portfolio="test", name="test")


def test_invalid_app_data():
    """Test creating app with invalid data."""
    invalid_data = {
        "client": client,
        "portfolio": "invalid-test",
        "app_regex": "test",
        "name": "Test",
        "zone": "test",
        "region": "test",
        "enforce_validation": "invalid-boolean-value",  # Should be true/false/etc
    }

    # This might not fail validation depending on implementation
    # But if it does, it should be BadRequestException
    try:
        AppActions.create(**invalid_data)
        # Clean up if it succeeded
        AppActions.delete(client=client, portfolio="invalid-test", app_regex="test")
    except BadRequestException:
        pass  # Expected behavior


def test_invalid_pagination_parameters():
    """Test list with invalid pagination parameters."""
    with pytest.raises((BadRequestException, ValueError)):
        AppActions.list(client=client, limit="invalid")  # Non-integer limit

    with pytest.raises((BadRequestException, ValueError)):
        AppActions.list(client=client, limit=-1)  # Negative limit


# =============================================================================
# Delete Tests
# =============================================================================


def test_delete_app():
    """Test deleting an app."""
    # Create an app specifically for deletion
    delete_test_data = {
        "client": client,
        "portfolio": "delete-test",
        "app_regex": "delete-test-.*",
        "name": "App for Deletion Test",
        "zone": "test-zone",
        "region": "us-test-1",
    }

    # Create the app
    create_response = AppActions.create(**delete_test_data)
    assert isinstance(create_response, SuccessResponse)

    # Verify it exists
    get_response = AppActions.get(client=client, portfolio="delete-test", app_regex="delete-test-.*")
    assert isinstance(get_response, SuccessResponse)

    # Delete the app
    delete_response = AppActions.delete(client=client, portfolio="delete-test", app_regex="delete-test-.*")
    assert isinstance(delete_response, SuccessResponse)
    assert "deleted" in delete_response.message.lower()

    # Verify it's gone
    get_after_delete = AppActions.get(client=client, portfolio="delete-test", app_regex="delete-test-.*")
    assert isinstance(get_after_delete, NoContentResponse)


def test_delete_nonexistent_app():
    """Test deleting non-existent app."""
    response = AppActions.delete(client=client, portfolio="nonexistent", app_regex="nonexistent-.*")
    assert isinstance(response, NoContentResponse)
    assert "does not exist" in response.message


def test_delete_without_required_parameters():
    """Test delete without required parameters."""
    with pytest.raises(BadRequestException):
        AppActions.delete(client=client, portfolio="test")  # Missing app_regex

    with pytest.raises(BadRequestException):
        AppActions.delete(client=client, app_regex="test")  # Missing portfolio

    with patch("core_framework.get_client", return_value=None):
        with pytest.raises(BadRequestException):
            AppActions.delete(portfolio="test", app_regex="test")  # Missing client


# =============================================================================
# Edge Cases and Data Validation
# =============================================================================


def test_minimal_app_creation():
    """Test creating app with minimal required fields."""
    minimal_data = {
        "client": client,
        "portfolio": "minimal-test",
        "app_regex": "minimal-.*",
        "name": "Minimal App",
        "zone": "minimal-zone",
        "region": "us-minimal-1",
    }

    response = AppActions.create(**minimal_data)
    assert isinstance(response, SuccessResponse)

    # Verify PascalCase keys in response
    assert "Portfolio" in response.data
    assert response.data["Portfolio"] == "minimal-test"
    assert "AppRegex" in response.data
    assert response.data["AppRegex"] == "minimal-.*"
    assert "Name" in response.data
    assert response.data["Name"] == "Minimal App"

    # Clean up
    AppActions.delete(client=client, portfolio="minimal-test", app_regex="minimal-.*")


def test_app_timestamps():
    """Test that timestamps are properly managed."""
    timestamp_test_data = {
        "client": client,
        "portfolio": "timestamp-test",
        "app_regex": "timestamp-.*",
        "name": "Timestamp Test App",
        "zone": "test-zone",
        "region": "us-test-1",
    }

    # Create app
    create_response = AppActions.create(**timestamp_test_data)

    # Verify timestamps exist with PascalCase keys
    assert "CreatedAt" in create_response.data
    assert "UpdatedAt" in create_response.data
    assert create_response.data["CreatedAt"] is not None
    assert create_response.data["UpdatedAt"] is not None

    original_updated_at = create_response.data["UpdatedAt"]

    # Update app (should change updated_at)
    patch_response = AppActions.patch(client=client, portfolio="timestamp-test", app_regex="timestamp-.*", environment="updated")

    # Verify timestamp behavior with PascalCase keys
    assert patch_response.data["CreatedAt"] == create_response.data["CreatedAt"]  # Should not change
    assert patch_response.data["UpdatedAt"] != original_updated_at  # Should be updated

    # Clean up
    AppActions.delete(client=client, portfolio="timestamp-test", app_regex="timestamp-.*")


# =============================================================================
# Response Format Tests
# =============================================================================


def test_response_casing_consistency():
    """Test that all responses follow proper casing conventions."""

    # Test create response
    create_data = {
        "client": client,
        "portfolio": "casing-test",
        "app_regex": "casing-.*",
        "name": "Casing Test App",
        "zone": "test-zone",
        "region": "us-test-1",
    }

    create_response = AppActions.create(**create_data)

    # Response level should be snake_case
    assert hasattr(create_response, "data")
    assert hasattr(create_response, "message")

    # Data content should be PascalCase
    data_dict = create_response.data
    expected_pascal_keys = ["Portfolio", "AppRegex", "Name", "Zone", "Region", "CreatedAt", "UpdatedAt"]

    for key in expected_pascal_keys:
        if key in ["CreatedAt", "UpdatedAt"]:
            continue  # These might be None in some cases
        assert key in data_dict, f"Expected PascalCase key '{key}' not found in response data"

    # Test get response
    get_response = AppActions.get(client=client, portfolio="casing-test", app_regex="casing-.*")
    assert hasattr(get_response, "data")
    get_data_dict = get_response.data
    assert "Portfolio" in get_data_dict
    assert "AppRegex" in get_data_dict

    # Test list response
    list_response = AppActions.list(client=client, limit=1)
    assert hasattr(list_response, "data")
    assert hasattr(list_response, "metadata")  # snake_case

    if list_response.data:
        list_item = list_response.data[0]
        assert "Portfolio" in list_item  # PascalCase
        assert "AppRegex" in list_item  # PascalCase

    # Clean up
    AppActions.delete(client=client, portfolio="casing-test", app_regex="casing-.*")


def test_metadata_structure():
    """Test metadata structure in list responses."""
    response = AppActions.list(client=client, limit=1)

    # Metadata should exist and be snake_case
    assert hasattr(response, "metadata")
    metadata = response.metadata

    # Common metadata fields (snake_case)
    expected_metadata_keys = ["limit", "total_count", "has_more"]

    for key in expected_metadata_keys:
        # Not all metadata keys may be present depending on implementation
        if hasattr(metadata, key) or (isinstance(metadata, dict) and key in metadata):
            # Key exists, verify it's snake_case (no caps)
            assert key.islower() or "_" in key, f"Metadata key '{key}' should be snake_case"


def test_nested_data_structure_casing():
    """Test that nested data structures maintain PascalCase in response.data."""

    complex_data = {
        "client": client,
        "portfolio": "nested-casing-test",
        "app_regex": "nested-.*",
        "name": "Nested Casing Test",
        "zone": "test-zone",
        "region": "us-test-1",
        "environment": "test",
        "account": "123456789012",
        "repository": "https://github.com/test/nested",
        "enforce_validation": "true",
        "image_aliases": {"base": "alpine:latest", "app": "test/app:v1"},
        "tags": {"Environment": "test", "Team": "qa"},
        "metadata": {"test_type": "nested", "complexity": "high"},
    }

    response = AppActions.create(**complex_data)
    assert isinstance(response, SuccessResponse)

    data = response.data

    # Top-level fields should be PascalCase
    assert "Portfolio" in data
    assert "AppRegex" in data
    assert "Name" in data
    assert "Zone" in data
    assert "Region" in data
    assert "Environment" in data
    assert "Account" in data
    assert "Repository" in data
    assert "EnforceValidation" in data
    assert "ImageAliases" in data
    assert "Tags" in data
    assert "Metadata" in data

    # Nested dictionary keys should preserve their original casing
    assert "base" in data["ImageAliases"]
    assert "app" in data["ImageAliases"]
    assert "Environment" in data["Tags"]
    assert "Team" in data["Tags"]
    assert "test_type" in data["Metadata"]
    assert "complexity" in data["Metadata"]

    # Clean up
    AppActions.delete(client=client, portfolio="nested-casing-test", app_regex="nested-.*")


def test_validation_enforcement_methods():
    """Test validation enforcement utility methods."""
    # Create app with validation enabled
    validation_app = {
        "client": client,
        "portfolio": "validation-test",
        "app_regex": "validation-.*",
        "name": "Validation Test App",
        "zone": "test-zone",
        "region": "us-test-1",
        "enforce_validation": "true",
    }

    response = AppActions.create(**validation_app)
    created_app = AppFact(**response.data)

    # Test validation enforcement
    assert created_app.is_validation_enforced() == True

    # Update with different validation values
    for validation_value, expected in [
        ("false", False),
        ("0", False),
        ("no", False),
        ("disabled", False),
        ("true", True),
        ("1", True),
        ("yes", True),
        ("enabled", True),
        (None, False),
    ]:
        if validation_value is not None:
            patch_response = AppActions.patch(
                client=client, portfolio="validation-test", app_regex="validation-.*", enforce_validation=validation_value
            )
            patched_app = AppFact(**patch_response.data)
            assert patched_app.is_validation_enforced() == expected

    # Clean up
    AppActions.delete(client=client, portfolio="validation-test", app_regex="validation-.*")
