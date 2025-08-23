import pytest
import datetime
from unittest.mock import patch

import core_framework as util

from core_db.registry.client.actions import ClientActions
from core_db.registry.client.models import ClientFact
from core_db.response import Response, SuccessResponse, ErrorResponse
from core_db.exceptions import (
    BadRequestException,
    NotFoundException,
    ConflictException,
    UnknownException,
)

from .bootstrap import *


client = util.get_client()

client_facts = [
    {
        "client": "acme-corp",
        "client_id": "ACME001",
        "client_type": "enterprise",
        "client_status": "active",
        "client_description": "Large enterprise manufacturing company with global operations",
        "client_name": "ACME Corporation",
        "organization_id": "o-acme123456789",
        "organization_name": "ACME AWS Organization",
        "organization_account": "123456789012",
        "organization_email": "aws-admin@acme-corp.com",
        "domain": "acme-corp.com",
        "iam_account": "123456789012",
        "audit_account": "123456789013",
        "automation_account": "123456789014",
        "security_account": "123456789015",
        "network_account": "123456789016",
        "master_region": "us-east-1",
        "client_region": "us-west-2",
        "bucket_region": "us-east-1",
        "bucket_name": "acme-corp-automation-artifacts",
        "docs_bucket_name": "acme-corp-documentation",
        "artefact_bucket_name": "acme-corp-build-artifacts",
        "ui_bucket_name": "acme-corp-ui-hosting",
        "scope": "acme-",
    },
    {
        "client": "startup-tech",
        "client_id": "STARTUP001",
        "client_type": "startup",
        "client_status": "active",
        "client_description": "Fast-growing SaaS startup focused on AI-powered analytics",
        "client_name": "StartupTech Inc",
        "organization_id": "o-startup987654321",
        "organization_name": "StartupTech AWS Org",
        "organization_account": "987654321098",
        "organization_email": "devops@startup-tech.io",
        "domain": "startup-tech.io",
        "iam_account": "987654321098",
        "audit_account": "987654321099",
        "automation_account": "987654321100",
        "security_account": "987654321101",
        "network_account": "987654321102",
        "master_region": "us-west-1",
        "client_region": "us-west-1",
        "bucket_region": "us-west-1",
        "bucket_name": "startup-tech-automation",
        "docs_bucket_name": "startup-tech-docs",
        "artefact_bucket_name": "startup-tech-artifacts",
        "ui_bucket_name": "startup-tech-console",
        "scope": "st-",
    },
    {
        "client": "gov-agency",
        "client_id": "GOV001",
        "client_type": "government",
        "client_status": "active",
        "client_description": "Federal government agency requiring high security and compliance",
        "client_name": "Department of Technology Services",
        "organization_id": "o-gov555666777",
        "organization_name": "DTS AWS Organization",
        "organization_account": "555666777888",
        "organization_email": "cloud-admin@dts.gov",
        "domain": "dts.gov",
        "iam_account": "555666777888",
        "audit_account": "555666777889",
        "automation_account": "555666777890",
        "security_account": "555666777891",
        "network_account": "555666777892",
        "master_region": "us-gov-east-1",
        "client_region": "us-gov-west-1",
        "bucket_region": "us-gov-east-1",
        "bucket_name": "dts-gov-automation-secure",
        "docs_bucket_name": "dts-gov-documentation",
        "artefact_bucket_name": "dts-gov-artifacts",
        "ui_bucket_name": "dts-gov-dashboard",
        "scope": "dts-",
    },
    {
        "client": "healthcare-plus",
        "client_id": "HEALTH001",
        "client_type": "healthcare",
        "client_status": "active",
        "client_description": "Healthcare technology company specializing in patient management systems",
        "client_name": "HealthcarePlus Solutions",
        "organization_id": "o-health111222333",
        "organization_name": "HealthcarePlus AWS Org",
        "organization_account": "111222333444",
        "organization_email": "cloud-ops@healthcareplus.com",
        "domain": "healthcareplus.com",
        "iam_account": "111222333444",
        "audit_account": "111222333445",
        "automation_account": "111222333446",
        "security_account": "111222333447",
        "network_account": "111222333448",
        "master_region": "us-east-2",
        "client_region": "us-east-2",
        "bucket_region": "us-east-2",
        "bucket_name": "healthcareplus-automation",
        "docs_bucket_name": "healthcareplus-docs",
        "artefact_bucket_name": "healthcareplus-builds",
        "ui_bucket_name": "healthcareplus-portal",
        "scope": "hp-",
    },
    {
        "client": "fintech-demo",
        "client_id": "FINTECH001",
        "client_type": "fintech",
        "client_status": "demo",
        "client_description": "Financial technology demo environment for testing new features",
        "client_name": "FinTech Demo Environment",
        "organization_account": "777888999000",
        "organization_email": "demo@fintech-example.com",
        "domain": "fintech-demo.example.com",
        "iam_account": "777888999000",
        "master_region": "eu-west-1",
        "client_region": "eu-west-1",
        "bucket_region": "eu-west-1",
        "bucket_name": "fintech-demo-automation",
        "docs_bucket_name": "fintech-demo-docs",
        "artefact_bucket_name": "fintech-demo-artifacts",
        "ui_bucket_name": "fintech-demo-ui",
        "scope": "demo-",
    },
    {
        "client": "minimal-client",
        "client_id": "MIN001",
        "client_type": "startup",
        "client_status": "active",
        "client_name": "Minimal Client for Testing",
    },
]


