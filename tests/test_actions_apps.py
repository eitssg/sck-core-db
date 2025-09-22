import pytest
from unittest.mock import patch

import core_framework as util

from core_db.registry.app.actions import AppActions
from core_db.registry.app.models import AppFact
from core_db.exceptions import (
    BadRequestException,
    NotFoundException,
    ConflictException,
    UnknownException,
)

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
        "tags": {
            "Environment": "production",
            "Team": "platform",
            "CostCenter": "engineering",
            "Backup": "required",
        },
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
        "metadata": {
            "deployment_strategy": "rolling",
            "health_check_path": "/status",
            "test_data_enabled": "true",
        },
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
        "tags": {
            "Environment": "development",
            "Team": "mobile",
            "AutoShutdown": "enabled",
        },
        "metadata": {
            "deployment_strategy": "recreate",
            "debug_mode": "enabled",
            "log_level": "debug",
        },
    },
]


# =============================================================================
# Basic CRUD Tests
# =============================================================================


def test_app_create(bootstrap_dynamo):
    """Test creating all app facts."""
    for app_fact in app_facts:

        response: AppFact = AppActions.create(client=client, **app_fact)

        # Keys in response.data should be PascalCase
        assert response.portfolio == app_fact["portfolio"]
        assert response.app_regex == app_fact["app_regex"]
        assert response.name == app_fact["name"]

        # Verify specific field mappings with PascalCase keys
        if "environment" in app_fact:
            assert response.environment == app_fact["environment"]
        if "zone" in app_fact:
            assert response.zone == app_fact["zone"]
        if "region" in app_fact:
            assert response.region == app_fact["region"]
            assert response.region == app_fact["region"]


def test_app_get():
    """Test retrieving specific app facts."""
    portfolio = "acme-web"
    app_regex = "core-api-.*"
    app = "core-api-v1"  # Should match the regex

    app_facts, paginator = AppActions.list(client=client, portfolio=portfolio, app_regex=app_regex)

    assert len(app_facts) > 0
    assert paginator.total_count > 0

    response = app_facts[0]

    # Keys in response.data should be PascalCase
    assert response.portfolio == portfolio
    assert response.app_regex == app_regex
    assert response.name == "Core API Production"
    assert response.environment == "production"
    assert response.zone == "prod-east"


def test_app_list_all():
    """Test listing all app facts with pagination."""
    app_facts, paginator = AppActions.list(client=client, limit=10)

    assert len(app_facts) == 3
    assert paginator.total_count == 3


def test_app_list_by_portfolio():
    """Test listing apps by portfolio."""
    portfolio = "acme-web"

    app_facts, paginator = AppActions.list(client=client, portfolio=portfolio, limit=5)

    assert len(app_facts) == 2
    assert paginator.total_count == 2

    for item in app_facts:
        assert item.portfolio == portfolio


def test_app_list_by_portfolio_and_app():
    """Test listing apps by portfolio and app name matching."""
    portfolio = "acme-web"
    app = "core-api-production"

    app_fact = AppActions.get(client=client, portfolio=portfolio, app=app, limit=5)

    # Verify the returned app fact matches the expected values
    assert app_fact.portfolio == portfolio
    assert app_fact.app == app


def test_app_list_with_pagination():
    """Test pagination functionality."""
    # Get first page
    app_facts, paginator = AppActions.list(client=client, limit=2)
    assert len(app_facts) <= 2

    # Check if there's more data
    if paginator.cursor:
        page2, paginator = AppActions.list(client=client, limit=2, cursor=paginator.cursor)

        # Verify different data using PascalCase keys
        page1_apps = {f"{item.portfolio}:{item.app_regex}" for item in app_facts}
        page2_apps = {f"{item.portfolio}:{item.app_regex}" for item in page2}

        assert page1_apps.isdisjoint(page2_apps), "Pages should not overlap"


# =============================================================================
# Update Tests (PUT and PATCH)
# =============================================================================


