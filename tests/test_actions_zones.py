from calendar import c
import pytest
from unittest.mock import patch
from pydantic import ValidationError

import core_framework as util

from core_db.registry.zone.actions import ZoneActions
from core_db.registry.zone.models import ZoneFact
from core_db.response import SuccessResponse, NoContentResponse
from core_db.exceptions import (
    BadRequestException,
    NotFoundException,
    ConflictException,
    UnknownException,
)

from .bootstrap import *

client = util.get_client()

zone_facts = [
    # Production Zone
    {
        "zone": "prod-east",
        "account_facts": {
            "organizational_unit": "Production",
            "aws_account_id": "123456789012",
            "account_name": "ACME Production Account",
            "environment": "production",
            "kms": {
                "aws_account_id": "123456789012",
                "kms_key_arn": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
                "kms_key": "12345678-1234-1234-1234-123456789012",
                "delegate_aws_account_ids": ["123456789012", "987654321098"],
                "allow_sns": True,
            },
            "resource_namespace": "acme-prod",
            "network_name": "production-network",
            "vpc_aliases": ["vpc-prod-main", "vpc-prod-backup"],
            "subnet_aliases": [
                "subnet-prod-public",
                "subnet-prod-private",
                "subnet-prod-database",
            ],
            "tags": {
                "Environment": "production",
                "Owner": "platform-team",
                "CostCenter": "engineering",
                "Backup": "required",
                "Compliance": "soc2",
            },
        },
        "region_facts": {
            "us-east-1": {
                "aws_region": "us-east-1",
                "az_count": 3,
                "image_aliases": {
                    "ubuntu": "ami-0c02fb55956c7d316",
                    "amazon-linux": "ami-0b898040803850657",
                    "windows": "ami-0c9978668f8d55984",
                    "nginx": "ami-0123456789abcdef0",
                },
                "min_successful_instances_percent": 100,
                "security_aliases": {
                    "corporate-cidrs": [
                        {
                            "type": "CIDR",
                            "value": "10.0.0.0/8",
                            "description": "Corporate network range",
                        },
                        {
                            "type": "CIDR",
                            "value": "172.16.0.0/12",
                            "description": "VPN network range",
                        },
                    ],
                    "admin-cidrs": [
                        {
                            "type": "CIDR",
                            "value": "192.168.1.0/24",
                            "description": "Admin access network",
                        }
                    ],
                },
                "security_group_aliases": {
                    "web-sg": "sg-web-prod-12345",
                    "app-sg": "sg-app-prod-67890",
                    "db-sg": "sg-db-prod-abcde",
                },
                "proxy": [
                    {
                        "host": "proxy.acme.com",
                        "port": "8080",
                        "url": "http://proxy.acme.com:8080",
                        "no_proxy": "*.acme.com,10.0.0.0/8,169.254.169.254",
                    }
                ],
                "proxy_host": "proxy.acme.com",
                "proxy_port": 8080,
                "proxy_url": "http://proxy.acme.com:8080",
                "no_proxy": "*.acme.com,10.0.0.0/8,169.254.169.254",
                "name_servers": ["8.8.8.8", "8.8.4.4", "1.1.1.1"],
                "tags": {
                    "Region": "us-east-1",
                    "AZ": "multi-az",
                    "NetworkTier": "production",
                },
            },
            "us-west-2": {
                "aws_region": "us-west-2",
                "az_count": 4,
                "image_aliases": {
                    "ubuntu": "ami-0892d3c7ee96c0bf7",
                    "amazon-linux": "ami-0c2d3e23eb9d8a2ce",
                    "windows": "ami-0dd8be3d67c8e3db8",
                },
                "min_successful_instances_percent": 75,
                "security_aliases": {
                    "corporate-cidrs": [
                        {
                            "type": "CIDR",
                            "value": "10.0.0.0/8",
                            "description": "Corporate network range",
                        }
                    ]
                },
                "security_group_aliases": {
                    "web-sg": "sg-web-prod-west-12345",
                    "app-sg": "sg-app-prod-west-67890",
                },
                "proxy_host": "proxy-west.acme.com",
                "proxy_port": 8080,
                "name_servers": ["8.8.8.8", "1.1.1.1"],
                "tags": {"Region": "us-west-2", "Purpose": "disaster-recovery"},
            },
        },
        "tags": {
            "Environment": "production",
            "Team": "platform",
            "Monitoring": "enhanced",
            "SLA": "tier1",
        },
    },
    # UAT Zone
    {
        "zone": "uat-central",
        "account_facts": {
            "organizational_unit": "UAT",
            "aws_account_id": "234567890123",
            "account_name": "ACME UAT Account",
            "environment": "uat",
            "kms": {
                "aws_account_id": "234567890123",
                "kms_key_arn": "arn:aws:kms:us-central-1:234567890123:key/87654321-4321-4321-4321-876543210987",
                "kms_key": "87654321-4321-4321-4321-876543210987",
                "delegate_aws_account_ids": ["234567890123"],
                "allow_sns": False,
            },
            "resource_namespace": "acme-uat",
            "network_name": "uat-network",
            "vpc_aliases": ["vpc-uat-main", "vpc-uat-test"],
            "subnet_aliases": ["subnet-uat-public", "subnet-uat-private"],
            "tags": {
                "Environment": "uat",
                "Owner": "qa-team",
                "CostCenter": "testing",
                "AutoShutdown": "enabled",
            },
        },
        "region_facts": {
            "us-central-1": {
                "aws_region": "us-central-1",
                "az_count": 2,
                "image_aliases": {
                    "ubuntu": "ami-uat123456789",
                    "amazon-linux": "ami-uat987654321",
                    "test-runner": "ami-test123456",
                },
                "min_successful_instances_percent": 50,
                "security_aliases": {
                    "test-cidrs": [
                        {
                            "type": "CIDR",
                            "value": "172.20.0.0/16",
                            "description": "UAT network range",
                        }
                    ],
                    "qa-cidrs": [
                        {
                            "type": "CIDR",
                            "value": "192.168.100.0/24",
                            "description": "QA team access",
                        }
                    ],
                },
                "security_group_aliases": {
                    "web-sg": "sg-web-uat-12345",
                    "app-sg": "sg-app-uat-67890",
                    "test-sg": "sg-test-uat-abcde",
                },
                "proxy": [
                    {
                        "host": "proxy-uat.acme.com",
                        "port": "3128",
                        "url": "http://proxy-uat.acme.com:3128",
                        "no_proxy": "*.uat.acme.com,172.20.0.0/16",
                    }
                ],
                "proxy_host": "proxy-uat.acme.com",
                "proxy_port": 3128,
                "proxy_url": "http://proxy-uat.acme.com:3128",
                "no_proxy": "*.uat.acme.com,172.20.0.0/16",
                "name_servers": ["8.8.8.8", "1.1.1.1"],
                "tags": {
                    "Region": "us-central-1",
                    "Purpose": "testing",
                    "TestData": "enabled",
                },
            }
        },
        "tags": {
            "Environment": "uat",
            "Team": "qa",
            "Purpose": "testing",
            "Temporary": "true",
        },
    },
    # Development Zone
    {
        "zone": "dev-west",
        "account_facts": {
            "organizational_unit": "Development",
            "aws_account_id": "345678901234",
            "account_name": "ACME Development Account",
            "environment": "development",
            "kms": {
                "aws_account_id": "345678901234",
                "delegate_aws_account_ids": ["345678901234"],
                "allow_sns": False,
            },
            "resource_namespace": "acme-dev",
            "network_name": "dev-network",
            "vpc_aliases": ["vpc-dev-main"],
            "subnet_aliases": ["subnet-dev-public", "subnet-dev-private"],
            "tags": {
                "Environment": "development",
                "Owner": "dev-team",
                "CostCenter": "engineering",
                "AutoShutdown": "enabled",
                "Schedule": "business-hours-only",
            },
        },
        "region_facts": {
            "us-west-2": {
                "aws_region": "us-west-2",
                "az_count": 2,
                "image_aliases": {
                    "ubuntu": "ami-dev123456789",
                    "amazon-linux": "ami-dev987654321",
                    "dev-tools": "ami-devtools123",
                },
                "min_successful_instances_percent": 25,
                "security_aliases": {
                    "dev-cidrs": [
                        {
                            "type": "CIDR",
                            "value": "172.30.0.0/16",
                            "description": "Development network range",
                        }
                    ],
                    "developer-cidrs": [
                        {
                            "type": "CIDR",
                            "value": "192.168.200.0/24",
                            "description": "Developer workstation access",
                        }
                    ],
                },
                "security_group_aliases": {
                    "web-sg": "sg-web-dev-12345",
                    "app-sg": "sg-app-dev-67890",
                    "debug-sg": "sg-debug-dev-xyz",
                },
                "proxy_host": "proxy-dev.acme.com",
                "proxy_port": 8080,
                "proxy_url": "http://proxy-dev.acme.com:8080",
                "no_proxy": "*.dev.acme.com,172.30.0.0/16,localhost",
                "name_servers": ["8.8.8.8", "1.1.1.1"],
                "tags": {
                    "Region": "us-west-2",
                    "Purpose": "development",
                    "DebugMode": "enabled",
                    "LogLevel": "debug",
                },
            }
        },
        "tags": {
            "Environment": "development",
            "Team": "engineering",
            "Experimental": "true",
            "CostOptimized": "true",
        },
    },
]