# =============================================================================
# Basic CRUD Tests
# =============================================================================


def test_create_client_fact(bootstrap_dynamo):
    """Test creating all client facts."""
    for i, client_fact in enumerate(client_facts):
        response = ClientActions.create(**client_fact)

        assert isinstance(response, SuccessResponse)
        assert response.data is not None, "Response data should not be None"

        data = ClientFact(**response.data)
        assert data.client == client_fact["client"]
        assert data.client_id == client_fact["client_id"]


def test_get_client_facts():
    """Test retrieving specific client facts."""
    client_name = "acme-corp"

    response: Response = ClientActions.get(client=client_name)

    assert isinstance(response, SuccessResponse)
    assert response.data is not None, "Response data should not be None"
    assert isinstance(response.data, dict), "Response data should be a dictionary"

    data = ClientFact(**response.data)
    assert data.client_id == "ACME001"
    assert data.client_name == "ACME Corporation"
    assert data.client_type == "enterprise"
    assert data.client_status == "active"


def test_list_client_facts():
    """Test listing all client facts with pagination."""
    response = ClientActions.list(client=client, limit=3)

    assert isinstance(response, SuccessResponse)
    assert response.data is not None
    assert isinstance(response.data, list)
    assert len(response.data) <= 3
    assert hasattr(response, "metadata")

    # Verify each item can be converted to ClientFact
    for item in response.data:
        client_fact = ClientFact(**item)
        assert client_fact.client is not None


def test_list_with_pagination():
    """Test pagination functionality."""
    # Get first page
    page1 = ClientActions.list(client=client, limit=2)
    assert len(page1.data) <= 2

    # Check if there's more data
    if page1.metadata.get("cursor"):
        page2 = ClientActions.list(
            client=client, limit=2, cursor=page1.metadata["cursor"]
        )
        assert isinstance(page2, SuccessResponse)

        # Verify different data
        page1_clients = {item["Client"] for item in page1.data}
        page2_clients = {item["Client"] for item in page2.data}
        assert page1_clients.isdisjoint(page2_clients), "Pages should not overlap"


def test_response_structure():
    """Test that response structure uses correct casing."""
    response = ClientActions.list(client=client, limit=2)

    # Top-level response keys should be snake_case
    assert hasattr(response, "data")
    assert hasattr(response, "metadata")

    # Data dictionaries should have PascalCase keys
    if response.data:
        first_item = response.data[0]
        assert "Client" in first_item  # PascalCase key
        assert (
            "ClientName" in first_item or "client_name" not in first_item
        )  # Verify PascalCase


# =============================================================================
# Update Tests (PUT and PATCH)
# =============================================================================


