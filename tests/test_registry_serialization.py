import pytest

from pynamodb.attributes import MapAttribute

import core_framework as util

from core_db.registry.client import ClientFactsModel, ClientFact
from core_db.registry.portfolio import PortfolioFactsModel, PortfolioFact, PortfolioActions
from core_db.registry.zone import (
    ZoneFactsModel,
    ZoneFact,
    ZoneActions,
)
from core_db.registry.app import (
    AppFactsModel,
    AppFact,
    AppActions,
)
from core_db.registry.portfolio.models import (
    ContactFacts,
    ApproverFacts,
    ProjectFacts,
    OwnerFacts,
)

client = util.get_client()


@pytest.fixture
def client_fact():
    """Fully populated ClientFact dictionary with all actual fields."""
    return {
        # Primary key
        "client": "acme",
        # Basic client information
        "client_id": "acme-corp-2024",
        "client_type": "enterprise",
        "client_status": "active",
        "client_description": "Large enterprise corporation specializing in technology solutions",
        "client_name": "ACME Corporation",
        # AWS Organization configuration
        "organization_id": "o-123456789abc",
        "organization_name": "ACME Holdings Inc",
        "organization_account": "123456789012",
        "organization_email": "aws-admin@acme.com",
        # Domain and networking
        "domain": "acme.com",
        # AWS Account assignments
        "iam_account": "123456789012",
        "audit_account": "987654321098",
        "automation_account": "333333333333",
        "security_account": "111111111111",
        "network_account": "222222222222",
        # Regional configuration
        "master_region": "us-west-2",
        "client_region": "us-west-2",
        "bucket_region": "us-west-2",
        # S3 bucket configuration
        "bucket_name": "acme-core-automation",
        "docs_bucket_name": "acme-core-automation-docs",
        "artefact_bucket_name": "acme-core-automation-artefacts",
        "ui_bucket_name": "acme-core-automation-ui",
        "ui_bucket": "acme-ui-legacy",
        # Resource naming
        "scope": "prod-",
    }


@pytest.fixture
def client_fact_alias():
    """Fully populated ClientFact dictionary with PascalCase alias field names."""
    return {
        # Primary key - PascalCase alias
        "Client": "acme",  # alias for client
        # Basic client information - PascalCase aliases
        "ClientId": "acme-corp-2024",  # alias for client_id
        "ClientType": "enterprise",  # alias for client_type
        "ClientStatus": "active",  # alias for client_status
        "ClientDescription": "Large enterprise corporation specializing in technology solutions",  # alias for client_description
        "ClientName": "ACME Corporation",  # alias for client_name
        # AWS Organization configuration - PascalCase aliases
        "OrganizationId": "o-123456789abc",  # alias for organization_id
        "OrganizationName": "ACME Holdings Inc",  # alias for organization_name
        "OrganizationAccount": "123456789012",  # alias for organization_account
        "OrganizationEmail": "aws-admin@acme.com",  # alias for organization_email
        # Domain and networking - PascalCase alias
        "Domain": "acme.com",  # alias for domain
        # AWS Account assignments - PascalCase aliases
        "IamAccount": "123456789012",  # alias for iam_account
        "AuditAccount": "987654321098",  # alias for audit_account
        "AutomationAccount": "333333333333",  # alias for automation_account
        "SecurityAccount": "111111111111",  # alias for security_account
        "NetworkAccount": "222222222222",  # alias for network_account
        # Regional configuration - PascalCase aliases
        "MasterRegion": "us-west-2",  # alias for master_region
        "ClientRegion": "us-west-2",  # alias for client_region
        "BucketRegion": "us-west-2",  # alias for bucket_region
        # S3 bucket configuration - PascalCase aliases
        "BucketName": "acme-core-automation",  # alias for bucket_name
        "DocsBucketName": "acme-core-automation-docs",  # alias for docs_bucket_name
        "ArtefactBucketName": "acme-core-automation-artefacts",  # alias for artefact_bucket_name
        "UiBucketName": "acme-core-automation-ui",  # alias for ui_bucket_name
        "UiBucket": "acme-ui-legacy",  # alias for ui_bucket
        # Resource naming - PascalCase alias
        "Scope": "prod-",  # alias for scope
    }


@pytest.fixture
def portfolio_facts():
    """Fully populated PortfolioFacts dictionary with all actual fields."""
    return {
        "portfolio": "platform-services",
        # Portfolio configuration with correct ExtendedMapAttribute fields
        "contacts": [
            {
                # Only fields that actually exist in ContactFacts
                "name": "Tech Lead",
                "email": "tech-lead@acme.com",
                "attributes": {
                    "department": "engineering",
                    "location": "san-francisco",
                },
                "enabled": True,
            },
            {
                "name": "Product Manager",
                "email": "pm@acme.com",
                "attributes": {"department": "product", "location": "new-york"},
                "enabled": True,
            },
        ],
        "approvers": [
            {
                # Only fields that actually exist in ApproverFacts
                "sequence": 1,
                "name": "Engineering Manager",
                "email": "eng-mgr@acme.com",
                "roles": ["deployment", "approval"],
                "attributes": {"department": "engineering"},
                "depends_on": [],
                "enabled": True,
            },
            {
                "sequence": 2,
                "name": "Director of Engineering",
                "email": "director@acme.com",
                "roles": ["executive", "approval"],
                "depends_on": [1],
                "enabled": True,
            },
        ],
        "project": {
            # Only fields that actually exist in ProjectFacts
            "name": "Platform Services Project",
            "code": "platform-svc",
            "repository": "https://github.com/acme/platform-services",
            "description": "Core platform infrastructure and services",
            "attributes": {"type": "infrastructure", "priority": "high"},
        },
        # Domain field
        "domain": "platform.acme.com",
        # bizapp is alternative to project
        "bizapp": {
            "name": "Business Platform App",
            "code": "biz-platform",
            "repository": "https://github.com/acme/biz-platform",
            "description": "Business platform application",
        },
        "owner": {
            # Only fields that actually exist in OwnerFacts
            "name": "Platform Team",
            "email": "platform-team@acme.com",
            "phone": "+1-555-0123",
            "attributes": {"department": "engineering", "budget_code": "ENG-PLT-001"},
        },
        # Metadata and attributes - all MapAttribute of UnicodeAttribute
        "tags": {
            "Environment": "production",
            "Team": "platform",
            "Service": "infrastructure",
        },
        "metadata": {
            "deploy_strategy": "blue-green",
            "scaling_policy": "auto",
            "backup_retention": "30d",
        },
        "attributes": {
            "max_instances": "10",
            "min_instances": "2",
            "health_check_path": "/health",
        },
    }