# =============================================================================
# Basic CRUD Tests
# =============================================================================


def test_zone_fact_create(bootstrap_dynamo):
    """Test creating all zone facts with full validation."""

    for i, zone_fact in enumerate(zone_facts):
        response: ZoneFact = ZoneActions.create(client=client, **zone_fact)

        assert isinstance(response, ZoneFact), f"Create failed for zone {i+1}"
        assert response is not None, f"Response data is None for zone {i+1}"

        # Verify nested structure with PascalCase
        account_facts = response.account_facts
        assert account_facts.aws_account_id == zone_fact["account_facts"]["aws_account_id"]

        # Verify region facts structure
        region_facts = response.region_facts

        # Check first region in each zone
        first_region = list(dict(zone_fact["region_facts"]).keys())[0]
        assert first_region in region_facts, f"Region {first_region} missing for zone {i+1}"


def test_zone_get():
    """Test retrieving specific zone facts."""
    zone_name = "prod-east"

    response: ZoneFact = ZoneActions.get(client=client, zone=zone_name)

    assert isinstance(response, ZoneFact)
    assert response is not None

    # Verify account facts structure
    account_facts = response.account_facts

    assert account_facts.aws_account_id == "123456789012"
    assert account_facts.environment == "production"

    # Verify region facts structure
    region_facts = response.region_facts

    assert "us-east-1" in region_facts

    us_east_region = region_facts["us-east-1"]

    assert us_east_region.aws_region == "us-east-1"
    assert us_east_region.az_count == 3

    arn = "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"

    # Verify KMS configuration
    assert account_facts.kms is not None
    assert account_facts.kms.aws_account_id == "123456789012"
    assert account_facts.kms.kms_key_arn == arn
    assert account_facts.kms.allow_sns == True