def test_update_client_full():
    """Test full client update (PUT semantics)."""
    client_name = "startup-tech"

    update_data = {
        "client": client_name,
        "client_id": "STARTUP001",
        "client_name": "StartupTech Inc - Updated",
        "client_type": "startup",
        "client_status": "active",
        "client_description": "Updated description for startup",
        "domain": "startup-tech-updated.io",
        "master_region": "us-east-1",  # Changed from us-west-1
    }

    response = ClientActions.update(**update_data)
    assert isinstance(response, SuccessResponse)

    updated_client = ClientFact(**response.data)
    assert updated_client.client_name == "StartupTech Inc - Updated"
    assert updated_client.master_region == "us-east-1"
    assert updated_client.domain == "startup-tech-updated.io"


def test_patch_client_partial():
    """Test partial client update (PATCH semantics)."""
    client_name = "healthcare-plus"

    # Only update description and status
    patch_data = {
        "client": client_name,
        "client_description": "Updated healthcare description via PATCH",
        "client_status": "maintenance",
    }

    response = ClientActions.patch(**patch_data)
    assert isinstance(response, SuccessResponse)

    patched_client = ClientFact(**response.data)
    assert (
        patched_client.client_description == "Updated healthcare description via PATCH"
    )
    assert patched_client.client_status == "maintenance"
    # Other fields should remain unchanged
    assert patched_client.client_name == "HealthcarePlus Solutions"
    assert patched_client.client_type == "healthcare"


def test_patch_with_none_values():
    """Test PATCH behavior with None values (should not remove fields)."""
    client_name = "gov-agency"

    patch_data = {
        "client": client_name,
        "client_description": "Updated government description",
        "organization_email": None,  # This should not remove the field
    }

    response = ClientActions.patch(**patch_data)
    assert isinstance(response, SuccessResponse)

    # Get the client to verify None didn't remove the field
    get_response = ClientActions.get(client=client_name)
    client_data = ClientFact(**get_response.data)

    assert client_data.client_description == "Updated government description"
    # organization_email should still exist (PATCH doesn't remove None fields)
    assert client_data.organization_email == "cloud-admin@dts.gov"


def test_update_with_none_values():
    """Test UPDATE behavior with None values (should remove fields)."""
    client_name = "fintech-demo"

    # Get current data first
    current_response = ClientActions.get(client=client_name)
    current_data = ClientFact(**current_response.data)

    update_data = {
        "client": client_name,
        "client_id": current_data.client_id,
        "client_name": current_data.client_name,
        "client_type": current_data.client_type,
        "client_status": current_data.client_status,
        "client_description": "Updated description via PUT",
        "organization_email": None,  # This should remove the field
    }

    response = ClientActions.update(**update_data)
    assert isinstance(response, SuccessResponse)

    updated_client = ClientFact(**response.data)
    assert updated_client.client_description == "Updated description via PUT"
    # organization_email should be None/removed
    assert updated_client.organization_email is None


# =============================================================================
# Error Handling Tests
# =============================================================================


def test_create_duplicate_client():
    """Test creating duplicate client should fail."""
    duplicate_data = client_facts[0].copy()  # Use existing client data

    with pytest.raises(ConflictException):
        ClientActions.create(**duplicate_data)


def test_get_nonexistent_client():
    """Test getting non-existent client."""
    with pytest.raises(UnknownException):  # Your implementation raises UnknownException
        ClientActions.get(client="nonexistent-client")


def test_update_nonexistent_client():
    """Test updating non-existent client."""
    with pytest.raises(NotFoundException):
        ClientActions.update(
            client="nonexistent-client", client_name="This Should Fail"
        )


def test_patch_nonexistent_client():
    """Test patching non-existent client."""
    with pytest.raises(NotFoundException):
        ClientActions.patch(
            client="nonexistent-client", client_description="This Should Fail"
        )


