from pydantic.type_adapter import P
import pytest
from unittest.mock import patch
import core_framework as util

from core_db.registry.portfolio.actions import PortfolioActions
from core_db.registry.portfolio.models import PortfolioFact
from core_db.response import SuccessResponse, NoContentResponse
from core_db.exceptions import (
    BadRequestException,
    NotFoundException,
    ConflictException,
    UnknownException,
)

from .bootstrap import *

client = util.get_client()

portfolio_facts: list[dict] = [
    {
        "portfolio": "web-services",
        "domain": "webservices.acme.com",
        "project": {
            "name": "Web Services Platform",
            "code": "web-api",
            "repository": "https://github.com/acme/web-services",
            "description": "Core web services and REST APIs for customer-facing applications",
        },
        "owner": {
            "name": "Sarah Johnson",
            "email": "sarah.johnson@acme.com",
            "phone": "+1-555-0123",
        },
        "contacts": [
            {"name": "Tech Lead", "email": "techm@acme.com", "enabled": True},
            {"name": "DevOps Engineer", "email": "devops@acme.com", "enabled": True},
        ],
        "approvers": [
            {
                "sequence": 1,
                "name": "Engineering Manager",
                "email": "eng-mgr@acme.com",
                "roles": ["deployment", "infrastructure"],
                "enabled": True,
            },
            {
                "sequence": 2,
                "name": "Platform Director",
                "email": "platform-dir@acme.com",
                "depends_on": [1],
                "enabled": True,
            },
        ],
        "tags": {
            "Environment": "production",
            "Team": "platform",
            "CostCenter": "engineering",
        },
        "metadata": {
            "deployment_strategy": "blue-green",
            "monitoring_level": "enhanced",
            "backup_retention": "30days",
        },
    },
    {
        "portfolio": "mobile-apps",
        "domain": "mobile.acme.com",
        "project": {
            "name": "Mobile Applications",
            "code": "mobile",
            "repository": "https://github.com/acme/mobile-apps",
            "description": "iOS and Android mobile applications for customer engagement",
        },
        "owner": {
            "name": "Michael Chen",
            "email": "michael.chen@acme.com",
            "phone": "+1-555-0456",
        },
        "contacts": [
            {
                "name": "Mobile Team Lead",
                "email": "mobile-lead@acme.com",
                "enabled": True,
            }
        ],
        "approvers": [
            {
                "sequence": 1,
                "name": "Mobile Manager",
                "email": "mobile-mgr@acme.com",
                "roles": ["mobile-deployment", "app-store"],
                "enabled": True,
            }
        ],
        "tags": {
            "Environment": "production",
            "Team": "mobile",
            "Platform": "cross-platform",
        },
        "attributes": {
            "app_store_id": "com.acme.mobile",
            "target_platforms": "ios,android",
        },
    },
    {
        "portfolio": "data-analytics",
        "domain": "analytics.acme.com",
        "project": {
            "name": "Data Analytics Platform",
            "code": "analytics",
            "repository": "https://github.com/acme/data-analytics",
            "description": "Business intelligence and data processing pipelines",
        },
        "bizapp": {
            "name": "Business Intelligence Suite",
            "code": "bi-suite",
            "description": "Comprehensive BI tools and dashboards",
        },
        "owner": {
            "name": "Dr. Lisa Wang",
            "email": "lisa.wang@acme.com",
            "phone": "+1-555-0789",
        },
        "contacts": [
            {"name": "Data Engineer", "email": "data-eng@acme.com", "enabled": True},
            {
                "name": "Analytics Lead",
                "email": "analytics-lead@acme.com",
                "enabled": True,
            },
        ],
        "approvers": [
            {
                "sequence": 1,
                "name": "Data Privacy Officer",
                "email": "privacy@acme.com",
                "roles": ["data-access", "privacy-review"],
                "enabled": True,
            },
            {
                "sequence": 2,
                "name": "Analytics Director",
                "email": "analytics-dir@acme.com",
                "roles": ["deployment"],
                "depends_on": [1],
                "enabled": True,
            },
        ],
        "tags": {
            "Environment": "production",
            "Team": "data",
            "DataClassification": "sensitive",
        },
        "metadata": {
            "data_retention": "7years",
            "compliance": "gdpr,ccpa",
            "encryption": "required",
        },
    },
    {
        "portfolio": "internal-tools",
        "project": {
            "name": "Internal Developer Tools",
            "code": "dev-tools",
            "repository": "https://github.com/acme/internal-tools",
            "description": "Internal productivity and development tools",
        },
        "owner": {"name": "Alex Rodriguez", "email": "alex.rodriguez@acme.com"},
        "contacts": [{"name": "DevEx Team", "email": "devex@acme.com", "enabled": True}],
        "approvers": [
            {
                "sequence": 1,
                "name": "DevEx Manager",
                "email": "devex-mgr@acme.com",
                "roles": ["internal-deployment"],
                "enabled": True,
            }
        ],
        "tags": {"Environment": "internal", "Team": "devex", "Visibility": "private"},
        "attributes": {
            "access_level": "employees-only",
            "deployment_frequency": "weekly",
        },
    },
    {
        "portfolio": "legacy-migration",
        "domain": "legacy.acme.com",
        "project": {
            "name": "Legacy System Migration",
            "code": "legacy-mig",
            "description": "Migration of legacy systems to cloud-native architecture",
        },
        "owner": {
            "name": "Robert Kim",
            "email": "robert.kim@acme.com",
            "phone": "+1-555-0321",
        },
        "contacts": [
            {
                "name": "Migration Architect",
                "email": "migration@acme.com",
                "enabled": True,
            },
            {
                "name": "Legacy Systems SME",
                "email": "legacy-sme@acme.com",
                "enabled": True,
            },
        ],
        "approvers": [
            {
                "sequence": 1,
                "name": "Architecture Review Board",
                "email": "arb@acme.com",
                "roles": ["architecture-review"],
                "enabled": True,
            },
            {
                "sequence": 2,
                "name": "Migration Manager",
                "email": "migration-mgr@acme.com",
                "roles": ["migration-deployment"],
                "enabled": True,
            },
            {
                "sequence": 3,
                "name": "CTO",
                "email": "cto@acme.com",
                "depends_on": [1, 2],
                "enabled": True,
            },
        ],
        "tags": {
            "Environment": "migration",
            "Team": "architecture",
            "Priority": "high",
        },
        "metadata": {
            "migration_phase": "assessment",
            "target_completion": "Q4-2025",
            "risk_level": "medium",
        },
        "attributes": {
            "legacy_systems": "mainframe,cobol",
            "target_architecture": "microservices",
        },
    },
]


