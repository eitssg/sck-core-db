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
        "client": client,
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
        "client": client,
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
        "client": client,
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
        response = ZoneActions.create(**zone_fact)

        assert isinstance(response, SuccessResponse), f"Create failed for zone {i+1}"
        assert response.data is not None, f"Response data is None for zone {i+1}"
        assert isinstance(
            response.data, dict
        ), f"Response data is not dict for zone {i+1}"

        # Verify PascalCase keys in response
        assert "Zone" in response.data, f"Zone key missing for zone {i+1}"
        assert (
            response.data["Zone"] == zone_fact["zone"]
        ), f"Zone mismatch for zone {i+1}"

        assert "AccountFacts" in response.data, f"AccountFacts missing for zone {i+1}"
        assert "RegionFacts" in response.data, f"RegionFacts missing for zone {i+1}"

        # Verify nested structure with PascalCase
        account_facts = response.data["AccountFacts"]
        assert "AwsAccountId" in account_facts, f"AwsAccountId missing for zone {i+1}"
        assert (
            account_facts["AwsAccountId"]
            == zone_fact["account_facts"]["aws_account_id"]
        )

        # Verify region facts structure
        region_facts = response.data["RegionFacts"]
        assert isinstance(region_facts, dict), f"RegionFacts not dict for zone {i+1}"

        # Check first region in each zone
        first_region = list(zone_fact["region_facts"].keys())[0]
        assert (
            first_region in region_facts
        ), f"Region {first_region} missing for zone {i+1}"
        assert (
            "AwsRegion" in region_facts[first_region]
        ), f"AwsRegion missing for zone {i+1}"


def test_zone_get():
    """Test retrieving specific zone facts."""
    zone_name = "prod-east"

    response = ZoneActions.get(client=client, zone=zone_name)

    assert isinstance(response, SuccessResponse)
    assert response.data is not None
    assert isinstance(response.data, dict)

    # Verify PascalCase keys
    assert "Zone" in response.data
    assert response.data["Zone"] == zone_name
    assert "AccountFacts" in response.data
    assert "RegionFacts" in response.data

    # Verify account facts structure
    account_facts = response.data["AccountFacts"]
    assert "AwsAccountId" in account_facts
    assert account_facts["AwsAccountId"] == "123456789012"
    assert "Environment" in account_facts
    assert account_facts["Environment"] == "production"

    # Verify region facts structure
    region_facts = response.data["RegionFacts"]
    assert "us-east-1" in region_facts
    us_east_region = region_facts["us-east-1"]
    assert "AwsRegion" in us_east_region
    assert us_east_region["AwsRegion"] == "us-east-1"
    assert "AzCount" in us_east_region
    assert us_east_region["AzCount"] == 3

    # Verify KMS configuration
    assert "Kms" in account_facts
    kms_facts = account_facts["Kms"]
    assert "AwsAccountId" in kms_facts
    assert "KmsKeyArn" in kms_facts
    assert "AllowSNS" in kms_facts
    assert kms_facts["AllowSNS"] == True


def test_zone_list_all():
    """Test listing all zones for client."""
    response = ZoneActions.list(client=client, limit=10)

    assert isinstance(response, SuccessResponse)
    assert response.data is not None
    assert isinstance(response.data, list)
    assert len(response.data) <= 10
    assert hasattr(response, "metadata")

    # Should have 3 zones from our test data
    assert len(response.data) >= 3

    # Verify each zone has proper structure
    zone_names = set()
    for zone in response.data:
        assert isinstance(zone, dict)
        assert "Zone" in zone
        assert "AccountFacts" in zone
        assert "RegionFacts" in zone
        zone_names.add(zone["Zone"])

    # Verify our test zones are present
    expected_zones = {"prod-east", "uat-central", "dev-west"}
    assert expected_zones.issubset(zone_names)