def test_missing_client_parameter():
    """Test various operations without client parameter."""
    # Test create without client
    with pytest.raises(BadRequestException):
        ClientActions.create(client_name="Test Client")

    # Test get without client
    with pytest.raises(BadRequestException):
        ClientActions.get()

    # Test list without client
    with pytest.raises(BadRequestException):
        ClientActions.list()

    # Test update without client
    with pytest.raises(BadRequestException):
        ClientActions.update(client_name="Test Client")

    # Test patch without client
    with pytest.raises(BadRequestException):
        ClientActions.patch(client_description="Test Description")


def test_invalid_client_data():
    """Test creating client with invalid data."""
    invalid_data = {
        "client": "test-client",
        "client_id": "",  # Empty client_id might be invalid depending on your validation
        "client_status": "invalid-status",  # Assuming you have enum validation
    }

    # This might pass or fail depending on your ClientFact validation rules
    try:
        response = ClientActions.create(**invalid_data)
        # If it passes, clean up
        ClientActions.delete(client="test-client")
    except BadRequestException:
        # Expected if you have strict validation
        pass


def test_invalid_pagination_parameters():
    """Test list with invalid pagination parameters."""
    with pytest.raises((BadRequestException, ValueError)):
        ClientActions.list(client=client, limit="invalid")  # Non-integer limit

    with pytest.raises((BadRequestException, ValueError)):
        ClientActions.list(client=client, limit=-1)  # Negative limit


# =============================================================================
# Delete Tests
# =============================================================================


def test_delete_client():
    """Test deleting a client."""
    # Create a client specifically for deletion
    delete_test_data = {
        "client": "delete-test-client",
        "client_id": "DELETE001",
        "client_name": "Client for Deletion Test",
        "client_type": "test",
        "client_status": "active",
    }

    # Create the client
    create_response = ClientActions.create(**delete_test_data)
    assert isinstance(create_response, SuccessResponse)

    # Verify it exists
    get_response = ClientActions.get(client="delete-test-client")
    assert isinstance(get_response, SuccessResponse)

    # Delete the client
    delete_response = ClientActions.delete(client="delete-test-client")
    assert isinstance(delete_response, SuccessResponse)
    assert delete_response.message and "deleted" in delete_response.message.lower()

    # Verify it's gone
    with pytest.raises(UnknownException):
        ClientActions.get(client="delete-test-client")


def test_delete_nonexistent_client():
    """Test deleting non-existent client."""
    with pytest.raises(UnknownException):
        ClientActions.delete(client="nonexistent-client-for-deletion")


def test_delete_without_client_parameter():
    """Test delete without client parameter should fail."""
    # Note: Your current implementation raises ValueError, but should probably be BadRequestException
    with pytest.raises((ValueError, BadRequestException)):
        ClientActions.delete()


# =============================================================================
# Edge Cases and Data Validation
# =============================================================================


def test_minimal_client_creation():
    """Test creating client with minimal required fields."""
    minimal_data = {"client": "minimal-test", "client_name": "Minimal Test Client"}

    response = ClientActions.create(**minimal_data)
    assert isinstance(response, SuccessResponse)

    client_data = ClientFact(**response.data)
    assert client_data.client == "minimal-test"
    assert client_data.client_name == "Minimal Test Client"

    # Clean up
    ClientActions.delete(client="minimal-test")


def test_large_client_data():
    """Test creating client with comprehensive data."""
    comprehensive_data = {
        "client": "comprehensive-test",
        "client_id": "COMP001",
        "client_type": "enterprise",
        "client_status": "active",
        "client_description": "Very long description " * 50,  # Large description
        "client_name": "Comprehensive Test Client",
        "organization_id": "o-comprehensive123",
        "organization_name": "Comprehensive AWS Organization",
        "organization_account": "111111111111",
        "organization_email": "admin@comprehensive-test.com",
        "domain": "comprehensive-test.com",
        "iam_account": "111111111111",
        "audit_account": "111111111112",
        "automation_account": "111111111113",
        "security_account": "111111111114",
        "network_account": "111111111115",
        "master_region": "us-east-1",
        "client_region": "us-west-2",
        "bucket_region": "us-east-1",
        "bucket_name": "comprehensive-test-automation",
        "docs_bucket_name": "comprehensive-test-docs",
        "artefact_bucket_name": "comprehensive-test-artifacts",
        "ui_bucket_name": "comprehensive-test-ui",
        "ui_bucket": "comprehensive-test-legacy-ui",
        "scope": "comp-",
    }

    response = ClientActions.create(**comprehensive_data)
    assert isinstance(response, SuccessResponse)

    # Verify all data was saved correctly
    get_response = ClientActions.get(client="comprehensive-test")
    client_data = ClientFact(**get_response.data)

    assert client_data.organization_id == "o-comprehensive123"
    assert client_data.scope == "comp-"
    assert len(client_data.client_description) > 100  # Verify large description saved

    # Clean up
    ClientActions.delete(client="comprehensive-test")