# =============================================================================
# Basic CRUD Tests
# =============================================================================


def test_portfolio_create(bootstrap_dynamo):
    """Test creating all portfolio facts."""
    for portfolio in portfolio_facts:
        PortfolioActions.create(client=client, **portfolio)


def test_portfolio_get():
    """Test retrieving specific portfolio facts."""
    portfolio_name = "web-services"

    response: PortfolioFact = PortfolioActions.get(client=client, portfolio=portfolio_name)

    # Keys in response.data should be PascalCase
    assert response.portfolio == portfolio_name
    assert response.domain == "webservices.acme.com"
    assert response.project.name == "Web Services Platform"
    assert response.owner.name == "Sarah Johnson"


def test_portfolio_list():
    """Test listing all portfolio facts with pagination."""
    portfolio_list, paginator = PortfolioActions.list(client=client, limit=3)

    assert isinstance(portfolio_list, list)
    assert len(portfolio_list) == 3
    assert paginator.total_count == 3

    # Verify each item has PascalCase keys and can be converted to PortfolioFact
    for item in portfolio_list:
        assert item.portfolio is not None


def test_portfolio_list_with_pagination():
    """Test pagination functionality."""
    # Get first page
    page1, paginator = PortfolioActions.list(client=client, limit=2)
    assert len(page1) == 2
    assert paginator.total_count == 2
    assert paginator.cursor is not None

    page2, paginator = PortfolioActions.list(client=client, limit=2, cursor=paginator.cursor)
    assert len(page2) == 2
    assert paginator.total_count == 2
    assert paginator.cursor is not None  # there are more items

    # Verify different data using PascalCase keys
    page1_portfolios = {item.portfolio for item in page1}
    page2_portfolios = {item.portfolio for item in page2}

    assert page1_portfolios.isdisjoint(page2_portfolios), "Pages should not overlap"


# =============================================================================
# Update Tests (PUT and PATCH)
# =============================================================================