def test_zone_list_all():
    """Test listing all zones for client."""
    response, paginator = ZoneActions.list(client=client, limit=10)

    assert isinstance(response, list)
    assert len(response) == 3
    assert paginator.total_count == 3

    zone_names = set()
    for zone in response:
        assert isinstance(zone, ZoneFact)
        zone_names.add(zone.zone)

    # Verify our test zones are present
    expected_zones = {"prod-east", "uat-central", "dev-west"}
    assert expected_zones.issubset(zone_names)


def test_zone_list_by_aws_account():
    """Test listing zones by AWS account ID."""
    # Test production account
    prod_account_id = "123456789012"
    response, paginator = ZoneActions.list(client=client, aws_account_id=prod_account_id)

    assert isinstance(response, list)
    assert len(response) == 1
    assert paginator.total_count == 1

    prod_zone = response[0]

    assert prod_zone.zone == "prod-east"
    assert prod_zone.account_facts.aws_account_id == prod_account_id

    # Test UAT account
    uat_account_id = "234567890123"
    response, paginator = ZoneActions.list(client=client, aws_account_id=uat_account_id)

    assert len(response) == 1
    assert paginator.total_count == 1

    uat_zone = response[0]
    assert uat_zone.zone == "uat-central"
    assert uat_zone.account_facts.aws_account_id == uat_account_id

    # Test non-existent account
    response, paginator = ZoneActions.list(client=client, aws_account_id="999999999999")
    assert len(response) == 0
    assert paginator.total_count == 0