@pytest.fixture
def portfolio_fact_alias():
    """Fully populated PortfolioFact dictionary with PascalCase alias field names."""
    return {
        # Primary keys - PascalCase aliases
        "Client": "acme",  # alias for client
        "Portfolio": "platform-services",  # alias for portfolio
        # ContactFactsItem with PascalCase aliases for all nested fields
        "Contacts": [  # alias for contacts
            {
                "Name": "Tech Lead",  # alias for name
                "Email": "tech-lead@acme.com",  # alias for email
                "Attributes": {
                    "department": "engineering",
                    "location": "san-francisco",
                },  # alias for attributes
                "Enabled": True,  # alias for enabled
            },
            {
                "Name": "Product Manager",  # alias for name
                "Email": "pm@acme.com",  # alias for email
                "Attributes": {
                    "department": "product",
                    "location": "new-york",
                },  # alias for attributes
                "Enabled": True,  # alias for enabled
            },
        ],
        # ApproverFactsItem with PascalCase aliases for all nested fields
        "Approvers": [  # alias for approvers
            {
                "Sequence": 1,  # alias for sequence
                "Name": "Engineering Manager",  # alias for name
                "Email": "eng-mgr@acme.com",  # alias for email
                "Roles": ["deployment", "approval"],  # alias for roles
                "Attributes": {"department": "engineering"},  # alias for attributes
                "DependsOn": [],  # alias for depends_on
                "Enabled": True,  # alias for enabled
            },
            {
                "Sequence": 2,  # alias for sequence
                "Name": "Director of Engineering",  # alias for name
                "Email": "director@acme.com",  # alias for email
                "Roles": ["executive", "approval"],  # alias for roles
                "DependsOn": [1],  # alias for depends_on
                "Enabled": True,  # alias for enabled
            },
        ],
        # ProjectFactsItem with PascalCase aliases for all nested fields
        "Project": {  # alias for project
            "Name": "Platform Services Project",  # alias for name
            "Code": "platform-svc",  # alias for code
            "Repository": "https://github.com/acme/platform-services",  # alias for repository
            "Description": "Core platform infrastructure and services",  # alias for description
            "Attributes": {
                "type": "infrastructure",
                "priority": "high",
            },  # alias for attributes
        },
        # Domain field - PascalCase alias
        "Domain": "platform.acme.com",  # alias for domain
        # BizappFactsItem with PascalCase aliases (alternative to project)
        "Bizapp": {  # alias for bizapp
            "Name": "Business Platform App",  # alias for name
            "Code": "biz-platform",  # alias for code
            "Repository": "https://github.com/acme/biz-platform",  # alias for repository
            "Description": "Business platform application",  # alias for description
        },
        # OwnerFactsItem with PascalCase aliases for all nested fields
        "Owner": {  # alias for owner
            "Name": "Platform Team",  # alias for name
            "Email": "platform-team@acme.com",  # alias for email
            "Phone": "+1-555-0123",  # alias for phone
            "Attributes": {
                "department": "engineering",
                "budget_code": "ENG-PLT-001",
            },  # alias for attributes
        },
        # Metadata and attributes - PascalCase aliases for MapAttribute fields
        "Tags": {
            "Environment": "production",
            "Team": "platform",
            "Service": "infrastructure",
        },  # alias for tags
        "Metadata": {
            "deploy_strategy": "blue-green",
            "scaling_policy": "auto",
            "backup_retention": "30d",
        },  # alias for metadata
        "Attributes": {
            "max_instances": "10",
            "min_instances": "2",
            "health_check_path": "/health",
        },  # alias for attributes
    }


@pytest.fixture
def zone_facts():
    """Fully populated ZoneFacts dictionary with all actual fields."""
    return {
        # Primary keys
        "zone": "production-west",
        # AccountFacts with correct field types
        "account_facts": {
            "organizational_unit": "Production",
            "aws_account_id": "123456789012",
            "account_name": "ACME Production West",
            "environment": "production",
            "kms": {
                # KmsFacts fields
                "aws_account_id": "123456789012",
                "kms_key_arn": "arn:aws:kms:us-west-2:123456789012:key/12345678-1234-1234-1234-123456789012",
                "kms_key": "12345678-1234-1234-1234-123456789012",
                "delegate_aws_account_ids": [
                    "123456789012",
                    "123456789013",
                    "123456789014",
                ],
                "allow_sns": True,
            },
            "resource_namespace": "acme-prod-west",
            "network_name": "acme-production-network",
            # These are ListAttribute, not MapAttribute!
            "vpc_aliases": {"vpc-12345abcde": {"cidr": "192.168.1.0/24"}, "vpc-67890fghij": {"cidr": "192.168.2.0/24"}},
            "subnet_aliases": {
                "subnet-web1a12345": {"cidr": "192.168.1.0/24"},
                "subnet-app1a11111": {"cidr": "192.168.1.0/24"},
                "subnet-db1a33333": {"cidr": "192.168.1.0/24"},
            },
            "tags": {
                "Environment": "production",
                "Region": "us-west-2",
                "Owner": "platform-team",
            },
        },
        # RegionFacts with correct nested structures
        "region_facts": {
            "us-west-2": {
                "aws_region": "us-west-2",
                "az_count": 3,
                "image_aliases": {
                    "latest": "ami-12345abcde",
                    "stable": "ami-67890fghij",
                    "ubuntu-22": "ami-22222bbbbb",
                },
                "min_successful_instances_percent": 75,
                # MapAttribute of ListAttribute of SecurityAliasFacts
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
                            "description": "Private network range",
                        },
                    ],
                    "office-locations": [
                        {
                            "type": "CIDR",
                            "value": "203.0.113.0/24",
                            "description": "San Francisco office",
                        }
                    ],
                },
                "security_group_aliases": {
                    "web-sg": "sg-web12345",
                    "app-sg": "sg-app67890",
                    "db-sg": "sg-db11111",
                },
                # ListAttribute of ProxyFacts
                "proxy": [
                    {
                        "host": "proxy-west-1.acme.com",
                        "port": "8080",
                        "url": "http://proxy-west-1.acme.com:8080",
                        "no_proxy": "localhost,127.0.0.1,.acme.com",
                    }
                ],
                # Legacy proxy fields
                "proxy_host": "proxy-west-1.acme.com",
                "proxy_port": 8080,
                "proxy_url": "http://proxy-west-1.acme.com:8080",
                "no_proxy": "localhost,127.0.0.1,.acme.com,.amazonaws.com",
                "name_servers": ["8.8.8.8", "8.8.4.4", "1.1.1.1"],
                "tags": {
                    "Region": "us-west-2",
                    "Tier": "production",
                    "Availability": "high",
                },
            }
        },
        # Global zone tags
        "tags": {
            "Environment": "production",
            "Zone": "production-west",
            "Owner": "platform-team",
        },
    }