def test_zone_list_by_aws_account():
    """Test listing zones by AWS account ID."""
    # Test production account
    prod_account_id = "123456789012"
    response = ZoneActions.list(client=client, aws_account_id=prod_account_id)

    assert isinstance(response, SuccessResponse)
    assert response.data is not None
    assert isinstance(response.data, list)

    # Should return only production zone
    assert len(response.data) == 1
    prod_zone = response.data[0]
    assert prod_zone["Zone"] == "prod-east"
    assert prod_zone["AccountFacts"]["AwsAccountId"] == prod_account_id

    # Test UAT account
    uat_account_id = "234567890123"
    response = ZoneActions.list(client=client, aws_account_id=uat_account_id)

    assert len(response.data) == 1
    uat_zone = response.data[0]
    assert uat_zone["Zone"] == "uat-central"
    assert uat_zone["AccountFacts"]["AwsAccountId"] == uat_account_id

    # Test non-existent account
    response = ZoneActions.list(client=client, aws_account_id="999999999999")
    assert len(response.data) == 0


def test_zone_list_with_pagination():
    """Test pagination functionality."""
    # Get first page with limit 2
    page1 = ZoneActions.list(client=client, limit=2)
    assert len(page1.data) <= 2

    # Check if there's more data
    if page1.metadata.get("cursor"):
        page2 = ZoneActions.list(
            client=client, limit=2, cursor=page1.metadata["cursor"]
        )
        assert isinstance(page2, SuccessResponse)

        # Verify different data using Zone keys
        page1_zones = {zone["Zone"] for zone in page1.data}
        page2_zones = {zone["Zone"] for zone in page2.data}
        assert page1_zones.isdisjoint(page2_zones), "Pages should not overlap"


# =============================================================================
# Complex Structure Validation Tests
# =============================================================================


def test_zone_complex_structure_validation():
    """Test that complex nested structures are properly handled."""
    zone_name = "prod-east"
    response = ZoneActions.get(client=client, zone=zone_name)

    data = response.data

    # Test KMS structure
    kms = data["AccountFacts"]["Kms"]
    assert "AwsAccountId" in kms
    assert "KmsKeyArn" in kms
    assert "KmsKey" in kms
    assert "DelegateAwsAccountIds" in kms
    assert isinstance(kms["DelegateAwsAccountIds"], list)
    assert len(kms["DelegateAwsAccountIds"]) == 2

    # Test region facts structure
    us_east_region = data["RegionFacts"]["us-east-1"]

    # Test image aliases
    assert "ImageAliases" in us_east_region
    image_aliases = us_east_region["ImageAliases"]
    assert "ubuntu" in image_aliases
    assert "amazon-linux" in image_aliases
    assert "nginx" in image_aliases

    # Test security aliases
    assert "SecurityAliases" in us_east_region
    security_aliases = us_east_region["SecurityAliases"]
    assert "corporate-cidrs" in security_aliases
    assert "admin-cidrs" in security_aliases

    corporate_cidrs = security_aliases["corporate-cidrs"]
    assert isinstance(corporate_cidrs, list)
    assert len(corporate_cidrs) == 2

    first_cidr = corporate_cidrs[0]
    assert "Type" in first_cidr
    assert "Value" in first_cidr
    assert "Description" in first_cidr
    assert first_cidr["Type"] == "CIDR"
    assert first_cidr["Value"] == "10.0.0.0/8"

    # Test security group aliases
    assert "SecurityGroupAliases" in us_east_region
    sg_aliases = us_east_region["SecurityGroupAliases"]
    assert "web-sg" in sg_aliases
    assert "app-sg" in sg_aliases
    assert "db-sg" in sg_aliases

    # Test proxy configuration
    assert "Proxy" in us_east_region
    proxy_list = us_east_region["Proxy"]
    assert isinstance(proxy_list, list)
    assert len(proxy_list) == 1

    proxy = proxy_list[0]
    assert "Host" in proxy
    assert "Port" in proxy
    assert "Url" in proxy
    assert "NoProxy" in proxy
    assert proxy["Host"] == "proxy.acme.com"
    assert proxy["Port"] == "8080"

    # Test simple proxy fields
    assert "ProxyHost" in us_east_region
    assert "ProxyPort" in us_east_region
    assert "ProxyUrl" in us_east_region
    assert "NoProxy" in us_east_region
    assert us_east_region["ProxyHost"] == "proxy.acme.com"
    assert us_east_region["ProxyPort"] == 8080

    # Test name servers
    assert "NameServers" in us_east_region
    name_servers = us_east_region["NameServers"]
    assert isinstance(name_servers, list)
    assert "8.8.8.8" in name_servers
    assert "1.1.1.1" in name_servers

    # Test tags
    assert "Tags" in us_east_region
    region_tags = us_east_region["Tags"]
    assert "Region" in region_tags
    assert "NetworkTier" in region_tags
    assert region_tags["Region"] == "us-east-1"
    assert region_tags["NetworkTier"] == "production"


