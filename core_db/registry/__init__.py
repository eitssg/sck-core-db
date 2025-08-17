"""Registry System for Core Automation DynamoDB Tables.

This module provides a comprehensive registry system for managing deployment automation
metadata across clients, portfolios, zones, and applications. The registry maintains
FACTS (Functional And Configuration Tracking System) records that enable hierarchical
organization and deployment automation across multi-tenant cloud environments.

The registry system implements a four-tier hierarchy:
    Client → Portfolio → Zone → Application

Key Components:
    - **ClientActions & ClientFactsModel**: Top-level client organization and isolation
    - **PortfolioActions & PortfolioFactsModel**: Portfolio-level project organization
    - **ZoneActions & ZoneFactsModel**: Environment and AWS resource configuration
    - **AppActions & AppFactsModel**: Application deployment metadata and configuration
    - **Factory Classes**: Client-specific model factories for table isolation

Architecture Features:
    - **Hierarchical Organization**: Four-tier client-portfolio-zone-app structure
    - **Multi-Tenant Isolation**: Client-specific DynamoDB tables for data separation
    - **CRUD Operations**: Complete lifecycle management for all registry entities
    - **Factory Pattern**: Dynamic model creation for client-specific table access
    - **Flexible Schema**: Extensible metadata storage for deployment automation
    - **AWS Integration**: Native support for AWS resources and deployment patterns

Registry Hierarchy:
    ```
    Client (acme)
    ├── Portfolio (web-services)
    │   ├── Zone (us-east-1-prod)
    │   │   ├── App (api-gateway)
    │   │   ├── App (user-service)
    │   │   └── App (payment-service)
    │   └── Zone (us-west-2-staging)
    │       ├── App (api-gateway)
    │       └── App (user-service)
    └── Portfolio (mobile-apps)
        ├── Zone (us-east-1-prod)
        │   ├── App (ios-app)
        │   └── App (android-app)
        └── Zone (eu-west-1-prod)
            ├── App (ios-app)
            └── App (android-app)
    ```

Table Structure:
    Each client maintains separate DynamoDB tables:
    - **Table Name**: {client}-core-automation-registry
    - **Hash Key**: Client identifier (partition key)
    - **Range Key**: Entity identifier (portfolio, zone, or app name)
    - **Billing Mode**: PAY_PER_REQUEST for cost optimization
    - **Client Isolation**: Complete data separation between clients

Examples:
    >>> from core_db.registry import (
    ...     ClientActions, PortfolioActions, ZoneActions, AppActions,
    ...     ClientFactsModel, PortfolioFactsModel, ZoneFactsModel, AppFactsModel
    ... )

    >>> # Create client organization
    >>> client_result = ClientActions.create(
    ...     client="acme",
    ...     description="ACME Corporation deployment automation",
    ...     contact_email="devops@acme.com",
    ...     organization_type="enterprise"
    ... )

    >>> # Create portfolio within client
    >>> portfolio_result = PortfolioActions.create(
    ...     client="acme",
    ...     portfolio="web-services",
    ...     description="Web-based applications and APIs",
    ...     contact_email="webteam@acme.com",
    ...     environment_strategy="blue-green"
    ... )

    >>> # Create deployment zone
    >>> zone_result = ZoneActions.create(
    ...     client="acme",
    ...     zone="us-east-1-prod",
    ...     description="Production environment in US East",
    ...     region="us-east-1",
    ...     environment_type="production",
    ...     vpc_id="vpc-12345678"
    ... )

    >>> # Create application
    >>> app_result = AppActions.create(
    ...     client="acme",
    ...     app="api-gateway",
    ...     description="Main API gateway service",
    ...     app_type="service",
    ...     portfolio="web-services",
    ...     deployment_zones=["us-east-1-prod", "us-west-2-staging"]
    ... )

    >>> # List all entities for a client
    >>> clients = ClientActions.list()
    >>> portfolios = PortfolioActions.list(client="acme")
    >>> zones = ZoneActions.list(client="acme")
    >>> apps = AppActions.list(client="acme")

Usage Patterns:
    **Client Management**: Top-level organization and billing isolation

    **Portfolio Organization**: Group related applications and services

    **Zone Configuration**: Environment-specific AWS resource management

    **Application Deployment**: Individual service deployment metadata

    **Cross-Entity Queries**: Navigate hierarchy for deployment automation

Registry Operations:
    **Create Operations**:
    ```python
    # Create complete deployment hierarchy
    ClientActions.create(client="acme", description="ACME Corp")
    PortfolioActions.create(client="acme", portfolio="web", description="Web services")
    ZoneActions.create(client="acme", zone="prod", region="us-east-1")
    AppActions.create(client="acme", app="api", portfolio="web", zones=["prod"])
    ```

    **Query Operations**:
    ```python
    # List entities at each level
    all_clients = ClientActions.list()
    client_portfolios = PortfolioActions.list(client="acme")
    client_zones = ZoneActions.list(client="acme")
    client_apps = AppActions.list(client="acme")

    # Get specific entities
    client = ClientActions.get(client="acme")
    portfolio = PortfolioActions.get(client="acme", portfolio="web")
    zone = ZoneActions.get(client="acme", zone="prod")
    app = AppActions.get(client="acme", app="api")
    ```

    **Update Operations**:
    ```python
    # Partial updates (PATCH semantics)
    ClientActions.patch(client="acme", contact_email="new@acme.com")
    PortfolioActions.patch(client="acme", portfolio="web", strategy="canary")
    ZoneActions.patch(client="acme", zone="prod", monitoring_enabled=True)
    AppActions.patch(client="acme", app="api", replicas=3)

    # Complete replacement (PUT semantics)
    ClientActions.update(client="acme", description="Updated ACME Corp")
    ```

Factory Pattern Usage:
    ```python
    # Get client-specific models for advanced operations
    from core_db.registry import (
    ...     ClientFactsFactory, PortfolioFactsFactory,
    ...     ZoneFactsFactory, AppFactsFactory
    ... )

    # Client-specific model instances
    ClientModel = ClientFactsFactory.get_model("acme")
    PortfolioModel = PortfolioFactsFactory.get_model("acme")
    ZoneModel = ZoneFactsFactory.get_model("acme")
    AppModel = AppFactsFactory.get_model("acme")

    # Direct DynamoDB operations
    portfolios = list(PortfolioModel.query("acme"))
    zones = list(ZoneModel.query("acme"))
    apps = list(AppModel.query("acme"))
    ```

Data Models:
    **ClientFact**: Top-level client organization metadata
    ```python
    client_data = {
        "client": "acme",
        "description": "ACME Corporation",
        "contact_email": "admin@acme.com",
        "organization_type": "enterprise",
        "billing_contact": "billing@acme.com"
    }
    ```

    **PortfolioFact**: Portfolio-level project organization
    ```python
    portfolio_data = {
        "client": "acme",
        "portfolio": "web-services",
        "description": "Web applications and APIs",
        "contact_email": "webteam@acme.com",
        "environment_strategy": "blue-green",
        "budget_allocation": {"prod": 10000, "staging": 2000}
    }
    ```

    **ZoneFact**: Environment and AWS resource configuration
    ```python
    zone_data = {
        "client": "acme",
        "zone": "us-east-1-prod",
        "description": "Production environment",
        "region": "us-east-1",
        "environment_type": "production",
        "vpc_id": "vpc-12345678",
        "subnet_ids": ["subnet-abc123", "subnet-def456"]
    }
    ```

    **AppFact**: Application deployment metadata
    ```python
    app_data = {
        "client": "acme",
        "app": "api-gateway",
        "description": "Main API gateway",
        "app_type": "service",
        "portfolio": "web-services",
        "deployment_zones": ["us-east-1-prod", "us-west-2-staging"],
        "container_config": {"image": "api:latest", "port": 8080}
    }
    ```

Integration Points:
    - **Deployment Automation**: Registry provides metadata for automated deployments
    - **Cost Management**: Track resource usage and billing across hierarchy
    - **Security Policies**: Apply security rules based on registry metadata
    - **Monitoring Systems**: Configure monitoring based on registry configuration
    - **CI/CD Pipelines**: Use registry data for deployment target configuration
    - **Infrastructure as Code**: Generate IaC templates from registry metadata

Related Modules:
    - core_db.registry.client: Client-level organization and isolation
    - core_db.registry.portfolio: Portfolio-level project management
    - core_db.registry.zone: Environment and AWS resource configuration
    - core_db.registry.app: Application deployment metadata management
    - core_deploy: Deployment automation consuming registry metadata
    - core_aws: AWS resource management integration

Error Handling:
    All registry operations may raise:
    - BadRequestException: Invalid parameters or missing required fields
    - ConflictException: Entity already exists (create operations)
    - NotFoundException: Entity not found (get/update/delete operations)
    - UnknownException: Database connection issues or unexpected errors

Best Practices:
    - **Hierarchical Design**: Follow client→portfolio→zone→app hierarchy
    - **Naming Conventions**: Use consistent naming across all registry entities
    - **Metadata Completeness**: Provide comprehensive metadata for automation
    - **Client Isolation**: Ensure proper data separation between clients
    - **Portfolio Organization**: Group related applications logically
    - **Environment Strategy**: Plan deployment strategies per portfolio
    - **Zone Configuration**: Configure environments for proper isolation

Operational Considerations:
    - **Registry Lifecycle**: Plan for entity creation, updates, and retirement
    - **Data Consistency**: Maintain referential integrity across hierarchy
    - **Access Control**: Implement proper RBAC for registry management
    - **Backup Strategy**: Ensure registry data is properly backed up
    - **Migration Planning**: Plan for registry schema evolution
    - **Performance Optimization**: Monitor query patterns and optimize access

Note:
    The registry system serves as the foundation for deployment automation and
    multi-tenant cloud operations. Proper registry design and maintenance is
    crucial for effective automated deployment and resource management.
"""