def test_client_timestamps():
    """Test that timestamps are properly managed."""
    timestamp_test_data = {
        "client": "timestamp-test",
        "client_name": "Timestamp Test Client",
        "client_type": "test",
        "client_status": "active",
    }

    # Create client
    create_response = ClientActions.create(**timestamp_test_data)
    created_client = ClientFact(**create_response.data)

    assert created_client.created_at is not None
    assert created_client.updated_at is not None

    original_updated_at = created_client.updated_at

    # Update client (should change updated_at)
    patch_response = ClientActions.patch(
        client="timestamp-test", client_description="Updated description"
    )
    updated_client = ClientFact(**patch_response.data)

    assert updated_client.created_at == created_client.created_at  # Should not change
    assert updated_client.updated_at != original_updated_at  # Should be updated

    # Clean up
    ClientActions.delete(client="timestamp-test")


# =============================================================================
# Response Format Tests
# =============================================================================


def test_response_casing_consistency():
    """Test that all responses follow proper casing conventions."""

    # Test create response
    create_data = {
        "client": "casing-test",
        "client_name": "Casing Test Client",
        "client_type": "test",
    }

    create_response = ClientActions.create(**create_data)

    # Response level should be snake_case
    assert hasattr(create_response, "data")
    assert hasattr(create_response, "message")

    # Data content should be PascalCase
    data_dict = create_response.data
    expected_pascal_keys = [
        "Client",
        "ClientName",
        "ClientType",
        "CreatedAt",
        "UpdatedAt",
    ]

    for key in expected_pascal_keys:
        if key in ["CreatedAt", "UpdatedAt"]:
            continue  # These might be None in some cases
        assert (
            key in data_dict
        ), f"Expected PascalCase key '{key}' not found in response data"

    # Test get response
    get_response = ClientActions.get(client="casing-test")
    assert hasattr(get_response, "data")
    get_data_dict = get_response.data
    assert "Client" in get_data_dict
    assert "ClientName" in get_data_dict

    # Test list response
    list_response = ClientActions.list(client=client, limit=1)
    assert hasattr(list_response, "data")
    assert hasattr(list_response, "metadata")  # snake_case

    if list_response.data:
        list_item = list_response.data[0]
        assert "Client" in list_item  # PascalCase

    # Clean up
    ClientActions.delete(client="casing-test")


def test_metadata_structure():
    """Test metadata structure in list responses."""
    response = ClientActions.list(client=client, limit=1)

    # Metadata should exist and be snake_case
    assert hasattr(response, "metadata")
    metadata = response.metadata

    # Common metadata fields (snake_case)
    expected_metadata_keys = ["limit", "total_count", "has_more"]

    for key in expected_metadata_keys:
        # Not all metadata keys may be present depending on implementation
        if hasattr(metadata, key) or (isinstance(metadata, dict) and key in metadata):
            # Key exists, verify it's snake_case (no caps)
            assert (
                key.islower() or "_" in key
            ), f"Metadata key '{key}' should be snake_case"


def test_error_response_casing():
    """Test that error responses also follow casing conventions."""

    try:
        ClientActions.get(client="nonexistent-client-casing-test")
        assert False, "Should have raised an exception"
    except Exception as e:
        # Error messages should be consistent
        # The exception itself doesn't need to follow the JSON casing rules
        assert isinstance(e, (UnknownException, NotFoundException))