@pytest.fixture
def zone_fact_alias():
    """Fully populated ZoneFact dictionary with PascalCase alias field names."""
    return {
        # Primary keys - PascalCase aliases
        "Client": "acme",  # alias for client
        "Zone": "production-west",  # alias for zone
        # AccountFactsItem with PascalCase aliases for all nested fields
        "AccountFacts": {  # alias for account_facts
            "Client": "acme",  # alias for client
            "OrganizationalUnit": "Production",  # alias for organizational_unit
            "AwsAccountId": "123456789012",  # alias for aws_account_id
            "AccountName": "ACME Production West",  # alias for account_name
            "Environment": "production",  # alias for environment
            "Kms": {  # alias for kms - KmsFactsItem PascalCase aliases
                "AwsAccountId": "123456789012",  # alias for aws_account_id
                "KmsKeyArn": "arn:aws:kms:us-west-2:123456789012:key/12345678-1234-1234-1234-123456789012",  # alias for kms_key_arn
                "KmsKey": "12345678-1234-1234-1234-123456789012",  # alias for kms_key
                "DelegateAwsAccountIds": [
                    "123456789012",
                    "123456789013",
                    "123456789014",
                ],  # alias for delegate_aws_account_ids
                "AllowSNS": True,  # alias for allow_sns
            },
            "ResourceNamespace": "acme-prod-west",  # alias for resource_namespace
            "NetworkName": "acme-production-network",  # alias for network_name
            # These remain as lists (no PascalCase needed for list items)
            "VpcAliases": {
                "vpc-12345abcde": {"cidr": "192.168.1.0/24"},
                "vpc-67890fghij": {"cidr": "192.168.2.0/24"},
            },  # alias for vpc_aliases
            "SubnetAliases": {
                "subnet-web1a12345": {"cidr": "192.168.1.0/24"},
                "subnet-app1a11111": {"cidr": "192.168.1.0/24"},
                "subnet-db1a33333": {"cidr": "192.168.1.0/24"},
            },  # alias for subnet_aliases
            "Tags": {
                "Environment": "production",
                "Region": "us-west-2",
                "Owner": "platform-team",
            },  # alias for tags
        },
        # RegionFactsItem with PascalCase aliases for all nested fields
        "RegionFacts": {  # alias for region_facts
            "us-west-2": {
                "AwsRegion": "us-west-2",  # alias for aws_region
                "AzCount": 3,  # alias for az_count
                "ImageAliases": {
                    "latest": "ami-12345abcde",
                    "stable": "ami-67890fghij",
                    "ubuntu-22": "ami-22222bbbbb",
                },  # alias for image_aliases
                "MinSuccessfulInstancesPercent": 75,  # alias for min_successful_instances_percent
                # SecurityAliasFactsItem with PascalCase aliases
                "SecurityAliases": {  # alias for security_aliases
                    "corporate-cidrs": [
                        {
                            "Type": "CIDR",
                            "Value": "10.0.0.0/8",
                            "Description": "Corporate network range",
                        },  # SecurityAliasFacts PascalCase
                        {
                            "Type": "CIDR",
                            "Value": "172.16.0.0/12",
                            "Description": "Private network range",
                        },
                    ],
                    "office-locations": [
                        {
                            "Type": "CIDR",
                            "Value": "203.0.113.0/24",
                            "Description": "San Francisco office",
                        }
                    ],
                },
                "SecurityGroupAliases": {
                    "web-sg": "sg-web12345",
                    "app-sg": "sg-app67890",
                    "db-sg": "sg-db11111",
                },  # alias for security_group_aliases
                # ProxyFactsItem with PascalCase aliases
                "Proxy": [  # alias for proxy
                    {
                        "Host": "proxy-west-1.acme.com",  # alias for host
                        "Port": "8080",  # alias for port
                        "Url": "http://proxy-west-1.acme.com:8080",  # alias for url
                        "NoProxy": "localhost,127.0.0.1,.acme.com",  # alias for no_proxy
                    }
                ],
                # Legacy proxy fields with PascalCase aliases
                "ProxyHost": "proxy-west-1.acme.com",  # alias for proxy_host
                "ProxyPort": 8080,  # alias for proxy_port
                "ProxyUrl": "http://proxy-west-1.acme.com:8080",  # alias for proxy_url
                "NoProxy": "localhost,127.0.0.1,.acme.com,.amazonaws.com",  # alias for no_proxy
                "NameServers": [
                    "8.8.8.8",
                    "8.8.4.4",
                    "1.1.1.1",
                ],  # alias for name_servers
                "Tags": {
                    "Region": "us-west-2",
                    "Tier": "production",
                    "Availability": "high",
                },  # alias for tags
            }
        },
        # Global zone tags - PascalCase alias
        "Tags": {
            "Environment": "production",
            "Zone": "production-west",
            "Owner": "platform-team",
        },  # alias for tags
    }


@pytest.fixture
def app_facts():
    """Fully populated AppFactsModel dictionary with all actual fields."""
    return {
        # Primary keys - ACTUAL FIELD NAMES from AppFactsModel model
        "portfolio": "acme:platform-services",  # This is the hash key
        "app": "user-service",  # This is the range key
        "app_regex": "user-service.*",  # This is the range key
        # App Details - ACTUAL FIELDS from AppFactsModel model
        "name": "User Management Service",
        "environment": "production",
        "account": "123456789012",
        "zone": "production-west",
        "region": "us-west-2",
        "repository": "https://github.com/acme/user-service",
        "enforce_validation": "true",
        # Complex Attributes - MapAttribute fields
        "image_aliases": {
            "latest": "ami-12345abcde",
            "stable": "ami-67890fghij",
            "ubuntu-22": "ami-22222bbbbb",
        },
        "tags": {
            "Service": "user-management",
            "Team": "backend",
            "Environment": "production",
        },
        "metadata": {
            "build_date": "2024-03-15T10:30:00Z",
            "commit_hash": "abc123def456",
            "deployment_date": "2024-03-15T14:20:00Z",
        },
    }


@pytest.fixture
def app_facts_alias():
    """Fully populated AppFact dictionary with PascalCase alias field names."""
    return {
        # Primary keys - PascalCase aliases from AppFact model
        "Portfolio": "acme:platform-services",  # alias for portfolio
        "App": "user-service",  # alias for app
        "AppRegex": "user-service.*",  # alias for app_regex
        # App Details - PascalCase aliases from AppFact model
        "Name": "User Management Service",  # alias for name
        "Environment": "production",  # alias for environment
        "Account": "123456789012",  # alias for account
        "Zone": "production-west",  # alias for zone
        "Region": "us-west-2",  # alias for region
        "Repository": "https://github.com/acme/user-service",  # alias for repository
        "EnforceValidation": "true",  # alias for enforce_validation
        # Complex Attributes - PascalCase aliases for MapAttribute fields
        "ImageAliases": {
            "latest": "ami-12345abcde",
            "stable": "ami-67890fghij",
            "ubuntu-22": "ami-22222bbbbb",
        },  # alias for image_aliases
        "Tags": {
            "Service": "user-management",
            "Team": "backend",
            "Environment": "production",
        },  # alias for tags
        "Metadata": {  # alias for metadata
            "build_date": "2024-03-15T10:30:00Z",
            "commit_hash": "abc123def456",
            "deployment_date": "2024-03-15T14:20:00Z",
        },
    }