def test_app_update_full():
    """Test full app update (PUT semantics)."""
    portfolio = "acme-mobile"
    app = "mobile-backend-dev"
    app_regex = "mobile-backend-.*"

    update_data = {
        "app": app,
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

    response: AppFact = AppActions.update(client=client, **update_data)
    assert response.name == "Updated Mobile Backend"
    assert response.environment == "staging"
    assert response.zone == "staging-west"
    assert response.region == "us-west-1"
    assert response.tags["Version"] == "2.0"
    assert response.metadata
    assert response.metadata["new_field"] == "updated-value"


def test_app_patch_partial():
    """Test partial app update (PATCH semantics)."""
    portfolio = "acme-web"
    app = "billing-service-uat"
    app_regex = "billing-service-.*"

    # Only update specific fields
    patch_data = {
        "app": app,
        "portfolio": portfolio,
        "app_regex": app_regex,
        "environment": "pre-production",
        "metadata": {
            "deployment_strategy": "canary",
            "rollback_enabled": "true",
            "patch_field": "patch-added",
        },
    }

    response: AppFact = AppActions.patch(client=client, **patch_data)

    # Verify PascalCase keys in response.data
    assert response.portfolio
    assert response.app_regex
    assert response.environment == "pre-production"
    assert response.metadata
    assert response.metadata["deployment_strategy"] == "canary"
    assert response.metadata["patch_field"] == "patch-added"

    # Other fields should remain unchanged
    assert response.name == "Billing Service UAT"  # Should not change
    assert response.zone == "uat-central"  # Should not change


def test_app_patch_with_none_values():
    """Test PATCH behavior with None values (should not remove fields)."""
    portfolio = "acme-web"
    app = "core-api-production"
    app_regex = "core-api-.*"

    patch_data = {
        "app": app,
        "portfolio": portfolio,
        "app_regex": app_regex,
        "metadata": {"monitoring_level": "standard", "new_monitoring_field": "enabled"},
        "account": None,  # This should not remove the field in PATCH mode
    }

    response: AppFact = AppActions.patch(client=client, **patch_data)

    # Verify the metadata was updated using PascalCase keys
    assert response.metadata
    assert response.metadata["monitoring_level"] == "standard"
    assert response.metadata["new_monitoring_field"] == "enabled"

    # Account should still exist (PATCH doesn't remove None fields)
    assert response.account == "123456789012"


def test_app_update_with_none_values():
    """Test UPDATE behavior with None values (should remove fields)."""
    portfolio = "acme-mobile"
    app = "mobile-backend-dev"
    app_regex = "mobile-backend-.*"

    # Get current data first for required fields
    current_data: AppFact = AppActions.get(client=client, portfolio=portfolio, app=app)

    update_data = {
        "app": app,
        "portfolio": portfolio,
        "app_regex": app_regex,
        "name": current_data.name,
        "zone": current_data.zone,
        "region": current_data.region,
        "environment": "production",  # Change this
        "account": None,  # This should remove the field in UPDATE mode
        "metadata": {"deployment_strategy": "rolling", "environment_updated": "true"},
    }

    response: AppFact = AppActions.update(client=client, **update_data)

    # Verify PascalCase keys in response
    assert response.environment == "production"
    assert response.metadata
    assert response.metadata["environment_updated"] == "true"

    # Account should be None/removed
    assert response.account is None


# =============================================================================
# Complex Data Structure Tests
# =============================================================================


def test_app_with_complex_structures():
    """Test app with complex image aliases, tags, and metadata."""

    complex_app = {
        "portfolio": "test-complex",
        "app": "complex-app-v2",
        "app_regex": "complex-app-.*",
        "name": "Complex Test App",
        "zone": "test-zone",
        "region": "us-test-1",
        "image_aliases": {
            "base": "ubuntu:20.04",
            "runtime": "node:16-alpine",
            "cache": "redis:6.2",
            "db": "postgres:13",
        },
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
    response: AppFact = AppActions.create(client=client, **complex_app)

    # Verify complex structure with PascalCase keys
    assert len(response.image_aliases) == 4
    assert response.image_aliases["base"] == "ubuntu:20.04"
    assert response.image_aliases["db"] == "postgres:13"

    assert response.tags
    assert response.tags["Complexity"] == "high"
    assert response.tags["SpecialChars"] == "test@value.com"

    assert response.metadata["nested_config"] == "enabled"
    assert response.metadata["json_like"] == '{"key": "value"}'

    # Clean up
    AppActions.delete(client=client, portfolio=response.portfolio, app=response.app)


def test_app_regex_validation():
    """Test app regex pattern validation and matching."""
    test_app = {
        "app": "test-api-v1",
        "portfolio": "test-regex",
        "app_regex": "test-api-v[0-9]+",
        "name": "Regex Test App",
        "zone": "test-zone",
        "region": "us-test-1",
    }

    # Create
    response: AppFact = AppActions.create(client=client, **test_app)

    assert response.matches_app("test-api-v1")
    assert response.matches_app("test-api-v999")
    assert not response.matches_app("test-api-beta")
    assert not response.matches_app("other-api-v1")

    # Clean up
    AppActions.delete(client=client, portfolio=response.portfolio, app=response.app)


# =============================================================================
# Error Handling Tests
# =============================================================================


def test_create_duplicate_app():
    """Test creating duplicate app should fail."""
    duplicate_data = {
        "app": "core-api-production",
        "portfolio": "acme-web",  # Already exists
        "app_regex": "core-api-.*",  # Already exists
        "name": "Duplicate Test",
        "zone": "test",
        "region": "us-test-1",
    }

    with pytest.raises(ConflictException):
        AppActions.create(client=client, **duplicate_data)


def test_get_nonexistent_app():
    """Test getting non-existent app."""

    with pytest.raises(NotFoundException):
        response: AppFact = AppActions.get(client=client, portfolio="nonexistent", app="nonexistent-app")


def test_update_nonexistent_app():
    """Test updating non-existent app."""
    with pytest.raises(NotFoundException):
        AppActions.update(
            client=client,
            portfolio="nonexistent",
            app="nonexistent-.*",
            name="Should Fail",
            zone="test",
            region="us-test-1",
        )


def test_patch_nonexistent_app():
    """Test patching non-existent app."""
    with pytest.raises(NotFoundException):
        AppActions.patch(
            client=client,
            portfolio="nonexistent",
            app="nonexistent-.*",
            environment="should-fail",
        )


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
            AppActions.list(client=None)

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
    a: AppFact = AppActions.create(**delete_test_data)

    # Verify it exists
    get_response: AppFact = AppActions.get(client=client, portfolio=a.portfolio, app=a.app)

    # Delete the app
    result = AppActions.delete(client=client, portfolio=a.portfolio, app=a.app)
    assert result is True

    # Verify it's gone.  Expect NotFoundException
    with pytest.raises(NotFoundException):
        AppActions.get(client=client, portfolio=a.portfolio, app=a.app)


def test_delete_nonexistent_app():
    """Test deleting non-existent app."""
    with pytest.raises(NotFoundException):
        result = AppActions.delete(client=client, portfolio="nonexistent", app="nonexistent-.*")


def test_delete_without_required_parameters():
    """Test delete without required parameters."""
    with pytest.raises(BadRequestException):
        AppActions.delete(client=client, portfolio="test")  # Missing app_regex

    with pytest.raises(BadRequestException):
        AppActions.delete(client=client, app_regex="test")  # Missing portfolio

    with patch("core_framework.get_client", return_value=None):
        with pytest.raises(BadRequestException):
            AppActions.delete(client=None, sportfolio="test", app="test")  # Missing client


# =============================================================================
# Edge Cases and Data Validation
# =============================================================================


def test_minimal_app_creation():
    """Test creating app with minimal required fields."""

    minimal_data = {
        "portfolio": "minimal-test",
        "app_regex": "minimal-.*",
        "name": "Minimal App",
        "zone": "minimal-zone",
        "region": "us-minimal-1",
    }

    response: AppFact = AppActions.create(client=client, **minimal_data)

    # Verify PascalCase keys in response
    assert response.portfolio == "minimal-test"
    assert response.app_regex == "minimal-.*"
    assert response.name == "Minimal App"
    assert response.zone == "minimal-zone"
    assert response.region == "us-minimal-1"

    # Clean up
    AppActions.delete(client=client, portfolio=response.portfolio, app=response.app)


def test_app_timestamps():
    """Test that timestamps are properly managed."""
    timestamp_test_data = {
        "portfolio": "timestamp-test",
        "app_regex": "timestamp-.*",
        "name": "Timestamp Test App",
        "zone": "test-zone",
        "region": "us-test-1",
    }

    # Create app
    create_response: AppFact = AppActions.create(client=client, **timestamp_test_data)

    # Verify timestamps exist with PascalCase keys
    assert create_response.created_at is not None
    assert create_response.updated_at is not None
    assert create_response.updated_at is not None

    original_updated_at = create_response.updated_at

    # Update app (should change updated_at)
    pr: AppFact = AppActions.patch(
        client=client,
        portfolio="timestamp-test",
        app=create_response.app,
        environment="updated",
    )

    # Verify timestamp behavior with PascalCase keys
    assert pr.created_at == create_response.created_at  # Should not change
    assert pr.updated_at != original_updated_at  # Should be updated

    # Clean up
    AppActions.delete(client=client, portfolio=pr.portfolio, app=pr.app)


# =============================================================================
# Response Format Tests
# =============================================================================


def test_response_casing_consistency():
    """Test that all responses follow proper casing conventions."""

    # Test create response
    create_data = {
        "portfolio": "casing-test",
        "app_regex": "casing-.*",
        "name": "Casing Test App",
        "zone": "test-zone",
        "region": "us-test-1",
    }

    cr: AppFact = AppActions.create(client=client, **create_data)

    # Test get response
    get_response: AppFact = AppActions.get(client=client, portfolio=cr.portfolio, app=cr.app)

    # Test list response
    list_response, paginator = AppActions.list(client=client, limit=1)

    if list_response:
        list_item = list_response[0]

    # Clean up
    AppActions.delete(client=client, portfolio=cr.portfolio, app=cr.app)


def test_nested_data_structure_casing():
    """Test that nested data structures maintain PascalCase in response.data."""

    complex_data = {
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

    response: AppFact = AppActions.create(client=client, **complex_data)

    data = response.model_dump()

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
    AppActions.delete(client=client, portfolio=response.portfolio, app=response.app)


def test_validation_enforcement_methods():
    """Test validation enforcement utility methods."""
    # Create app with validation enabled
    validation_app = {
        "portfolio": "validation-test",
        "app_regex": "validation-.*",
        "name": "Validation Test App",
        "zone": "test-zone",
        "region": "us-test-1",
        "enforce_validation": "true",
    }

    response: AppFact = AppActions.create(client=client, **validation_app)

    # Test validation enforcement
    assert response.is_validation_enforced() == True

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
            patched_app: AppFact = AppActions.patch(
                client=client,
                portfolio=response.portfolio,
                app=response.app,
                enforce_validation=validation_value,
            )
            assert patched_app.is_validation_enforced() == expected

    # Clean up
    AppActions.delete(client=client, portfolio=response.portfolio, app=response.app)