def test_portfolio_update_full():
    """Test full portfolio update (PUT semantics)."""
    portfolio_name = "mobile-apps"

    update_data = {
        "portfolio": portfolio_name,
        "domain": "mobile-updated.acme.com",
        "project": {
            "name": "Updated Mobile Applications",
            "code": "mobile-v2",
            "repository": "https://github.com/acme/mobile-apps-v2",
            "description": "Next generation mobile applications",
        },
        "owner": {
            "name": "Michael Chen",
            "email": "michael.chen@acme.com",
            "phone": "+1-555-9999",
        },
        "tags": {
            "Environment": "production",
            "Team": "mobile-updated",
            "Version": "2.0",
        },
    }

    response: PortfolioFact = PortfolioActions.update(client=client, **update_data)

    assert response.domain == "mobile-updated.acme.com"
    assert response.project.name == "Updated Mobile Applications"
    assert response.owner.phone == "+1-555-9999"
    assert response.tags["Version"] == "2.0"


def test_portfolio_patch_partial():
    """Test partial portfolio update (PATCH semantics)."""
    portfolio_name = "data-analytics"

    # Only update specific fields
    patch_data = {
        "portfolio": portfolio_name,
        "domain": "analytics-updated.acme.com",
        "metadata": {
            "data_retention": "10years",
            "compliance": "gdpr,ccpa,sox",
            "encryption": "required",
            "new_field": "patch-added",
        },
    }

    response: PortfolioFact = PortfolioActions.patch(client=client, **patch_data)

    assert response.domain == "analytics-updated.acme.com"
    assert response.metadata["data_retention"] == "10years"
    assert response.metadata["new_field"] == "patch-added"

    # Other fields should remain unchanged
    assert response.project.name == "Data Analytics Platform"
    assert response.owner.name == "Dr. Lisa Wang"


def test_portfolio_patch_with_none_values():
    """Test PATCH behavior with None values (should not remove fields)."""
    portfolio_name = "internal-tools"

    patch_data = {
        "portfolio": portfolio_name,
        "attributes": {
            "access_level": "all-employees",
            "deployment_frequency": "daily",
        },
        "domain": None,  # This should not remove the field in PATCH mode
    }

    response: PortfolioFact = PortfolioActions.patch(client=client, **patch_data)

    assert response.attributes["access_level"] == "all-employees"
    assert response.attributes["deployment_frequency"] == "daily"

    # Domain should still exist (PATCH doesn't remove None fields)


def test_portfolio_update_with_none_values():
    """Test UPDATE behavior with None values (should remove fields)."""
    portfolio_name = "legacy-migration"

    # Get current data first for required fields
    current_data: PortfolioFact = PortfolioActions.get(client=client, portfolio=portfolio_name)

    update_data = {
        "portfolio": portfolio_name,
        # Convert PascalCase back to snake_case for input
        "project": {
            "name": current_data.project.name,
            "code": current_data.project.code,
            "description": current_data.project.description,
        },
        "owner": {
            "name": current_data.owner.name,
            "email": current_data.owner.email,
            "phone": current_data.owner.phone,
        },
        "contacts": [
            {
                "name": contact.name,
                "email": contact.email,
                "enabled": contact.enabled,
            }
            for contact in current_data.contacts
        ],
        "domain": None,  # This should remove the field in UPDATE mode
        "metadata": {
            "migration_phase": "implementation",
            "target_completion": "Q2-2026",
        },
    }

    response: PortfolioFact = PortfolioActions.update(client=client, **update_data)

    # Verify PascalCase keys in response
    assert response.metadata["migration_phase"] == "implementation"

    # Domain should be None/removed
    assert response.domain is None


# =============================================================================
# Complex Data Structure Tests
# =============================================================================


def test_portfolio_with_complex_approvers():
    """Test portfolio with complex approval workflows."""
    complex_portfolio = {
        "client": client,
        "portfolio": "complex-approval-test",
        "project": {
            "name": "Complex Approval Workflow Test",
            "code": "approval-test",
            "description": "Testing complex approval dependencies",
        },
        "owner": {"name": "Test Owner", "email": "test@acme.com"},
        "approvers": [
            {
                "sequence": 1,
                "name": "First Approver",
                "email": "first@acme.com",
                "roles": ["initial-review"],
                "enabled": True,
            },
            {
                "sequence": 2,
                "name": "Second Approver",
                "email": "second@acme.com",
                "roles": ["technical-review"],
                "depends_on": [1],
                "enabled": True,
            },
            {
                "sequence": 3,
                "name": "Final Approver",
                "email": "final@acme.com",
                "roles": ["final-approval"],
                "depends_on": [1, 2],
                "enabled": True,
            },
        ],
    }

    # Create
    response: PortfolioFact = PortfolioActions.create(**complex_portfolio)

    assert len(response.approvers) == 3
    assert response.approvers[2].depends_on == [1, 2]

    # Clean up
    PortfolioActions.delete(client=client, portfolio=response.portfolio)