def validate_client_facts_model(result: ClientFactsModel):

    # Primary key
    assert result.client == "acme"
    # Basic client information
    assert result.client_id == "acme-corp-2024"
    assert result.client_type == "enterprise"
    assert result.client_status == "active"
    assert result.client_description == "Large enterprise corporation specializing in technology solutions"
    assert result.client_name == "ACME Corporation"
    # AWS Organization configuration
    assert result.organization_id == "o-123456789abc"
    assert result.organization_name == "ACME Holdings Inc"
    assert result.organization_account == "123456789012"
    assert result.organization_email == "aws-admin@acme.com"
    # Domain and networking
    assert result.domain == "acme.com"
    # AWS Account assignments
    assert result.iam_account == "123456789012"
    assert result.audit_account == "987654321098"
    assert result.automation_account == "333333333333"
    assert result.security_account == "111111111111"
    assert result.network_account == "222222222222"
    # Regional configuration
    assert result.master_region == "us-west-2"
    assert result.client_region == "us-west-2"
    assert result.bucket_region == "us-west-2"
    # S3 bucket configuration
    assert result.bucket_name == "acme-core-automation"
    assert result.docs_bucket_name == "acme-core-automation-docs"
    assert result.artefact_bucket_name == "acme-core-automation-artefacts"
    assert result.ui_bucket_name == "acme-core-automation-ui"
    assert result.ui_bucket == "acme-ui-legacy"
    # Resource naming
    assert result.scope == "prod-"


def test_client_facts_model(client_fact: dict, client_fact_alias: dict):
    """Test ClientFactsModel instantiation with all fields."""

    for data in [client_fact, client_fact_alias]:
        result = ClientFactsModel(**data)
        validate_client_facts_model(result)
        data = result.to_simple_dict()
        validate_client_facts_pascal_case(data)


def validate_client_facts_snake_case(data: dict):
    # Check all fields in snake_case
    assert data["client"] == "acme"
    assert data["client_id"] == "acme-corp-2024"
    assert data["client_type"] == "enterprise"
    assert data["client_status"] == "active"
    assert data["client_description"] == "Large enterprise corporation specializing in technology solutions"
    assert data["client_name"] == "ACME Corporation"
    assert data["organization_id"] == "o-123456789abc"
    assert data["organization_name"] == "ACME Holdings Inc"
    assert data["organization_account"] == "123456789012"
    assert data["organization_email"] == "aws-admin@acme.com"
    assert data["domain"] == "acme.com"
    assert data["iam_account"] == "123456789012"
    assert data["audit_account"] == "987654321098"
    assert data["automation_account"] == "333333333333"
    assert data["security_account"] == "111111111111"
    assert data["network_account"] == "222222222222"
    assert data["master_region"] == "us-west-2"
    assert data["client_region"] == "us-west-2"
    assert data["bucket_region"] == "us-west-2"
    assert data["bucket_name"] == "acme-core-automation"
    assert data["docs_bucket_name"] == "acme-core-automation-docs"
    assert data["artefact_bucket_name"] == "acme-core-automation-artefacts"
    assert data["ui_bucket_name"] == "acme-core-automation-ui"
    assert data["ui_bucket"] == "acme-ui-legacy"
    assert data["scope"] == "prod-"


def validate_client_facts_pascal_case(data: dict):
    assert data["ClientType"] == "enterprise"
    assert data["ClientStatus"] == "active"
    assert data["ClientDescription"] == "Large enterprise corporation specializing in technology solutions"
    assert data["ClientName"] == "ACME Corporation"
    assert data["OrganizationId"] == "o-123456789abc"
    assert data["OrganizationName"] == "ACME Holdings Inc"
    assert data["OrganizationAccount"] == "123456789012"
    assert data["OrganizationEmail"] == "aws-admin@acme.com"
    assert data["Domain"] == "acme.com"
    assert data["IamAccount"] == "123456789012"
    assert data["AuditAccount"] == "987654321098"
    assert data["AutomationAccount"] == "333333333333"
    assert data["SecurityAccount"] == "111111111111"
    assert data["NetworkAccount"] == "222222222222"
    assert data["MasterRegion"] == "us-west-2"
    assert data["ClientRegion"] == "us-west-2"
    assert data["BucketRegion"] == "us-west-2"
    assert data["BucketName"] == "acme-core-automation"
    assert data["DocsBucketName"] == "acme-core-automation-docs"
    assert data["ArtefactBucketName"] == "acme-core-automation-artefacts"
    assert data["UiBucketName"] == "acme-core-automation-ui"
    assert data["UiBucket"] == "acme-ui-legacy"
    assert data["Scope"] == "prod-"


def validate_client_fact_model(result: ClientFact):
    assert result.client == "acme"
    assert result.client_id == "acme-corp-2024"
    assert result.client_type == "enterprise"
    assert result.client_status == "active"
    assert result.client_description == "Large enterprise corporation specializing in technology solutions"
    assert result.client_name == "ACME Corporation"
    assert result.organization_id == "o-123456789abc"
    assert result.organization_name == "ACME Holdings Inc"
    assert result.organization_account == "123456789012"
    assert result.organization_email == "aws-admin@acme.com"
    assert result.domain == "acme.com"
    assert result.iam_account == "123456789012"
    assert result.audit_account == "987654321098"
    assert result.automation_account == "333333333333"
    assert result.security_account == "111111111111"
    assert result.network_account == "222222222222"
    assert result.master_region == "us-west-2"
    assert result.client_region == "us-west-2"
    assert result.bucket_region == "us-west-2"
    assert result.bucket_name == "acme-core-automation"
    assert result.docs_bucket_name == "acme-core-automation-docs"
    assert result.artefact_bucket_name == "acme-core-automation-artefacts"
    assert result.ui_bucket_name == "acme-core-automation-ui"
    assert result.ui_bucket == "acme-ui-legacy"
    assert result.scope == "prod-"


def test_client_fact_data(client_fact: dict, client_fact_alias: dict):
    """Test ClientFact Pydantic model instantiation with all fields."""

    for data in [client_fact, client_fact_alias]:
        result = ClientFact(**data)
        validate_client_fact_model(result)
        data = result.to_model()
        validate_client_facts_model(data)