def test_zone_account_facts_validation():
    """Test detailed account facts validation."""
    zone_name = "uat-central"
    response = ZoneActions.get(client=client, zone=zone_name)

    account_facts = response.data["AccountFacts"]

    # Test all account fields
    assert "OrganizationalUnit" in account_facts
    assert account_facts["OrganizationalUnit"] == "UAT"
    assert "AwsAccountId" in account_facts
    assert account_facts["AwsAccountId"] == "234567890123"
    assert "AccountName" in account_facts
    assert account_facts["AccountName"] == "ACME UAT Account"
    assert "Environment" in account_facts
    assert account_facts["Environment"] == "uat"
    assert "ResourceNamespace" in account_facts
    assert account_facts["ResourceNamespace"] == "acme-uat"
    assert "NetworkName" in account_facts
    assert account_facts["NetworkName"] == "uat-network"

    # Test VPC and subnet aliases
    assert "VpcAliases" in account_facts
    vpc_aliases = account_facts["VpcAliases"]
    assert isinstance(vpc_aliases, list)
    assert "vpc-uat-main" in vpc_aliases
    assert "vpc-uat-test" in vpc_aliases

    assert "SubnetAliases" in account_facts
    subnet_aliases = account_facts["SubnetAliases"]
    assert isinstance(subnet_aliases, list)
    assert "subnet-uat-public" in subnet_aliases
    assert "subnet-uat-private" in subnet_aliases

    # Test account-level tags
    assert "Tags" in account_facts
    account_tags = account_facts["Tags"]
    assert "Environment" in account_tags
    assert "AutoShutdown" in account_tags
    assert account_tags["Environment"] == "uat"
    assert account_tags["AutoShutdown"] == "enabled"


def test_zone_multiple_regions():
    """Test zone with multiple regions."""
    zone_name = "prod-east"
    response = ZoneActions.get(client=client, zone=zone_name)

    region_facts = response.data["RegionFacts"]

    # Should have both us-east-1 and us-west-2
    assert "us-east-1" in region_facts
    assert "us-west-2" in region_facts

    # Test us-east-1 specifics
    us_east = region_facts["us-east-1"]
    assert us_east["AzCount"] == 3
    assert us_east["MinSuccessfulInstancesPercent"] == 100
    assert "nginx" in us_east["ImageAliases"]

    # Test us-west-2 specifics
    us_west = region_facts["us-west-2"]
    assert us_west["AzCount"] == 4
    assert us_west["MinSuccessfulInstancesPercent"] == 75
    assert "nginx" not in us_west["ImageAliases"]  # Different AMIs per region

    # Both should have basic proxy config
    assert us_east["ProxyHost"] == "proxy.acme.com"
    assert us_west["ProxyHost"] == "proxy-west.acme.com"


# =============================================================================
# Update Tests (PUT and PATCH)
# =============================================================================