from .client.models import ClientFactsModel, ClientFact
from .client.actions import ClientActions

from .zone.models import ZoneFactsModel, ZoneFact
from .zone.actions import ZoneActions

from .portfolio.models import PortfolioFactsModel, PortfolioFact
from .portfolio.actions import PortfolioActions

from .app.models import AppFactsModel, AppFact
from .app.actions import AppActions

# Import factory classes for completeness
try:
    from .client.models import ClientFactsFactory
except ImportError:
    ClientFactsFactory = None

try:
    from .zone.models import ZoneFactsFactory
except ImportError:
    ZoneFactsFactory = None

try:
    from .portfolio.models import PortfolioFactsFactory
except ImportError:
    PortfolioFactsFactory = None

try:
    from .app.models import AppFactsFactory
except ImportError:
    AppFactsFactory = None

__all__ = [
    # Fact/Model classes
    "ClientFact",
    "ZoneFact",
    "PortfolioFact",
    "AppFact",
    # Action classes
    "ClientActions",
    "ZoneActions",
    "PortfolioActions",
    "AppActions",
    # Model classes
    "ClientFactsModel",
    "ZoneFactsModel",
    "PortfolioFactsModel",
    "AppFactsModel",
    # Factory classes (if available)
    "ClientFactsFactory",
    "ZoneFactsFactory",
    "PortfolioFactsFactory",
    "AppFactsFactory",
]