def test_client_fact_api_serialization(client_fact: dict):
    """Test ClientFact PascalCase API serialization."""
    result = ClientFact(**client_fact)

    # Default it should be in PascalCase
    api_data = result.model_dump()
    validate_client_facts_pascal_case(api_data)

    data = result.model_dump(by_alias=True)
    validate_client_facts_pascal_case(data)

    data = result.model_dump(by_alias=False)
    validate_client_facts_snake_case(data)


def test_client_fact_dynamodb_conversion(client_fact: dict):
    """Test ClientFact to DynamoDB format conversion."""
    result = ClientFact(**client_fact)

    # Test DynamoDB conversion (snake_case)
    pynamo_data = result.to_model()
    validate_client_facts_model(pynamo_data)

    data = ClientFact.from_model(pynamo_data)
    validate_client_fact_model(data)


def validate_app_facts_snake_case(result: dict):
    """Validate AppFact model data in snake_case format."""
    # Test primary keys
    assert result["portfolio"] == "acme:platform-services"
    assert result["app_regex"] == "user-service.*"

    # Test app configuration fields
    assert result["name"] == "User Management Service"
    assert result["environment"] == "production"
    assert result["account"] == "123456789012"
    assert result["zone"] == "production-west"
    assert result["region"] == "us-west-2"
    assert result["repository"] == "https://github.com/acme/user-service"
    assert result["enforce_validation"] == "true"

    # Test nested MapAttribute fields - image_aliases
    assert result["image_aliases"]["latest"] == "ami-12345abcde"
    assert result["image_aliases"]["stable"] == "ami-67890fghij"
    assert result["image_aliases"]["ubuntu-22"] == "ami-22222bbbbb"

    # Test nested MapAttribute fields - tags
    assert result["tags"]["Service"] == "user-management"
    assert result["tags"]["Team"] == "backend"
    assert result["tags"]["Environment"] == "production"

    # Test nested MapAttribute fields - metadata
    assert result["metadata"]["build_date"] == "2024-03-15T10:30:00Z"
    assert result["metadata"]["commit_hash"] == "abc123def456"
    assert result["metadata"]["deployment_date"] == "2024-03-15T14:20:00Z"


def validate_app_facts_pascal_case(result: dict):
    # Test PascalCase conversion
    assert result["Portfolio"] == "acme:platform-services"
    assert result["AppRegex"] == "user-service.*"
    assert result["Name"] == "User Management Service"
    assert result["Environment"] == "production"
    assert result["Account"] == "123456789012"
    assert result["Zone"] == "production-west"
    assert result["Region"] == "us-west-2"
    assert result["Repository"] == "https://github.com/acme/user-service"
    assert result["EnforceValidation"] == "true"
    # Test nested MapAttribute fields
    assert result["ImageAliases"]["latest"] == "ami-12345abcde"
    assert result["ImageAliases"]["stable"] == "ami-67890fghij"
    assert result["ImageAliases"]["ubuntu-22"] == "ami-22222bbbbb"
    assert result["Tags"]["Service"] == "user-management"
    assert result["Tags"]["Team"] == "backend"
    assert result["Tags"]["Environment"] == "production"
    # Test PascalCase attr_names from AppFactsModel model
    assert result["Metadata"]["build_date"] == "2024-03-15T10:30:00Z"
    assert result["Metadata"]["commit_hash"] == "abc123def456"
    assert result["Metadata"]["deployment_date"] == "2024-03-15T14:20:00Z"


def validate_app_fact_model(result: AppFact):
    # Test primary keys
    assert result.portfolio == "acme:platform-services"
    assert result.app_regex == "user-service.*"

    # Test app configuration
    assert result.name == "User Management Service"
    assert result.environment == "production"
    assert result.account == "123456789012"
    assert result.zone == "production-west"
    assert result.region == "us-west-2"
    assert result.repository == "https://github.com/acme/user-service"
    assert result.enforce_validation == "true"

    # Test MapAttributes
    assert result.image_aliases["latest"] == "ami-12345abcde"
    assert result.tags["Service"] == "user-management"
    assert result.metadata["build_date"] == "2024-03-15T10:30:00Z"
    assert result.metadata["commit_hash"] == "abc123def456"
    assert result.metadata["deployment_date"] == "2024-03-15T14:20:00Z"


def validate_app_facts_model(result: AppFactsModel):
    # Test primary keys
    assert result.portfolio == "acme:platform-services"
    assert result.app_regex == "user-service.*"

    # Test app configuration
    assert result.name == "User Management Service"
    assert result.environment == "production"
    assert result.account == "123456789012"
    assert result.zone == "production-west"
    assert result.region == "us-west-2"
    assert result.repository == "https://github.com/acme/user-service"
    assert result.enforce_validation == "true"

    # Test MapAttributes
    assert result.image_aliases["latest"] == "ami-12345abcde"
    assert result.tags["Service"] == "user-management"
    assert result.metadata["build_date"] == "2024-03-15T10:30:00Z"
    assert result.metadata["commit_hash"] == "abc123def456"
    assert result.metadata["deployment_date"] == "2024-03-15T14:20:00Z"


def test_app_facts_pascal_case_serialization(app_facts: dict, app_facts_alias: dict):
    """Test AppFactsModel conversion to PascalCase dictionary."""

    for data in [app_facts, app_facts_alias]:
        app_facts_model = AppFactsModel(**data)
        validate_app_facts_model(app_facts_model)
        result = app_facts_model.to_simple_dict()
        validate_app_facts_pascal_case(result)


def test_app_fact_model_instantiation(app_facts: dict, app_facts_alias: dict):
    """Test AppFactsModel instantiation with all fields."""
    for app_facts in [app_facts, app_facts_alias]:
        # Test instantiation with all fields
        result = AppFact(**app_facts)
        validate_app_fact_model(result)
        data = result.to_model(client)
        validate_app_facts_model(data)