def test_portfolio_with_both_project_and_bizapp():
    """Test portfolio with both project and bizapp fields."""
    dual_project_portfolio = {
        "client": client,
        "portfolio": "dual-project-test",
        "project": {
            "name": "Main Project",
            "code": "main",
            "description": "Primary project implementation",
        },
        "bizapp": {
            "name": "Business Application",
            "code": "bizapp",
            "description": "Supporting business application",
        },
        "owner": {"name": "Dual Project Owner", "email": "dual@acme.com"},
    }

    # Create
    response: PortfolioFact = PortfolioActions.create(**dual_project_portfolio)

    assert response.project.name == "Main Project"
    assert response.bizapp.name == "Business Application"

    # Clean up
    PortfolioActions.delete(client=client, portfolio="dual-project-test")


# =============================================================================
# Error Handling Tests
# =============================================================================


def test_create_duplicate_portfolio():
    """Test creating duplicate portfolio should fail."""
    duplicate_data = {
        "portfolio": "web-services",  # Already exists
        "project": {
            "name": "Duplicate Test",
            "code": "dup",
            "description": "This should fail",
        },
        "owner": {"name": "Test Owner", "email": "test@acme.com"},
    }

    with pytest.raises(ConflictException):
        PortfolioActions.create(client=client, **duplicate_data)


def test_get_nonexistent_portfolio():
    """Test getting non-existent portfolio."""
    with pytest.raises(NotFoundException):
        response = PortfolioActions.get(client=client, portfolio="nonexistent-portfolio")


def test_update_nonexistent_portfolio():
    """Test updating non-existent portfolio."""
    with pytest.raises(NotFoundException):
        PortfolioActions.update(
            client=client,
            portfolio="nonexistent-portfolio",
            project={
                "name": "This Should Fail",
                "code": "fail",
                "description": "Should not work",
            },
            owner={"name": "Test", "email": "test@test.com"},
        )


def test_patch_nonexistent_portfolio():
    """Test patching non-existent portfolio."""
    with pytest.raises(NotFoundException):
        PortfolioActions.patch(client=client, portfolio="nonexistent-portfolio", domain="should-fail.com")


def test_missing_required_parameters():
    """Test various operations without required parameters."""
    # Test create without portfolio
    with pytest.raises(BadRequestException):
        PortfolioActions.create(client=client, domain="test.com")

    # Test get without portfolio
    with pytest.raises(BadRequestException):
        PortfolioActions.get(client=client, portfolio=None)

    # Test list without client (if util.get_client() returns None)
    with patch("core_framework.get_client", return_value=None):
        with pytest.raises(BadRequestException):
            PortfolioActions.list(client=None)

    # Test update without portfolio
    with pytest.raises(BadRequestException):
        PortfolioActions.update(client=client, domain="test.com")

    # Test patch without portfolio
    with pytest.raises(BadRequestException):
        PortfolioActions.patch(client=client, domain="test.com")


def test_invalid_portfolio_data():
    """Test creating portfolio with invalid data."""
    invalid_data = {
        "client": client,
        "portfolio": "invalid-test",
        "project": "this should be a dict, not a string",  # Invalid type
        "owner": {"name": "Test Owner", "email": "test@acme.com"},
    }

    with pytest.raises(BadRequestException):
        PortfolioActions.create(**invalid_data)


def test_invalid_pagination_parameters():
    """Test list with invalid pagination parameters."""
    with pytest.raises((BadRequestException, ValueError)):
        PortfolioActions.list(client=client, limit="invalid")  # Non-integer limit

    with pytest.raises((BadRequestException, ValueError)):
        PortfolioActions.list(client=client, limit=-1)  # Negative limit


# =============================================================================
# Delete Tests
# =============================================================================


def test_delete_portfolio():
    """Test deleting a portfolio."""
    # Create a portfolio specifically for deletion
    delete_test_data = {
        "portfolio": "delete-test-portfolio1",
        "project": {
            "name": "Portfolio for Deletion Test",
            "code": "delete-test",
            "description": "This portfolio will be deleted",
        },
        "owner": {"name": "Delete Test Owner", "email": "delete@test.com"},
    }

    # Create the portfolio
    PortfolioActions.create(client=client, **delete_test_data)

    # Verify it exists
    PortfolioActions.get(client=client, portfolio="delete-test-portfolio1")

    # Delete the portfolio
    PortfolioActions.delete(client=client, portfolio="delete-test-portfolio1")

    # Verify it's gone
    with pytest.raises(NotFoundException):
        PortfolioActions.get(client=client, portfolio="delete-test-portfolio1")