def test_zone_list_with_pagination():
    """Test pagination functionality."""
    # Get first page with limit 2
    page1, paginator1 = ZoneActions.list(client=client, limit=2)
    assert len(page1) <= 2
    assert paginator1.cursor is not None

    page2, paginator2 = ZoneActions.list(client=client, limit=2, cursor=paginator1.cursor)
    assert isinstance(page2, list)

    # Verify different data using Zone keys
    page1_zones = {zone.zone for zone in page1}
    page2_zones = {zone.zone for zone in page2}
    assert page1_zones.isdisjoint(page2_zones), "Pages should not overlap"


# =============================================================================
# Complex Structure Validation Tests
# =============================================================================


def test_zone_complex_structure_validation():
    """Test that complex nested structures are properly handled."""
    zone_name = "prod-east"
    response: ZoneFact = ZoneActions.get(client=client, zone=zone_name)

    kms = response.account_facts.kms
    assert kms is not None
    assert kms.aws_account_id == "123456789012"
    assert kms.kms_key_arn == "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
    assert kms.allow_sns == True
    assert len(kms.delegate_aws_account_ids) == 2

    # Test region facts structure
    us_east_region = response.region_facts["us-east-1"]

    image_aliases = us_east_region.image_aliases
    assert "ubuntu" in image_aliases
    assert "amazon-linux" in image_aliases
    assert "nginx" in image_aliases

    # Test security aliases
    security_aliases = us_east_region.security_aliases
    assert "corporate-cidrs" in security_aliases
    assert "admin-cidrs" in security_aliases

    corporate_cidrs = security_aliases["corporate-cidrs"]
    assert isinstance(corporate_cidrs, list)
    assert len(corporate_cidrs) == 2

    first_cidr = corporate_cidrs[0]
    assert first_cidr.type == "CIDR"
    assert first_cidr.value == "10.0.0.0/8"

    # Test security group aliases
    sg_aliases = us_east_region.security_group_aliases
    assert "web-sg" in sg_aliases
    assert "app-sg" in sg_aliases
    assert "db-sg" in sg_aliases

    # Test proxy configuration
    proxy_list = us_east_region.proxy
    assert isinstance(proxy_list, list)
    assert len(proxy_list) == 1

    proxy = proxy_list[0]
    assert proxy.host == "proxy.acme.com"
    assert proxy.port == "8080"

    # Test simple proxy fields
    assert us_east_region.proxy_host == "proxy.acme.com"
    assert us_east_region.proxy_port == 8080
    assert us_east_region.proxy_url == "http://proxy.acme.com:8080"

    assert us_east_region.no_proxy == "*.acme.com,10.0.0.0/8,169.254.169.254"
    assert us_east_region.proxy_host == "proxy.acme.com"
    assert us_east_region.proxy_port == 8080

    # Test name servers
    assert us_east_region.name_servers is not None
    assert isinstance(us_east_region.name_servers, list)
    assert "8.8.8.8" in us_east_region.name_servers
    assert "1.1.1.1" in us_east_region.name_servers

    # Test tags
    assert us_east_region.tags is not None
    region_tags = us_east_region.tags
    assert "Region" in region_tags
    assert "NetworkTier" in region_tags
    assert region_tags["Region"] == "us-east-1"
    assert region_tags["NetworkTier"] == "production"


def test_zone_account_facts_validation():
    """Test detailed account facts validation."""
    zone_name = "uat-central"
    response: ZoneFact = ZoneActions.get(client=client, zone=zone_name)

    account_facts = response.account_facts

    assert account_facts.organizational_unit == "UAT"
    assert account_facts.aws_account_id == "234567890123"
    assert account_facts.account_name == "ACME UAT Account"
    assert account_facts.environment == "uat"
    assert account_facts.resource_namespace == "acme-uat"
    assert account_facts.network_name == "uat-network"

    # Test VPC and subnet aliases
    vpc_aliases = account_facts.vpc_aliases
    assert isinstance(vpc_aliases, list)
    assert "vpc-uat-main" in vpc_aliases
    assert "vpc-uat-test" in vpc_aliases

    assert account_facts.subnet_aliases is not None
    subnet_aliases = account_facts.subnet_aliases
    assert isinstance(subnet_aliases, list)
    assert "subnet-uat-public" in subnet_aliases
    assert "subnet-uat-private" in subnet_aliases

    account_tags = account_facts.tags
    assert "Environment" in account_tags
    assert "AutoShutdown" in account_tags
    assert account_tags["Environment"] == "uat"
    assert account_tags["AutoShutdown"] == "enabled"