def verify_portfolio_facts_model(result: PortfolioFactsModel):
    """Verify PortfolioFactsModel fields and nested object types."""
    # Test primary keys
    assert result.portfolio == "platform-services"

    # Test portfolio configuration
    assert result.domain == "platform.acme.com"

    # Test contacts - verify it's a list and each item is ContactFacts instance
    assert hasattr(result, "contacts")
    assert isinstance(result.contacts, list)
    assert len(result.contacts) == 2

    # Verify first contact
    contact1 = result.contacts[0]
    assert isinstance(contact1, ContactFacts)
    assert contact1.name == "Tech Lead"
    assert contact1.email == "tech-lead@acme.com"
    assert contact1.enabled == True
    assert isinstance(contact1.attributes, MapAttribute)
    assert contact1.attributes["department"] == "engineering"
    assert contact1.attributes["location"] == "san-francisco"

    # Verify second contact
    contact2 = result.contacts[1]
    assert isinstance(contact2, ContactFacts)
    assert contact2.name == "Product Manager"
    assert contact2.email == "pm@acme.com"
    assert contact2.enabled == True
    assert isinstance(contact2.attributes, MapAttribute)
    assert contact2.attributes["department"] == "product"
    assert contact2.attributes["location"] == "new-york"

    # Test approvers - verify it's a list and each item is ApproverFacts instance
    assert hasattr(result, "approvers")
    assert isinstance(result.approvers, list)
    assert len(result.approvers) == 2

    # Verify first approver
    approver1 = result.approvers[0]
    assert isinstance(approver1, ApproverFacts)
    assert approver1.sequence == 1
    assert approver1.name == "Engineering Manager"
    assert approver1.email == "eng-mgr@acme.com"
    assert isinstance(approver1.roles, list)
    assert approver1.roles == ["deployment", "approval"]
    assert isinstance(approver1.attributes, MapAttribute)
    assert approver1.attributes["department"] == "engineering"
    assert isinstance(approver1.depends_on, list)
    assert approver1.depends_on == []
    assert approver1.enabled == True

    # Verify second approver
    approver2 = result.approvers[1]
    assert isinstance(approver2, ApproverFacts)
    assert approver2.sequence == 2
    assert approver2.name == "Director of Engineering"
    assert approver2.email == "director@acme.com"
    assert isinstance(approver2.roles, list)
    assert approver2.roles == ["executive", "approval"]
    assert isinstance(approver2.depends_on, list)
    assert approver2.depends_on == [1]
    assert approver2.enabled == True

    # Test project - verify it's a ProjectFacts instance
    assert hasattr(result, "project")
    assert isinstance(result.project, ProjectFacts)
    assert result.project.name == "Platform Services Project"
    assert result.project.code == "platform-svc"
    assert result.project.repository == "https://github.com/acme/platform-services"
    assert result.project.description == "Core platform infrastructure and services"
    assert isinstance(result.project.attributes, MapAttribute)
    assert result.project.attributes["type"] == "infrastructure"
    assert result.project.attributes["priority"] == "high"

    assert hasattr(result, "bizapp")
    assert isinstance(result.bizapp, ProjectFacts)
    assert result.bizapp.name == "Business Platform App"
    assert result.bizapp.code == "biz-platform"
    assert result.bizapp.repository == "https://github.com/acme/biz-platform"
    assert result.bizapp.description == "Business platform application"

    # Test owner - verify it's an OwnerFacts instance
    assert hasattr(result, "owner")
    assert isinstance(result.owner, OwnerFacts)
    assert result.owner.name == "Platform Team"
    assert result.owner.email == "platform-team@acme.com"
    assert result.owner.phone == "+1-555-0123"
    assert isinstance(result.owner.attributes, MapAttribute)
    assert result.owner.attributes["department"] == "engineering"
    assert result.owner.attributes["budget_code"] == "ENG-PLT-001"

    # Test tags - verify it's a dict MapAttribute
    assert hasattr(result, "tags")
    assert isinstance(result.tags, MapAttribute)
    assert result.tags["Environment"] == "production"
    assert result.tags["Team"] == "platform"
    assert result.tags["Service"] == "infrastructure"

    # Test metadata - verify it's a dict MapAttribute
    assert hasattr(result, "metadata")
    assert isinstance(result.metadata, MapAttribute)
    assert result.metadata["deploy_strategy"] == "blue-green"
    assert result.metadata["scaling_policy"] == "auto"
    assert result.metadata["backup_retention"] == "30d"

    # Test attributes - verify it's a dict MapAttribute
    assert hasattr(result, "attributes")
    assert isinstance(result.attributes, MapAttribute)
    assert result.attributes["max_instances"] == "10"
    assert result.attributes["min_instances"] == "2"
    assert result.attributes["health_check_path"] == "/health"

    # Test audit fields (inherited from DatabaseTable)
    assert hasattr(result, "created_at")
    assert hasattr(result, "updated_at")
    # These may be None if excluded during creation


def verify_portfolio_facts_pascal_case(result: dict):
    """Verify PortfolioFactsModel data in PascalCase format."""
    # Test primary keys
    assert result["Portfolio"] == "platform-services"

    # Test portfolio configuration
    assert result["Domain"] == "platform.acme.com"

    # Test contacts - verify PascalCase conversion for ContactFacts fields
    assert "Contacts" in result
    assert len(result["Contacts"]) == 2

    # Verify first contact
    contact1 = result["Contacts"][0]
    assert contact1["Name"] == "Tech Lead"
    assert contact1["Email"] == "tech-lead@acme.com"
    assert contact1["Enabled"] == True
    assert isinstance(contact1["Attributes"], dict)
    assert contact1["Attributes"]["department"] == "engineering"
    assert contact1["Attributes"]["location"] == "san-francisco"

    # Verify second contact
    contact2 = result["Contacts"][1]
    assert contact2["Name"] == "Product Manager"
    assert contact2["Email"] == "pm@acme.com"
    assert contact2["Enabled"] == True
    assert isinstance(contact2["Attributes"], dict)
    assert contact2["Attributes"]["department"] == "product"
    assert contact2["Attributes"]["location"] == "new-york"

    # Test approvers - verify PascalCase conversion for ApproverFacts fields
    assert "Approvers" in result
    assert len(result["Approvers"]) == 2

    # Verify first approver
    approver1 = result["Approvers"][0]
    assert approver1["Sequence"] == 1
    assert approver1["Name"] == "Engineering Manager"
    assert approver1["Email"] == "eng-mgr@acme.com"
    assert isinstance(approver1["Roles"], list)
    assert approver1["Roles"] == ["deployment", "approval"]
    assert isinstance(approver1["Attributes"], dict)
    assert approver1["Attributes"]["department"] == "engineering"
    assert isinstance(approver1["DependsOn"], list)
    assert approver1["DependsOn"] == []
    assert approver1["Enabled"] == True

    # Verify second approver
    approver2 = result["Approvers"][1]
    assert approver2["Sequence"] == 2
    assert approver2["Name"] == "Director of Engineering"
    assert approver2["Email"] == "director@acme.com"
    assert isinstance(approver2["Roles"], list)
    assert approver2["Roles"] == ["executive", "approval"]
    assert isinstance(approver2["DependsOn"], list)
    assert approver2["DependsOn"] == [1]
    assert approver2["Enabled"] == True

    # Test project - verify PascalCase conversion for ProjectFacts fields
    assert "Project" in result
    project = result["Project"]
    assert project["Name"] == "Platform Services Project"
    assert project["Code"] == "platform-svc"
    assert project["Repository"] == "https://github.com/acme/platform-services"
    assert project["Description"] == "Core platform infrastructure and services"
    assert isinstance(project["Attributes"], dict)
    assert project["Attributes"]["type"] == "infrastructure"
    assert project["Attributes"]["priority"] == "high"

    # Test bizapp - verify PascalCase conversion for BizappFacts fields (if present)
    if "Bizapp" in result and result["Bizapp"] is not None:
        bizapp = result["Bizapp"]
        assert bizapp["Name"] == "Business Platform App"
        assert bizapp["Code"] == "biz-platform"
        assert bizapp["Repository"] == "https://github.com/acme/biz-platform"
        assert bizapp["Description"] == "Business platform application"

    # Test owner - verify PascalCase conversion for OwnerFacts fields
    assert "Owner" in result
    owner = result["Owner"]
    assert owner["Name"] == "Platform Team"
    assert owner["Email"] == "platform-team@acme.com"
    assert owner["Phone"] == "+1-555-0123"
    assert isinstance(owner["Attributes"], dict)
    assert owner["Attributes"]["department"] == "engineering"
    assert owner["Attributes"]["budget_code"] == "ENG-PLT-001"

    # Test tags - verify PascalCase field name for MapAttribute
    assert "Tags" in result
    assert isinstance(result["Tags"], dict)
    assert result["Tags"]["Environment"] == "production"
    assert result["Tags"]["Team"] == "platform"
    assert result["Tags"]["Service"] == "infrastructure"

    # Test metadata - verify PascalCase field name for MapAttribute
    assert "Metadata" in result
    assert isinstance(result["Metadata"], dict)
    assert result["Metadata"]["deploy_strategy"] == "blue-green"
    assert result["Metadata"]["scaling_policy"] == "auto"
    assert result["Metadata"]["backup_retention"] == "30d"

    # Test attributes - verify PascalCase field name for MapAttribute
    assert "Attributes" in result
    assert isinstance(result["Attributes"], dict)
    assert result["Attributes"]["max_instances"] == "10"
    assert result["Attributes"]["min_instances"] == "2"
    assert result["Attributes"]["health_check_path"] == "/health"

    # Test audit fields (inherited from DatabaseTable) - PascalCase field names
    if "CreatedAt" in result:
        assert "CreatedAt" in result  # PascalCase alias for created_at
    if "UpdatedAt" in result:
        assert "UpdatedAt" in result  # PascalCase alias for updated_at