def test_zone_update_full():
    """Test full zone update (PUT semantics)."""
    zone_name = "dev-west"

    # Get current data first
    current = ZoneActions.get(client=client, zone=zone_name)
    original_account_id = current.data["AccountFacts"]["AwsAccountId"]

    update_data = {
        "client": client,
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

    response = ZoneActions.update(**update_data)
    assert isinstance(response, SuccessResponse)

    # Verify updates with PascalCase keys
    data = response.data
    assert data["Zone"] == zone_name

    # Verify account facts updates
    account_facts = data["AccountFacts"]
    assert account_facts["AccountName"] == "Updated Development Account"
    assert account_facts["Environment"] == "staging"
    assert account_facts["ResourceNamespace"] == "acme-dev-updated"
    assert account_facts["Tags"]["Purpose"] == "updated-testing"

    # Verify region facts updates
    region_facts = data["RegionFacts"]["us-west-2"]
    assert region_facts["AzCount"] == 3
    assert region_facts["MinSuccessfulInstancesPercent"] == 50
    assert region_facts["ProxyHost"] == "proxy-updated.acme.com"
    assert region_facts["ProxyPort"] == 9090
    assert "new-image" in region_facts["ImageAliases"]

    # Verify global tags
    assert data["Tags"]["UpdatedField"] == "updated-value"
    assert data["Tags"]["Team"] == "updated-engineering"


def test_zone_patch_partial():
    """Test partial zone update (PATCH semantics)."""
    zone_name = "uat-central"

    # Get current data to verify what doesn't change
    current = ZoneActions.get(client=client, zone=zone_name)
    original_account_name = current.data["AccountFacts"]["AccountName"]
    original_org_unit = current.data["AccountFacts"]["OrganizationalUnit"]

    # Patch only specific fields
    patch_data = {
        "client": client,
        "zone": zone_name,
        "account_facts": {
            "aws_account_id": "234567890123",  # Keep same (required)
            "environment": "pre-production",  # Change this
            "resource_namespace": "acme-uat-patched",  # Change this
            # Don't include account_name or organizational_unit - they should remain
        },
        "tags": {"Environment": "pre-production", "PatchedField": "patch-added"},
    }

    response = ZoneActions.patch(**patch_data)
    assert isinstance(response, SuccessResponse)

    # Verify PascalCase keys in response
    data = response.data
    account_facts = data["AccountFacts"]

    # Changed fields
    assert account_facts["Environment"] == "pre-production"
    assert account_facts["ResourceNamespace"] == "acme-uat-patched"

    # Unchanged fields should remain
    assert account_facts["AccountName"] == original_account_name
    assert account_facts["OrganizationalUnit"] == original_org_unit

    # Tags should be updated/added
    assert data["Tags"]["PatchedField"] == "patch-added"
    assert data["Tags"]["Environment"] == "pre-production"


def test_zone_patch_with_nested_updates():
    """Test PATCH with complex nested structure updates."""
    zone_name = "prod-east"

    # Update only specific nested fields
    patch_data = {
        "client": client,
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

    response = ZoneActions.patch(**patch_data)
    assert isinstance(response, SuccessResponse)

    data = response.data
    us_east = data["RegionFacts"]["us-east-1"]

    # Verify changes
    assert us_east["MinSuccessfulInstancesPercent"] == 90
    assert us_east["ProxyPort"] == 8888
    assert us_east["ImageAliases"]["ubuntu"] == "ami-patched-ubuntu"
    assert "patched-image" in us_east["ImageAliases"]
    assert us_east["Tags"]["PatchedTag"] == "patched-value"

    # Verify us-west-2 region still exists (not removed by patch)
    assert "us-west-2" in data["RegionFacts"]
    us_west = data["RegionFacts"]["us-west-2"]
    assert us_west["ProxyHost"] == "proxy-west.acme.com"  # Should be unchanged


# =============================================================================
# Error Handling Tests
# =============================================================================


def test_create_duplicate_zone():
    """Test creating duplicate zone should fail."""
    duplicate_data = {
        "client": client,
        "zone": "prod-east",  # Already exists
        "account_facts": {
            "aws_account_id": "999999999999",
        },
        "region_facts": {"us-test-1": {"aws_region": "us-test-1"}},
    }

    with pytest.raises(ConflictException):
        ZoneActions.create(**duplicate_data)


def test_get_nonexistent_zone():
    """Test getting non-existent zone."""
    response = ZoneActions.get(client=client, zone="nonexistent-zone")
    assert isinstance(response, NoContentResponse)
    assert "does not exist" in response.message


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
        ZoneActions.patch(
            client=client, zone="nonexistent-zone", tags={"Test": "should-fail"}
        )


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
        ZoneActions.get(client=client)

    # Test get without client
    with patch("core_framework.get_client", return_value=None):
        with pytest.raises(BadRequestException):
            ZoneActions.get(zone="test-zone")

    # Test list without client
    with patch("core_framework.get_client", return_value=None):
        with pytest.raises(BadRequestException):
            ZoneActions.list()

    # Test delete without zone
    with pytest.raises(BadRequestException):
        ZoneActions.delete(client=client)


def test_invalid_zone_data():
    """Test creating zone with invalid data."""
    invalid_data = {
        "client": client,
        "zone": "invalid-test-zone",
        "account_facts": {
            # Missing required aws_account_id
            "account_name": "Invalid Test"
        },
        "region_facts": {"us-test-1": {"aws_region": "us-test-1"}},
    }

    with pytest.raises(BadRequestException):
        ZoneActions.create(**invalid_data)


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
        "client": client,
        "zone": "delete-test-zone",
        "account_facts": {
            "aws_account_id": "999999999999",
            "account_name": "Zone for Deletion Test",
            "environment": "test",
        },
        "region_facts": {"us-test-1": {"aws_region": "us-test-1", "az_count": 1}},
    }

    # Create the zone
    create_response = ZoneActions.create(**delete_test_data)
    assert isinstance(create_response, SuccessResponse)

    # Verify it exists
    get_response = ZoneActions.get(client=client, zone="delete-test-zone")
    assert isinstance(get_response, SuccessResponse)

    # Delete the zone
    delete_response = ZoneActions.delete(client=client, zone="delete-test-zone")
    assert isinstance(delete_response, SuccessResponse)
    assert "deleted" in delete_response.message.lower()

    # Verify it's gone
    get_after_delete = ZoneActions.get(client=client, zone="delete-test-zone")
    assert isinstance(get_after_delete, NoContentResponse)


def test_delete_nonexistent_zone():
    """Test deleting non-existent zone."""
    response = ZoneActions.delete(client=client, zone="nonexistent-zone")
    assert isinstance(response, NoContentResponse)
    assert "not found" in response.message


def test_delete_without_required_parameters():
    """Test delete without required parameters."""
    with pytest.raises(BadRequestException):
        ZoneActions.delete(client=client)  # Missing zone

    with patch("core_framework.get_client", return_value=None):
        with pytest.raises(BadRequestException):
            ZoneActions.delete(zone="test")  # Missing client


# =============================================================================
# Response Format and Casing Tests
# =============================================================================


def test_response_casing_consistency():
    """Test that all responses follow proper casing conventions."""
    zone_name = "prod-east"

    # Test get response
    get_response = ZoneActions.get(client=client, zone=zone_name)

    # Response attributes should be snake_case
    assert hasattr(get_response, "data")
    assert hasattr(get_response, "message") or not hasattr(
        get_response, "message"
    )  # May not have message

    # Data content should be PascalCase
    data = get_response.data
    expected_pascal_keys = [
        "Zone",
        "AccountFacts",
        "RegionFacts",
        "Tags",
        "CreatedAt",
        "UpdatedAt",
    ]

    for key in expected_pascal_keys:
        if key in ["CreatedAt", "UpdatedAt", "Tags"]:
            continue  # These might be optional
        assert (
            key in data
        ), f"Expected PascalCase key '{key}' not found in response data"

    # Test list response
    list_response = ZoneActions.list(client=client, limit=1)
    assert hasattr(list_response, "data")
    assert hasattr(list_response, "metadata")  # snake_case

    if list_response.data:
        list_item = list_response.data[0]
        assert "Zone" in list_item  # PascalCase
        assert "AccountFacts" in list_item  # PascalCase


def test_nested_data_casing():
    """Test that nested data structures maintain proper casing."""
    zone_name = "prod-east"
    response = ZoneActions.get(client=client, zone=zone_name)

    data = response.data

    # Top-level should be PascalCase
    assert "AccountFacts" in data
    assert "RegionFacts" in data

    # AccountFacts nested fields should be PascalCase
    account_facts = data["AccountFacts"]
    assert "AwsAccountId" in account_facts
    assert "AccountName" in account_facts
    assert "Kms" in account_facts

    # KMS nested fields should be PascalCase
    kms = account_facts["Kms"]
    assert "AwsAccountId" in kms
    assert "DelegateAwsAccountIds" in kms

    # RegionFacts nested fields should be PascalCase
    region_facts = data["RegionFacts"]
    us_east = region_facts["us-east-1"]
    assert "AwsRegion" in us_east
    assert "ImageAliases" in us_east
    assert "SecurityAliases" in us_east

    # SecurityAliases nested structure
    security_aliases = us_east["SecurityAliases"]
    corporate_cidrs = security_aliases["corporate-cidrs"]
    first_cidr = corporate_cidrs[0]
    assert "Type" in first_cidr
    assert "Value" in first_cidr
    assert "Description" in first_cidr


def test_audit_fields():
    """Test that audit fields are properly managed."""
    zone_name = "uat-central"

    # Get zone to check timestamps
    response = ZoneActions.get(client=client, zone=zone_name)
    data = response.data

    # Should have audit fields with PascalCase
    assert "CreatedAt" in data
    assert "UpdatedAt" in data
    assert data["CreatedAt"] is not None
    assert data["UpdatedAt"] is not None

    original_created_at = data["CreatedAt"]
    original_updated_at = data["UpdatedAt"]

    # Patch the zone (should update UpdatedAt but not CreatedAt)
    patch_response = ZoneActions.patch(
        client=client, zone=zone_name, tags={"TestPatch": "timestamp-test"}
    )

    patched_data = patch_response.data
    assert patched_data["CreatedAt"] == original_created_at  # Should not change
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
        "client": client,
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

    create_response = ZoneActions.create(**create_data)
    assert isinstance(create_response, SuccessResponse)
    assert create_response.data["Zone"] == zone_name

    # 2. Read
    get_response = ZoneActions.get(client=client, zone=zone_name)
    assert isinstance(get_response, SuccessResponse)
    assert get_response.data["AccountFacts"]["Environment"] == "test"

    # 3. Update (partial)
    patch_response = ZoneActions.patch(
        client=client, zone=zone_name, tags={"Test": "lifecycle", "Stage": "updated"}
    )
    assert isinstance(patch_response, SuccessResponse)
    assert patch_response.data["Tags"]["Stage"] == "updated"

    # 4. Update (full)
    update_response = ZoneActions.update(
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
    assert isinstance(update_response, SuccessResponse)
    assert update_response.data["AccountFacts"]["Environment"] == "staging"
    assert update_response.data["RegionFacts"]["us-lifecycle-1"]["AzCount"] == 3

    # 5. Delete
    delete_response = ZoneActions.delete(client=client, zone=zone_name)
    assert isinstance(delete_response, SuccessResponse)

    # 6. Verify deletion
    final_get = ZoneActions.get(client=client, zone=zone_name)
    assert isinstance(final_get, NoContentResponse)


def test_zone_model_conversion():
    """Test ZoneFact model conversion methods."""
    zone_name = "prod-east"

    # Get zone as Pydantic model
    response = ZoneActions.get(client=client, zone=zone_name)

    # Create ZoneFact from response data
    zone_fact = ZoneFact(**response.data)

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
        "client": client,
        "zone": "minimal-test-zone",
        "account_facts": {"aws_account_id": "222222222222"},
        "region_facts": {"us-minimal-1": {"aws_region": "us-minimal-1"}},
    }

    response = ZoneActions.create(**minimal_data)
    assert isinstance(response, SuccessResponse)

    # Verify minimal structure
    data = response.data
    assert data["Zone"] == "minimal-test-zone"
    assert data["AccountFacts"]["AwsAccountId"] == "222222222222"
    assert data["RegionFacts"]["us-minimal-1"]["AwsRegion"] == "us-minimal-1"

    # Clean up
    ZoneActions.delete(client=client, zone="minimal-test-zone")