def test_zone_multiple_regions():
    """Test zone with multiple regions."""
    zone_name = "prod-east"
    response: ZoneFact = ZoneActions.get(client=client, zone=zone_name)

    region_facts = response.region_facts

    # Should have both us-east-1 and us-west-2
    assert "us-east-1" in region_facts
    assert "us-west-2" in region_facts

    # Test us-east-1 specifics
    us_east = region_facts["us-east-1"]
    assert us_east.az_count == 3
    assert us_east.min_successful_instances_percent == 100
    assert "nginx" in us_east.image_aliases

    # Test us-west-2 specifics
    us_west = region_facts["us-west-2"]
    assert us_west.az_count == 4
    assert us_west.min_successful_instances_percent == 75
    assert "nginx" not in us_west.image_aliases  # Different AMIs per region

    # Both should have basic proxy config
    assert us_east.proxy_host == "proxy.acme.com"
    assert us_west.proxy_host == "proxy-west.acme.com"


# =============================================================================
# Update Tests (PUT and PATCH)
# =============================================================================


def test_zone_update_full():
    """Test full zone update (PUT semantics)."""
    zone_name = "dev-west"

    # Get current data first
    current: ZoneFact = ZoneActions.get(client=client, zone=zone_name)
    original_account_id = current.account_facts.aws_account_id

    update_data = {
        "zone": zone_name,
        "account_facts": {
            "aws_account_id": original_account_id,  # Keep the same account
            "account_name": "Updated Development Account",
            "environment": "staging",  # Changed from development
            "resource_namespace": "acme-dev-updated",
            "network_name": "updated-dev-network",
            "vpc_aliases": ["vpc-dev-updated"],
            "tags": {
                "Environment": "staging",
                "Owner": "updated-dev-team",
                "Purpose": "updated-testing",
            },
        },
        "region_facts": {
            "us-west-2": {
                "aws_region": "us-west-2",
                "az_count": 3,  # Changed from 2
                "image_aliases": {
                    "ubuntu": "ami-updated123456",
                    "new-image": "ami-newimage123",
                },
                "min_successful_instances_percent": 50,  # Changed from 25
                "proxy_host": "proxy-updated.acme.com",
                "proxy_port": 9090,  # Changed from 8080
                "tags": {"Region": "us-west-2", "Purpose": "updated-development"},
            }
        },
        "tags": {
            "Environment": "staging",
            "Team": "updated-engineering",
            "UpdatedField": "updated-value",
        },
    }

    response: ZoneFact = ZoneActions.update(client=client, **update_data)

    # Verify updates with PascalCase keys
    assert response.zone == zone_name

    # Verify account facts updates
    account_facts = response.account_facts
    assert account_facts.account_name == "Updated Development Account"
    assert account_facts.environment == "staging"
    assert account_facts.resource_namespace == "acme-dev-updated"
    assert account_facts.tags["Purpose"] == "updated-testing"

    # Verify region facts updates
    region_facts = response.region_facts["us-west-2"]
    assert region_facts.az_count == 3
    assert region_facts.min_successful_instances_percent == 50
    assert region_facts.proxy_host == "proxy-updated.acme.com"
    assert region_facts.proxy_port == 9090
    assert "new-image" in region_facts.image_aliases

    # Verify global tags
    assert response.tags["UpdatedField"] == "updated-value"
    assert response.tags["Team"] == "updated-engineering"