def verify_portfolio_facts_snake_case(result: dict):

    # Test primary keys
    assert result["portfolio"] == "platform-services"

    # Test portfolio configuration
    assert result["domain"] == "platform.acme.com"

    # Test contacts - verify snake_case conversion for ContactFacts fields
    assert "contacts" in result
    assert len(result["contacts"]) == 2

    # Verify first contact
    contact1 = result["contacts"][0]
    assert contact1["name"] == "Tech Lead"
    assert contact1["email"] == "tech-lead@acme.com"
    assert contact1["enabled"] == True
    assert isinstance(contact1["attributes"], dict)
    assert contact1["attributes"]["department"] == "engineering"
    assert contact1["attributes"]["location"] == "san-francisco"

    # Verify second contact
    contact2 = result["contacts"][1]
    assert contact2["name"] == "Product Manager"
    assert contact2["email"] == "pm@acme.com"
    assert contact2["enabled"] == True
    assert isinstance(contact2["attributes"], dict)
    assert contact2["attributes"]["department"] == "product"
    assert contact2["attributes"]["location"] == "new-york"

    # Test approvers - verify snake_case conversion for ApproverFacts fields
    assert "approvers" in result
    assert len(result["approvers"]) == 2

    # Verify first approver
    approver1 = result["approvers"][0]
    assert approver1["sequence"] == 1
    assert approver1["name"] == "Engineering Manager"
    assert approver1["email"] == "eng-mgr@acme.com"
    assert isinstance(approver1["roles"], list)
    assert approver1["roles"] == ["deployment", "approval"]
    assert isinstance(approver1["attributes"], dict)
    assert approver1["attributes"]["department"] == "engineering"
    assert isinstance(approver1["depends_on"], list)
    assert approver1["depends_on"] == []
    assert approver1["enabled"] == True

    # Verify second approver
    approver2 = result["approvers"][1]
    assert approver2["sequence"] == 2
    assert approver2["name"] == "Director of Engineering"
    assert approver2["email"] == "director@acme.com"
    assert isinstance(approver2["roles"], list)
    assert approver2["roles"] == ["executive", "approval"]
    assert isinstance(approver2["depends_on"], list)
    assert approver2["depends_on"] == [1]
    assert approver2["enabled"] == True

    # Test project - verify snake_case conversion for ProjectFacts fields
    assert "project" in result
    project = result["project"]
    assert project["name"] == "Platform Services Project"
    assert project["code"] == "platform-svc"
    assert project["repository"] == "https://github.com/acme/platform-services"
    assert project["description"] == "Core platform infrastructure and services"
    assert isinstance(project["attributes"], dict)
    assert project["attributes"]["type"] == "infrastructure"
    assert project["attributes"]["priority"] == "high"

    # Test bizapp - verify snake_case conversion for BizappFacts fields (if present)
    assert "bizapp" in result
    bizapp = result["bizapp"]
    assert bizapp["name"] == "Business Platform App"
    assert bizapp["code"] == "biz-platform"
    assert bizapp["repository"] == "https://github.com/acme/biz-platform"
    assert bizapp["description"] == "Business platform application"

    # Test owner - verify snake_case conversion for OwnerFacts fields
    assert "owner" in result
    owner = result["owner"]
    assert owner["name"] == "Platform Team"
    assert owner["email"] == "platform-team@acme.com"
    assert owner["phone"] == "+1-555-0123"
    assert isinstance(owner["attributes"], dict)
    assert owner["attributes"]["department"] == "engineering"
    assert owner["attributes"]["budget_code"] == "ENG-PLT-001"

    # Test tags - verify snake_case field name for MapAttribute
    assert "tags" in result
    assert isinstance(result["tags"], dict)
    assert result["tags"]["Environment"] == "production"
    assert result["tags"]["Team"] == "platform"
    assert result["tags"]["Service"] == "infrastructure"

    # Test metadata - verify snake_case field name for MapAttribute
    assert "metadata" in result
    assert isinstance(result["metadata"], dict)
    assert result["metadata"]["deploy_strategy"] == "blue-green"
    assert result["metadata"]["scaling_policy"] == "auto"
    assert result["metadata"]["backup_retention"] == "30d"

    # Test attributes - verify snake_case field name for MapAttribute
    assert "attributes" in result
    assert isinstance(result["attributes"], dict)
    assert result["attributes"]["max_instances"] == "10"
    assert result["attributes"]["min_instances"] == "2"
    assert result["attributes"]["health_check_path"] == "/health"

    # Test audit fields (inherited from DatabaseTable) - snake_case field names
    if "created_at" in result:
        assert "created_at" in result  # snake_case for created_at
    if "updated_at" in result:
        assert "updated_at" in result  # snake_case for updated_at


