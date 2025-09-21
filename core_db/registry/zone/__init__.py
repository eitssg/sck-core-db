"""Zone Registry module for the core-automation-registry DynamoDB table.

This module provides comprehensive zone management for the registry system, combining
both data models and action classes to enable complete CRUD operations for zone FACTS
records with proper client-zone hierarchy and deployment environment management.

Key Components:
    - **ZoneActions**: CRUD operations for zone registry management
    - **ZoneFactsModel**: PynamoDB model for DynamoDB zone registry operations
    - **ZoneFactsFactory**: Factory for creating client-specific model instances
    - **AccountFacts**: AWS account information data model for zones
    - **RegionFacts**: AWS region configuration data model for zones
    - **KmsFacts**: KMS key management data model for zones
    - **SecurityAliasFacts**: Security alias configuration data model for zones
    - **ProxyFacts**: Proxy configuration data model for zones

Features:
    - **Zone Lifecycle Management**: Complete CRUD operations for zone entities
    - **Client-Zone Hierarchy**: Proper hierarchical organization within client namespaces
    - **Deployment Environment Support**: Configuration for development, staging, production environments
    - **AWS Resource Integration**: Support for accounts, regions, KMS, security, and proxy configurations
    - **Client Isolation**: Factory pattern ensures proper table isolation between clients

Zone Structure:
    Zones are stored with a composite key structure in client-specific tables:
    - **Hash Key**: client (client identifier for data partitioning)
    - **Range Key**: zone (zone name within client namespace)
    - **Attributes**: Zone-specific metadata, AWS resources, and environment configuration

Schema Structure:
    The zone registry schema includes:
    - **Client**: Hash key (client identifier)
    - **Zone**: Range key (zone name within client)
    - **description**: Human-readable zone description
    - **region**: AWS region for the zone
    - **environment_type**: Environment classification (development, staging, production)
    - **vpc_id**: VPC identifier for network isolation
    - **subnet_ids**: List of subnet identifiers for deployment
    - **security_group_ids**: List of security group identifiers
    - **availability_zones**: List of availability zones for high availability
    - **account_facts**: AccountFacts for AWS account configuration
    - **region_facts**: RegionFacts for region-specific settings
    - **kms_facts**: KmsFacts for encryption key management
    - **security_alias_facts**: SecurityAliasFacts for security configurations
    - **proxy_facts**: ProxyFacts for proxy and networking configurations

Examples:
    >>> from core_db.registry.zone import (
    ...     ZoneActions, ZoneFactsModel, ZoneFactsFactory,
    ...     AccountFacts, RegionFacts, KmsFacts, SecurityAliasFacts, ProxyFacts
    ... )

    >>> # Create a new zone with comprehensive AWS configuration
    >>> result = ZoneActions.create(
    ...     client="acme",
    ...     zone="us-east-1-prod",
    ...     description="Production environment in US East",
    ...     region="us-east-1",
    ...     environment_type="production",
    ...     vpc_id="vpc-12345678",
    ...     subnet_ids=["subnet-abcd1234", "subnet-efgh5678", "subnet-ijkl9012"],
    ...     security_group_ids=["sg-web-prod", "sg-app-prod", "sg-db-prod"],
    ...     availability_zones=["us-east-1a", "us-east-1b", "us-east-1c"],
    ...     account_facts=AccountFacts(
    ...         account_id="123456789012",
    ...         account_name="acme-production",
    ...         billing_contact="billing@acme.com"
    ...     ),
    ...     region_facts=RegionFacts(
    ...         region_name="us-east-1",
    ...         endpoint_url="https://ec2.us-east-1.amazonaws.com",
    ...         availability_zones=["us-east-1a", "us-east-1b", "us-east-1c"]
    ...     ),
    ...     kms_facts=KmsFacts(
    ...         key_id="arn:aws:kms:us-east-1:123456789012:key/abcd1234-5678-90ef-1234-567890abcdef",
    ...         key_alias="alias/acme-prod-encryption",
    ...         encryption_context={"Environment": "Production", "Client": "acme"}
    ...     )
    ... )

    >>> # List all zones for a client
    >>> zones = ZoneActions.list(client="acme")
    >>> for zone in zones.data:
    ...     print(f"Zone: {zone['Zone']}")
    ...     print(f"Description: {zone.get('description')}")
    ...     print(f"Environment: {zone.get('environment_type')}")
    ...     print(f"Region: {zone.get('region')}")

    >>> # Get specific zone with full AWS configuration
    >>> zone = ZoneActions.get(client="acme", zone="us-east-1-prod")
    >>> if zone.data:
    ...     print(f"VPC ID: {zone.data.get('vpc_id')}")
    ...     print(f"Subnets: {zone.data.get('subnet_ids', [])}")
    ...     print(f"Security Groups: {zone.data.get('security_group_ids', [])}")
    ...     account_info = zone.data.get('account_facts', {})
    ...     print(f"Account: {account_info.get('account_id')}")

    >>> # Update zone with security and proxy configuration
    >>> result = ZoneActions.patch(
    ...     client="acme",
    ...     zone="us-east-1-prod",
    ...     monitoring_enabled=True,
    ...     backup_retention_days=30,
    ...     security_alias_facts=SecurityAliasFacts(
    ...         security_alias="acme-prod-security",
    ...         iam_role_arn="arn:aws:iam::123456789012:role/AcmeProdRole",
    ...         security_policy="strict"
    ...     ),
    ...     proxy_facts=ProxyFacts(
    ...         proxy_enabled=True,
    ...         proxy_host="proxy.acme.com",
    ...         proxy_port=8080,
    ...         no_proxy_domains=["*.acme.com", "localhost"]
    ...     )
    ... )

    >>> # Use model factory directly for advanced operations
    >>> ZoneModel = ZoneFactsFactory.get_model("acme")
    >>> zones = list(ZoneModel.query("acme"))
    >>> prod_zones = [
    ...     z for z in zones
    ...     if z.environment_type == "production"
    ... ]

Usage Patterns:
    **Environment Management**: Create and manage deployment environments per region

    **AWS Resource Organization**: Track and configure AWS resources per zone

    **Security Configuration**: Manage KMS keys, IAM roles, and security policies per zone

    **Network Isolation**: Configure VPCs, subnets, and security groups per environment

    **Proxy Management**: Configure proxy settings for environments with network restrictions

    **Multi-Account Strategy**: Support for multiple AWS accounts across environments

Table Information:
    - **Table Name**: {client}-core-automation-registry (client-specific)
    - **Hash Key**: Client (client identifier)
    - **Range Key**: Zone (zone name within client)
    - **Schema Type**: Zone registry with AWS resource metadata
    - **Billing Mode**: PAY_PER_REQUEST
    - **Client Isolation**: Each client has separate table

Zone Configuration Examples:
    ```python
    # Production zone with full AWS configuration
    production_zone = {
        "client": "acme",
        "zone": "us-east-1-prod",
        "description": "Production environment in US East with high availability",
        "region": "us-east-1",
        "environment_type": "production",
        "vpc_id": "vpc-12345678",
        "subnet_ids": ["subnet-web-1a", "subnet-web-1b", "subnet-web-1c"],
        "security_group_ids": ["sg-web-prod", "sg-app-prod", "sg-db-prod"],
        "availability_zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
        "monitoring_enabled": True,
        "backup_retention_days": 30,
        "account_facts": {
            "account_id": "123456789012",
            "account_name": "acme-production",
            "billing_contact": "billing@acme.com",
            "cost_center": "production-ops"
        },
        "region_facts": {
            "region_name": "us-east-1",
            "endpoint_url": "https://ec2.us-east-1.amazonaws.com",
            "availability_zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
            "instance_types_available": ["t3.micro", "t3.small", "t3.medium", "m5.large"]
        },
        "kms_facts": {
            "key_id": "arn:aws:kms:us-east-1:123456789012:key/abcd1234-5678-90ef-1234-567890abcdef",
            "key_alias": "alias/acme-prod-encryption",
            "encryption_context": {"Environment": "Production", "Client": "acme"},
            "key_rotation_enabled": True
        },
        "security_alias_facts": {
            "security_alias": "acme-prod-security",
            "iam_role_arn": "arn:aws:iam::123456789012:role/AcmeProdRole",
            "security_policy": "strict",
            "mfa_required": True
        }
    }

    # Development zone with basic configuration
    development_zone = {
        "client": "acme",
        "zone": "us-west-2-dev",
        "description": "Development environment in US West",
        "region": "us-west-2",
        "environment_type": "development",
        "vpc_id": "vpc-dev87654321",
        "subnet_ids": ["subnet-dev-2a", "subnet-dev-2b"],
        "security_group_ids": ["sg-dev-web", "sg-dev-app"],
        "availability_zones": ["us-west-2a", "us-west-2b"],
        "monitoring_enabled": False,
        "backup_retention_days": 7,
        "account_facts": {
            "account_id": "123456789013",
            "account_name": "acme-development",
            "billing_contact": "dev-billing@acme.com"
        },
        "region_facts": {
            "region_name": "us-west-2",
            "endpoint_url": "https://ec2.us-west-2.amazonaws.com",
            "availability_zones": ["us-west-2a", "us-west-2b"]
        }
    }

    # Staging zone with proxy configuration
    staging_zone = {
        "client": "acme",
        "zone": "eu-west-1-staging",
        "description": "Staging environment in EU West with proxy",
        "region": "eu-west-1",
        "environment_type": "staging",
        "vpc_id": "vpc-staging123",
        "subnet_ids": ["subnet-staging-1a", "subnet-staging-1b"],
        "monitoring_enabled": True,
        "backup_retention_days": 14,
        "proxy_facts": {
            "proxy_enabled": True,
            "proxy_host": "corporate-proxy.acme.com",
            "proxy_port": 8080,
            "proxy_protocol": "http",
            "no_proxy_domains": ["*.acme.com", "*.amazonaws.com", "localhost"],
            "authentication_required": True
        }
    }
    ```

Environment Type Examples:
    ```python
    # Different environment types with configurations
    environment_types = {
        "development": {
            "description": "Development and testing environment",
            "resource_limits": {"cpu": "low", "memory": "low", "storage": "standard"},
            "backup_frequency": "daily",
            "monitoring_level": "basic",
            "cost_optimization": "aggressive"
        },
        "staging": {
            "description": "Pre-production staging environment",
            "resource_limits": {"cpu": "medium", "memory": "medium", "storage": "standard"},
            "backup_frequency": "daily",
            "monitoring_level": "enhanced",
            "cost_optimization": "moderate"
        },
        "production": {
            "description": "Production environment with high availability",
            "resource_limits": {"cpu": "high", "memory": "high", "storage": "premium"},
            "backup_frequency": "continuous",
            "monitoring_level": "comprehensive",
            "cost_optimization": "performance"
        },
        "disaster_recovery": {
            "description": "Disaster recovery environment",
            "resource_limits": {"cpu": "medium", "memory": "medium", "storage": "premium"},
            "backup_frequency": "continuous",
            "monitoring_level": "comprehensive",
            "cost_optimization": "availability"
        }
    }
    ```

AWS Resource Models:
    **AccountFacts**: AWS account configuration and billing information
    ```python
    account = AccountFacts(
        account_id="123456789012",
        account_name="acme-production",
        billing_contact="billing@acme.com",
        cost_center="production-ops",
        organization_unit="production"
    )
    ```

    **RegionFacts**: AWS region configuration and capabilities
    ```python
    region = RegionFacts(
        region_name="us-east-1",
        endpoint_url="https://ec2.us-east-1.amazonaws.com",
        availability_zones=["us-east-1a", "us-east-1b", "us-east-1c"],
        instance_types_available=["t3.micro", "m5.large", "c5.xlarge"],
        services_available=["EC2", "RDS", "S3", "Lambda"]
    )
    ```

    **KmsFacts**: KMS encryption key management
    ```python
    kms = KmsFacts(
        key_id="arn:aws:kms:us-east-1:123456789012:key/abcd1234-5678-90ef-1234-567890abcdef",
        key_alias="alias/acme-prod-encryption",
        encryption_context={"Environment": "Production", "Client": "acme"},
        key_rotation_enabled=True,
        key_usage="ENCRYPT_DECRYPT"
    )
    ```

    **SecurityAliasFacts**: Security configuration and IAM roles
    ```python
    security = SecurityAliasFacts(
        security_alias="acme-prod-security",
        iam_role_arn="arn:aws:iam::123456789012:role/AcmeProdRole",
        security_policy="strict",
        mfa_required=True,
        session_duration=3600
    )
    ```

    **ProxyFacts**: Proxy and network configuration
    ```python
    proxy = ProxyFacts(
        proxy_enabled=True,
        proxy_host="corporate-proxy.acme.com",
        proxy_port=8080,
        proxy_protocol="http",
        no_proxy_domains=["*.acme.com", "localhost"],
        authentication_required=True
    )
    ```

Integration Points:
    - **Application Deployment**: Zones provide target environments for application deployment
    - **AWS Resource Management**: Integration with AWS APIs for resource provisioning
    - **Security Management**: Integration with IAM and security policies
    - **Cost Management**: Integration with AWS billing and cost optimization
    - **Network Management**: Integration with VPC and networking configurations
    - **Monitoring Systems**: Integration with CloudWatch and monitoring tools

Related Modules:
    - core_db.registry: Base registry system and common functionality
    - core_db.registry.actions: Base RegistryAction class with shared methods
    - core_db.registry.portfolio: Portfolio registry containing zones
    - core_deploy: Deployment automation targeting specific zones
    - core_aws: AWS resource management and provisioning

Error Handling:
    All operations may raise:
    - BadRequestException: Invalid parameters or missing required fields
    - ConflictException: Zone already exists (create operations)
    - NotFoundException: Zone not found (get/update/delete operations)
    - UnknownException: Database connection issues or unexpected errors

Best Practices:
    - **Environment Separation**: Use separate zones for different environments
    - **Resource Tagging**: Consistently tag AWS resources with zone information
    - **Security Isolation**: Implement proper security boundaries between zones
    - **Network Design**: Plan VPC and subnet architecture for zone isolation
    - **Cost Management**: Monitor and optimize costs per zone
    - **Backup Strategy**: Implement appropriate backup retention per environment type

Operational Considerations:
    - **Zone Lifecycle**: Plan for zone creation, configuration, and retirement
    - **Resource Provisioning**: Automate AWS resource creation based on zone configuration
    - **Security Compliance**: Ensure zones meet security and compliance requirements
    - **Disaster Recovery**: Configure appropriate DR zones for production environments
    - **Cost Monitoring**: Track resource usage and costs per zone
    - **Access Control**: Implement proper RBAC for zone management

Note:
    Zone registry provides the foundation for AWS resource organization and deployment
    environment management. Proper zone design and configuration is crucial for secure,
    scalable, and cost-effective multi-environment operations.
"""

from .models import ZoneFact, ZoneFactsFactory, ZoneFactsModel
from .actions import ZoneActions

__all__ = ["ZoneFact", "ZoneActions", "ZoneFactsFactory", "ZoneFactsModel"]