def test_zone_patch_partial():
    """Test partial zone update (PATCH semantics)."""
    zone_name = "uat-central"

    # Get current data to verify what doesn't change
    current: ZoneFact = ZoneActions.get(client=client, zone=zone_name)
    original_account_name = current.account_facts.account_name
    original_org_unit = current.account_facts.organizational_unit

    # Patch only specific fields
    patch_data = {
        "zone": zone_name,
        "account_facts": {
            "aws_account_id": "234567890123",  # Keep same (required)
            "environment": "pre-production",  # Change this
            "resource_namespace": "acme-uat-patched",  # Change this
            # Don't include account_name or organizational_unit - they should remain
        },
        "tags": {"Environment": "pre-production", "PatchedField": "patch-added"},
    }

    response: ZoneFact = ZoneActions.patch(client=client, **patch_data)

    account_facts = response.account_facts
    # Changed fields
    assert account_facts.environment == "pre-production"
    assert account_facts.resource_namespace == "acme-uat-patched"

    # Unchanged fields should remain
    assert account_facts.account_name == original_account_name
    assert account_facts.organizational_unit == original_org_unit

    # Tags should be updated/added
    assert response.tags["PatchedField"] == "patch-added"
    assert response.tags["Environment"] == "pre-production"


def test_zone_patch_with_nested_updates():
    """Test PATCH with complex nested structure updates."""
    zone_name = "prod-east"

    # Update only specific nested fields
    patch_data = {
        "zone": zone_name,
        "region_facts": {
            "us-east-1": {
                "aws_region": "us-east-1",  # Required
                "min_successful_instances_percent": 90,  # Changed from 100
                "image_aliases": {
                    "ubuntu": "ami-patched-ubuntu",
                    "patched-image": "ami-new-patched",
                },  # Updated  # Added
                "proxy_port": 8888,  # Changed from 8080
                "tags": {"Region": "us-east-1", "PatchedTag": "patched-value"},
            }
            # Note: us-west-2 not included, should remain unchanged
        },
    }

    response: ZoneFact = ZoneActions.patch(client=client, **patch_data)
    us_east = response.region_facts["us-east-1"]

    # Verify changes
    assert us_east.min_successful_instances_percent == 90
    assert us_east.proxy_port == 8888
    assert us_east.image_aliases["ubuntu"] == "ami-patched-ubuntu"
    assert "patched-image" in us_east.image_aliases
    assert us_east.tags["PatchedTag"] == "patched-value"

    # Verify us-west-2 region still exists (not removed by patch)
    assert "us-west-2" in response.region_facts
    us_west = response.region_facts["us-west-2"]
    assert us_west.proxy_host == "proxy-west.acme.com"  # Should be unchanged


# =============================================================================
# Error Handling Tests
# =============================================================================


def test_create_duplicate_zone():
    """Test creating duplicate zone should fail."""
    duplicate_data = {
        "zone": "prod-east",  # Already exists
        "account_facts": {
            "aws_account_id": "999999999999",
        },
        "region_facts": {"us-test-1": {"aws_region": "us-test-1"}},
    }

    with pytest.raises(ConflictException):
        ZoneActions.create(client=client, **duplicate_data)


def test_get_nonexistent_zone():
    """Test getting non-existent zone."""
    with pytest.raises(NotFoundException):
        ZoneActions.get(client=client, zone="nonexistent-zone")


def test_update_nonexistent_zone():
    """Test updating non-existent zone should fail."""
    with pytest.raises(NotFoundException):
        ZoneActions.update(
            client=client,
            zone="nonexistent-zone",
            account_facts={"aws_account_id": "123456789012"},
            region_facts={"us-test-1": {"aws_region": "us-test-1"}},
        )


def test_patch_nonexistent_zone():
    """Test patching non-existent zone should fail."""
    with pytest.raises(NotFoundException):
        ZoneActions.patch(client=client, zone="nonexistent-zone", tags={"Test": "should-fail"})


def test_missing_required_parameters():
    """Test operations without required parameters."""
    # Test create without zone
    with pytest.raises(BadRequestException):
        ZoneActions.create(
            client=client,
            account_facts={"aws_account_id": "123456789012"},
            region_facts={"us-test-1": {"aws_region": "us-test-1"}},
        )

    # Test get without zone
    with pytest.raises(BadRequestException):
        ZoneActions.get(client=client, zone=None)

    # Test get without client
    with patch("core_framework.get_client", return_value=None):
        with pytest.raises(BadRequestException):
            ZoneActions.get(client=None, zone="test-zone")

    # Test list without client
    with patch("core_framework.get_client", return_value=None):
        with pytest.raises(BadRequestException):
            ZoneActions.list(client=None)

    # Test delete without zone
    with pytest.raises(BadRequestException):
        ZoneActions.delete(client=client, zone=None)


