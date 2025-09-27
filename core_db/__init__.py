"""Core Database Module for Simple Cloud Kit.

This module provides database abstraction and registry management for deployment automation.
It includes DynamoDB operations, multi-tenant support, and data models for cloud environments.

Key Components:
    - **item**: Deployment hierarchy management (portfolios, apps, branches, builds, components)
    - **event**: Audit trail and deployment activity tracking
    - **registry**: FACTS (Functional And Configuration Tracking System) registry
    - **response**: Standardized response objects for API operations
    - **exceptions**: Custom exception classes for database operations

Architecture Overview::

    Client → Portfolio → Zone → Application

    Multi-tenant DynamoDB tables with client-specific namespaces for isolation.

Example:
    >>> import core_db
    >>> from core_db.item import ItemActions
    >>>
    >>> # Create deployment item
    >>> portfolio = ItemActions.create_portfolio(
    ...     client="acme",
    ...     portfolio="web-services",
    ...     description="Web applications and APIs"
    ... )
    - VPC, subnet, and security group management
    - KMS encryption and security policies
    - IAM role and policy management
    - Cost tracking and optimization

Registry Entity Examples::

    # Client entity
    client_data = {
        "client": "acme",
        "description": "ACME Corporation",
        "contact_email": "admin@acme.com",
        "organization_type": "enterprise"
    }

    # Portfolio entity
    portfolio_data = {
        "client": "acme",
        "portfolio": "web-services",
        "description": "Web applications and APIs",
        "environment_strategy": "blue-green",
        "budget_allocation": {"prod": 10000, "staging": 2000}
    }

    # Zone entity
    zone_data = {
        "client": "acme",
        "zone": "us-east-1-prod",
        "description": "Production environment",
        "region": "us-east-1",
        "vpc_id": "vpc-12345678",
        "environment_type": "production"
    }

    # Application entity
    app_data = {
        "client": "acme",
        "app": "api-gateway",
        "description": "Main API gateway",
        "app_type": "service",
        "portfolio": "web-services",
        "deployment_zones": ["us-east-1-prod"]
    }

    **NoContentResponse**: Successful operation without data::

        response = NoContentResponse(
            data={"message": "Entity not found"},
            message="No content available"
        )

Exception Types:
    **BadRequestException**: Invalid request parameters::

        raise BadRequestException("Client name is required")

    **ConflictException**: Entity already exists::

        raise ConflictException("Client already exists: acme")

    **NotFoundException**: Entity not found::

        raise NotFoundException("Client not found: acme")

    **UnknownException**: Unexpected database errors::

        raise UnknownException("Database connection failed")

Integration Points:
    - **Deployment Automation**: Registry provides metadata for automated deployments
    - **CI/CD Pipelines**: Integration with deployment pipeline configuration
    - **Infrastructure as Code**: Generate IaC templates from registry data
    - **Cost Management**: Track resource usage and billing across hierarchy
    - **Security Policies**: Apply security rules based on registry metadata
    - **Monitoring Systems**: Configure monitoring from registry configuration

Related Modules:
    - core_framework: Core framework components and utilities
    - core_execute: Execution engine for deployment automation
    - core_deploy: Deployment automation consuming registry metadata
    - core_aws: AWS resource management and provisioning
    - core_api: API layer for registry and deployment operations

Best Practices:
    - **Hierarchical Design**: Follow client→portfolio→zone→app structure
    - **Data Consistency**: Maintain referential integrity across entities
    - **Error Handling**: Use proper exception handling for all operations
    - **Client Isolation**: Ensure proper data separation between clients
    - **Metadata Completeness**: Provide comprehensive data for automation

Operational Considerations:
    - **Scalability**: Design for enterprise-scale multi-tenant usage
    - **Performance**: Optimize database queries and connection usage
    - **Security**: Implement proper access control and data encryption
    - **Backup Strategy**: Ensure registry data is properly backed up
    - **Migration Planning**: Plan for schema evolution and data migration
    - **Monitoring**: Track database performance and error rates

Version Information:
    Current version includes:
    - Registry system with four-tier hierarchy
    - Multi-tenant client isolation
    - Comprehensive CRUD operations
    - AWS resource integration
    - Standardized response handling
    - Custom exception management

Note:
    The core_db module serves as the foundation for all database operations
    in the Simple Cloud Kit. Proper understanding and usage of the registry
    system is crucial for effective deployment automation and multi-tenant
    cloud operations.
"""

__version__ = "0.1.2-pre.19+2ae5778"