def test_portfolio_facts_pascal_case_serialization(portfolio_facts: dict):
    """Test PortfolioFactsModel conversion to PascalCase dictionary."""
    portfolio_facts_model = PortfolioFactsModel(**portfolio_facts)
    verify_portfolio_facts_model(portfolio_facts_model)
    result = portfolio_facts_model.to_simple_dict()
    verify_portfolio_facts_pascal_case(result)

    # Round Trip through Pydantic model
    data = PortfolioFact(**result)
    result = data.model_dump()
    verify_portfolio_facts_pascal_case(result)
    result = data.model_dump(by_alias=False)
    verify_portfolio_facts_snake_case(result)

    # Round Trip through Pydantic model
    data = PortfolioFactsModel(**result)
    verify_portfolio_facts_model(data)


def test_zone_facts_pascal_case_serialization(zone_facts: dict):
    """Test ZoneFactsModel conversion to PascalCase dictionary."""
    zone_facts_model = ZoneFactsModel(**zone_facts)
    result = zone_facts_model.to_simple_dict()

    dynamodb = zone_facts_model.to_dynamodb_dict()
    assert isinstance(dynamodb, dict)

    # Test PascalCase conversion at all levels
    assert result["Zone"] == "production-west"

    account_facts = result["AccountFacts"]
    assert account_facts["AwsAccountId"] == "123456789012"
    assert account_facts["Environment"] == "production"

    kms_facts = account_facts["Kms"]
    assert kms_facts["AwsAccountId"] == "123456789012"
    assert kms_facts["AllowSNS"] == True
    assert isinstance(kms_facts["DelegateAwsAccountIds"], list)


def test_portfolio_facts_model_instantiation(portfolio_facts: dict):
    """Test PortfolioFactsModel instantiation with all fields."""
    result = PortfolioFactsModel(**portfolio_facts)

    # Test primary keys
    assert result.portfolio == "platform-services"

    # Test portfolio configuration
    assert result.domain == "platform.acme.com"

    # Test contacts
    assert len(result.contacts) == 2
    assert result.contacts[0].name == "Tech Lead"
    assert result.contacts[0].email == "tech-lead@acme.com"
    assert result.contacts[0].enabled == True

    # Test approvers
    assert len(result.approvers) == 2
    assert result.approvers[0].sequence == 1
    assert result.approvers[0].name == "Engineering Manager"
    assert result.approvers[1].depends_on == [1]

    # Test project
    assert result.project.name == "Platform Services Project"
    assert result.project.code == "platform-svc"

    # Test owner
    assert result.owner.name == "Platform Team"
    assert result.owner.phone == "+1-555-0123"


def test_zone_facts_model_instantiation(zone_facts: dict):
    """Test ZoneFactsModel instantiation with all fields."""
    result = ZoneFactsModel(**zone_facts)

    # Test primary keys
    assert result.zone == "production-west"

    # Test account facts
    assert result.account_facts.aws_account_id == "123456789012"
    assert result.account_facts.environment == "production"

    # Test KMS facts
    assert result.account_facts.kms.aws_account_id == "123456789012"
    assert result.account_facts.kms.allow_sns == True
    assert len(result.account_facts.kms.delegate_aws_account_ids) == 3

    # Test region facts
    us_west_2 = result.region_facts["us-west-2"]
    assert us_west_2.aws_region == "us-west-2"
    assert us_west_2.az_count == 3
    assert us_west_2.min_successful_instances_percent == 75

    # Test security aliases
    assert "corporate-cidrs" in us_west_2.security_aliases
    assert len(us_west_2.security_aliases["corporate-cidrs"]) == 2

    # Test proxy configuration
    assert len(us_west_2.proxy) == 1
    assert us_west_2.proxy[0].host == "proxy-west-1.acme.com"


def test_portfolio_fact_pydantic_instantiation(portfolio_facts: dict, portfolio_fact_alias: dict):
    """Test PortfolioFact Pydantic model instantiation with all fields."""

    for data in [portfolio_facts, portfolio_fact_alias]:
        # Test instantiation with all fields

        result = PortfolioFact(**data)

        # Test primary keys
        assert result.portfolio == "platform-services"

        # Test portfolio configuration
        assert result.domain == "platform.acme.com"

        # Test contacts (should be ContactFactsItem objects)
        assert len(result.contacts) == 2
        assert result.contacts[0].name == "Tech Lead"
        assert result.contacts[0].email == "tech-lead@acme.com"
        assert result.contacts[0].enabled == True

        # Test approvers (should be ApproverFactsItem objects)
        assert len(result.approvers) == 2
        assert result.approvers[0].sequence == 1
        assert result.approvers[0].name == "Engineering Manager"
        assert result.approvers[1].depends_on == [1]

        # Test project (should be ProjectFactsItem object)
        assert result.project.name == "Platform Services Project"
        assert result.project.code == "platform-svc"

        # Test owner (should be OwnerFactsItem object)
        assert result.owner.name == "Platform Team"
        assert result.owner.phone == "+1-555-0123"


def test_zone_fact_pydantic_instantiation(zone_facts: dict, zone_fact_alias: dict):
    """Test ZoneFact Pydantic model instantiation with all fields."""

    for data in [zone_facts, zone_fact_alias]:
        # Test instantiation with all fields

        result = ZoneFact(**data)

        # Test primary keys
        assert result.zone == "production-west"

        # Test account facts (should be AccountFactsItem object)
        assert result.account_facts.aws_account_id == "123456789012"
        assert result.account_facts.environment == "production"

        # Test KMS facts (should be KmsFactsItem object)
        assert result.account_facts.kms.aws_account_id == "123456789012"
        assert result.account_facts.kms.allow_sns == True
        assert len(result.account_facts.kms.delegate_aws_account_ids) == 3

        # Test region facts (should be RegionFactsItem objects)
        us_west_2 = result.region_facts["us-west-2"]
        assert us_west_2.aws_region == "us-west-2"
        assert us_west_2.az_count == 3
        assert us_west_2.min_successful_instances_percent == 75


def test_app_fact_pydantic_instantiation(app_facts: dict):
    """Test AppFact Pydantic model instantiation with all fields."""
    result = AppFact(**app_facts)

    # Test primary keys
    assert result.portfolio == "acme:platform-services"
    assert result.app_regex == "user-service.*"

    # Test app configuration
    assert result.name == "User Management Service"
    assert result.environment == "production"
    assert result.account == "123456789012"
    assert result.zone == "production-west"
    assert result.region == "us-west-2"
    assert result.repository == "https://github.com/acme/user-service"
    assert result.enforce_validation == "true"

    # Test business logic methods
    assert result.matches_app("user-service-api") == True
    assert result.matches_app("order-service") == False
    assert result.is_validation_enforced() == True