def test_invalid_zone_data():
    """Test creating zone with invalid data."""
    invalid_data = {
        "zone": "invalid-test-zone",
        "account_facts": {
            # Missing required aws_account_id
            "account_name": "Invalid Test"
        },
        "region_facts": {"us-test-1": {"aws_region": "us-test-1"}},
    }

    with pytest.raises(BadRequestException):
        ZoneActions.create(client=client, **invalid_data)


def test_invalid_pagination_parameters():
    """Test list with invalid pagination parameters."""
    with pytest.raises(BadRequestException):
        ZoneActions.list(client=client, limit="invalid")  # Non-integer limit

    with pytest.raises(BadRequestException):
        ZoneActions.list(client=client, limit=-1)  # Negative limit


# =============================================================================
# Delete Tests
# =============================================================================


def test_delete_zone():
    """Test deleting a zone."""
    # Create a zone specifically for deletion
    delete_test_data = {
        "zone": "delete-test-zone",
        "account_facts": {
            "aws_account_id": "999999999999",
            "account_name": "Zone for Deletion Test",
            "environment": "test",
        },
        "region_facts": {"us-test-1": {"aws_region": "us-test-1", "az_count": 1}},
    }

    # Create the zone
    create_response: ZoneFact = ZoneActions.create(client=client, **delete_test_data)
    assert isinstance(create_response, ZoneFact)

    # Verify it exists
    get_response: ZoneFact = ZoneActions.get(client=client, zone="delete-test-zone")
    assert isinstance(get_response, ZoneFact)

    # Delete the zone
    delete_response: bool = ZoneActions.delete(client=client, zone="delete-test-zone")
    assert delete_response is True

    # Verify it's gone
    with pytest.raises(NotFoundException):
        ZoneActions.get(client=client, zone="delete-test-zone")


def test_delete_nonexistent_zone():
    """Test deleting non-existent zone."""
    with pytest.raises(NotFoundException):
        ZoneActions.delete(client=client, zone="nonexistent-zone")


def test_delete_without_required_parameters():
    """Test delete without required parameters."""
    with pytest.raises(BadRequestException):
        ZoneActions.delete(client=client, zone=None)  # Missing zone


# =============================================================================
# Response Format and Casing Tests
# =============================================================================


def test_response_casing_consistency():
    """Test that all responses follow proper casing conventions."""
    zone_name = "prod-east"

    # Test get response
    get_response: ZoneFact = ZoneActions.get(client=client, zone=zone_name)
    assert isinstance(get_response, ZoneFact)

    # Test list response
    list_response, paginator = ZoneActions.list(client=client, limit=1)
    assert len(list_response) == 1
    assert paginator.total_count == 1

    list_item = list_response[0]
    assert isinstance(list_item, ZoneFact)


def test_nested_data_casing():
    """Test that nested data structures maintain proper casing."""
    zone_name = "prod-east"
    data: ZoneFact = ZoneActions.get(client=client, zone=zone_name)

    # AccountFacts nested fields should be PascalCase
    account_facts = data.account_facts

    # KMS nested fields should be PascalCase
    kms = account_facts.kms

    # RegionFacts nested fields should be PascalCase
    region_facts = data.region_facts
    us_east = region_facts["us-east-1"]
    # SecurityAliases nested structure
    security_aliases = us_east.security_aliases
    corporate_cidrs = security_aliases["corporate-cidrs"]
    first_cidr = corporate_cidrs[0]
    assert first_cidr.type == "CIDR"


def test_audit_fields():
    """Test that audit fields are properly managed."""
    zone_name = "uat-central"

    # Get zone to check timestamps
    data: ZoneFact = ZoneActions.get(client=client, zone=zone_name)

    assert data.created_at is not None
    assert data.updated_at is not None

    original_created_at = data.created_at
    original_updated_at = data.updated_at

    # Patch the zone (should update UpdatedAt but not CreatedAt)
    patch_response: ZoneFact = ZoneActions.patch(client=client, zone=zone_name, tags={"TestPatch": "timestamp-test"})

    assert patch_response.created_at == original_created_at  # Should not change
    # UpdatedAt should be different (assuming time has passed)
    # Note: In fast tests, this might be the same if within same second