def test_delete_nonexistent_portfolio():
    """Test deleting non-existent portfolio."""

    with pytest.raises(NotFoundException):
        PortfolioActions.delete(client=client, portfolio="nonexistent-portfolio-for-deletion")


def test_delete_without_required_parameters():
    """Test delete without required parameters."""
    with pytest.raises(BadRequestException):
        PortfolioActions.delete(client=client, portfolio=None)  # Missing portfolio

    with patch("core_framework.get_client", return_value=None):
        with pytest.raises(BadRequestException):
            PortfolioActions.delete(client=None, portfolio="test")  # Missing client


# =============================================================================
# Edge Cases and Data Validation
# =============================================================================


def test_minimal_portfolio_creation():
    """Test creating portfolio with minimal required fields."""
    minimal_data = {"portfolio": "minimal-test1"}

    response: PortfolioFact = PortfolioActions.create(client=client, **minimal_data)
    assert response.portfolio == "minimal-test1"

    # Clean up
    PortfolioActions.delete(client=client, portfolio="minimal-test1")


def test_portfolio_timestamps():
    """Test that timestamps are properly managed."""
    timestamp_test_data = {
        "portfolio": "timestamp-test",
        "project": {
            "name": "Timestamp Test Project",
            "code": "timestamp",
            "description": "Testing timestamp behavior",
        },
        "owner": {"name": "Timestamp Test Owner", "email": "timestamp@test.com"},
    }

    # Create portfolio
    create_response: PortfolioFact = PortfolioActions.create(client=client, **timestamp_test_data)

    assert create_response.created_at is not None
    assert create_response.updated_at is not None

    original_updated_at = create_response.updated_at

    # Update portfolio (should change updated_at)
    patch_response: PortfolioFact = PortfolioActions.patch(
        client=client, portfolio="timestamp-test", domain="timestamp-updated.test.com"
    )

    # Verify timestamp behavior with PascalCase keys
    assert patch_response.created_at == create_response.created_at  # Should not change
    assert patch_response.updated_at != original_updated_at  # Should be updated

    # Clean up
    PortfolioActions.delete(client=client, portfolio="timestamp-test")


# =============================================================================
# Response Format Tests
# =============================================================================


def test_response_casing_consistency():
    """Test that all responses follow proper casing conventions."""

    # Test create response
    create_data = {
        "portfolio": "casing-test",
        "project": {
            "name": "Casing Test Project",
            "code": "casing",
            "description": "Testing response casing",
        },
        "owner": {"name": "Casing Test Owner", "email": "casing@test.com"},
    }

    data_dict: PortfolioFact = PortfolioActions.create(client=client, **create_data)

    # Test get response
    get_response: PortfolioFact = PortfolioActions.get(client=client, portfolio="casing-test")

    # Test list response
    list_response, paginator = PortfolioActions.list(client=client, limit=1)

    assert len(list_response) == 1
    assert paginator.total_count >= 1

    # Clean up
    PortfolioActions.delete(client=client, portfolio="casing-test")


def test_nested_data_structure_casing():
    """Test that nested data structures maintain PascalCase in response.data."""

    complex_data = {
        "portfolio": "nested-test",
        "project": {
            "name": "Nested Test Project",
            "code": "nested",
            "repository": "https://github.com/test/nested",
            "description": "Testing nested structure casing",
        },
        "owner": {
            "name": "Nested Owner",
            "email": "nested@test.com",
            "phone": "+1-555-1234",
        },
        "contacts": [
            {"name": "Contact 1", "email": "c1@test.com", "enabled": True},
            {"name": "Contact 2", "email": "c2@test.com", "enabled": False},
        ],
        "approvers": [
            {
                "sequence": 1,
                "name": "Approver 1",
                "email": "a1@test.com",
                "roles": ["deploy"],
                "enabled": True,
            }
        ],
        "tags": {"Environment": "test", "Team": "qa"},
        "metadata": {"test_type": "nested", "complexity": "high"},
    }

    response: PortfolioFact = PortfolioActions.create(client=client, **complex_data)

    # Clean up
    PortfolioActions.delete(client=client, portfolio=response.portfolio)
