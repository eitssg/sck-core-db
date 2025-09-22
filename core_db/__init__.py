"""Core Database Module for Simple Cloud Kit.

This module provides comprehensive database abstraction and registry management for the
Simple Cloud Kit automation framework. It includes DynamoDB operations, registry systems
for deployment automation, and data models for multi-tenant cloud environments.

The core_db module serves as the central data layer for:
    - **Registry Management**: Client, portfolio, zone, and application metadata
    - **Database Operations**: DynamoDB CRUD operations with proper error handling
    - **Multi-Tenant Support**: Client-specific table isolation and data separation
    - **Deployment Automation**: Metadata storage for automated deployment pipelines
    - **AWS Integration**: Native support for AWS resources and configurations

Key Components:
    - **registry**: Complete FACTS (Functional And Configuration Tracking System) registry
    - **response**: Standardized response objects for API operations
    - **exceptions**: Custom exception classes for database operations
    - **constants**: Database constants and configuration values

Architecture Overview:
    ```
    core_db/
    ├── registry/           # Registry system for deployment metadata
    │   ├── client/         # Client-level organization and isolation
    │   ├── portfolio/      # Portfolio-level project management
    │   ├── zone/           # Environment and AWS resource configuration
    │   └── app/            # Application deployment metadata
    ├── response.py         # Standardized response objects
    ├── exceptions.py       # Custom database exceptions
    └── constants.py        # Database constants and keys
    ```

Registry System:
    The registry implements a four-tier hierarchy for deployment automation:

    **Client → Portfolio → Zone → Application**

    - **Client**: Top-level organization with billing and access isolation
    - **Portfolio**: Project-level grouping of related applications
    - **Zone**: Environment-specific AWS resource configuration
    - **Application**: Individual service deployment metadata

Examples:
    >>> import core_db
    >>> print(f"Core DB Version: {core_db.__version__}")

    >>> # Registry system usage
    >>> from core_db.registry import ClientActions, PortfolioActions, ZoneActions, AppActions

    >>> # Create deployment hierarchy
    >>> client = ClientActions.create(
    ...     client="acme",
    ...     description="ACME Corporation",
    ...     contact_email="admin@acme.com"
    ... )

    >>> portfolio = PortfolioActions.create(
    ...     client="acme",
    ...     portfolio="web-services",
    ...     description="Web applications and APIs"
    ... )

    >>> zone = ZoneActions.create(
    ...     client="acme",
    ...     zone="us-east-1-prod",
    ...     description="Production environment",
    ...     region="us-east-1"
    ... )

    >>> app = AppActions.create(
    ...     client="acme",
    ...     app="api-gateway",
    ...     description="Main API gateway",
    ...     portfolio="web-services"
    ... )


Module Features:
    **Registry Management**:
    - Complete CRUD operations for all registry entities
    - Hierarchical organization with proper data relationships
    - Multi-tenant isolation with client-specific tables
    - Factory pattern for dynamic model creation
    - Comprehensive metadata storage for automation

    **Database Operations**:
    - DynamoDB abstraction with PynamoDB models
    - Standardized response objects for consistency
    - Custom exception handling for database errors
    - Connection management and error recovery
    - Atomic operations for data consistency

    **Multi-Tenant Support**:
    - Client-specific table isolation
    - Data separation and access control
    - Billing and resource tracking per client
    - Scalable architecture for enterprise use
    - Secure data handling and privacy

    **AWS Integration**:
    - Native AWS resource configuration
    - VPC, subnet, and security group management
    - KMS encryption and security policies
    - IAM role and policy management
    - Cost tracking and optimization

Registry Entity Examples:
    ```python
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
    ```

    **NoContentResponse**: Successful operation without data
    ```python
    response = NoContentResponse(
        data={"message": "Entity not found"},
        message="No content available"
    )
    ```

Exception Types:
    **BadRequestException**: Invalid request parameters
    ```python
    raise BadRequestException("Client name is required")
    ```

    **ConflictException**: Entity already exists
    ```python
    raise ConflictException("Client already exists: acme")
    ```

    **NotFoundException**: Entity not found
    ```python
    raise NotFoundException("Client not found: acme")
    ```

    **UnknownException**: Unexpected database errors
    ```python
    raise UnknownException("Database connection failed")
    ```

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