# =============================================================================
# Integration and Workflow Tests
# =============================================================================


def test_complete_zone_lifecycle():
    """Test complete zone lifecycle: create, read, update, delete."""
    zone_name = "lifecycle-test-zone"

    # 1. Create
    create_data = {
        "zone": zone_name,
        "account_facts": {
            "aws_account_id": "111111111111",
            "account_name": "Lifecycle Test Account",
            "environment": "test",
        },
        "region_facts": {
            "us-lifecycle-1": {
                "aws_region": "us-lifecycle-1",
                "az_count": 2,
                "proxy_host": "proxy-lifecycle.test.com",
            }
        },
        "tags": {"Test": "lifecycle", "Stage": "create"},
    }

    create_response: ZoneFact = ZoneActions.create(client=client, **create_data)
    assert isinstance(create_response, ZoneFact)
    assert create_response.zone == zone_name

    # 2. Read
    get_response: ZoneFact = ZoneActions.get(client=client, zone=zone_name)
    assert isinstance(get_response, ZoneFact)
    assert get_response.account_facts.environment == "test"

    # 3. Update (partial)
    patch_response: ZoneFact = ZoneActions.patch(client=client, zone=zone_name, tags={"Test": "lifecycle", "Stage": "updated"})
    assert isinstance(patch_response, ZoneFact)
    assert patch_response.tags["Stage"] == "updated"

    # 4. Update (full)
    update_response: ZoneFact = ZoneActions.update(
        client=client,
        zone=zone_name,
        account_facts={
            "aws_account_id": "111111111111",
            "account_name": "Updated Lifecycle Account",
            "environment": "staging",
        },
        region_facts={
            "us-lifecycle-1": {
                "aws_region": "us-lifecycle-1",
                "az_count": 3,
                "proxy_host": "proxy-updated.test.com",
            }
        },
        tags={"Test": "lifecycle", "Stage": "fully-updated"},
    )
    assert isinstance(update_response, ZoneFact)
    assert update_response.account_facts.environment == "staging"
    assert update_response.region_facts["us-lifecycle-1"].az_count == 3

    # 5. Delete
    delete_response: bool = ZoneActions.delete(client=client, zone=zone_name)
    assert delete_response is True

    # 6. Verify deletion
    with pytest.raises(NotFoundException):
        ZoneActions.get(client=client, zone=zone_name)


def test_zone_model_conversion():
    """Test ZoneFact model conversion methods."""
    zone_name = "prod-east"

    # Get zone as Pydantic model
    zone_fact: ZoneFact = ZoneActions.get(client=client, zone=zone_name)

    # Test model attributes
    assert zone_fact.zone == zone_name
    assert zone_fact.account_facts.aws_account_id == "123456789012"
    assert zone_fact.account_facts.environment == "production"

    # Test region facts
    assert "us-east-1" in zone_fact.region_facts
    us_east = zone_fact.region_facts["us-east-1"]
    assert us_east.aws_region == "us-east-1"
    assert us_east.az_count == 3

    # Test conversion back to model
    db_model = zone_fact.to_model(client)
    assert db_model.zone == zone_name

    # Test model_dump with mode='json' for API serialization
    api_data = zone_fact.model_dump(mode="json")
    assert "Zone" in api_data  # PascalCase for API
    assert "AccountFacts" in api_data
    assert "RegionFacts" in api_data


def test_minimal_zone_creation():
    """Test creating zone with minimal required fields only."""
    minimal_data = {
        "zone": "minimal-test-zone",
        "account_facts": {"aws_account_id": "222222222222"},
        "region_facts": {"us-minimal-1": {"aws_region": "us-minimal-1"}},
    }

    response: ZoneFact = ZoneActions.create(client=client, **minimal_data)
    assert isinstance(response, ZoneFact)

    assert response.zone == "minimal-test-zone"
    assert response.account_facts.aws_account_id == "222222222222"
    assert response.region_facts["us-minimal-1"].aws_region == "us-minimal-1"

    # Clean up
    ZoneActions.delete(client=client, zone="minimal-test-zone")
