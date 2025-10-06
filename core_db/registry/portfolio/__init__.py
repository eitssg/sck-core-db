"""Portfolio Registry module for the core-automation-registry DynamoDB table.

This module provides comprehensive portfolio management for the registry system, combining
both data models and action classes to enable complete CRUD operations for portfolio FACTS
records with proper client-portfolio hierarchy and organizational metadata management.

Key Components:
    - **PortfolioActions**: CRUD operations for portfolio registry management
    - **PortfolioFactsModel**: PynamoDB model for DynamoDB portfolio registry operations
    - **PortfolioFactsFactory**: Factory for creating client-specific model instances
    - **ContactFacts**: Contact information data model for portfolios
    - **ApproverFacts**: Approval workflow data model for portfolios
    - **OwnerFacts**: Ownership and responsibility data model for portfolios
    - **ProjectFacts**: Project metadata data model for portfolios

Features:
    - **Portfolio Lifecycle Management**: Complete CRUD operations for portfolio entities
    - **Client-Portfolio Hierarchy**: Proper hierarchical organization within client namespaces
    - **Organizational Structure**: Support for contacts, approvers, owners, and projects
    - **Flexible Parameter Handling**: Supports various portfolio identifier formats
    - **Client Isolation**: Factory pattern ensures proper table isolation between clients

Portfolio Structure:
    Portfolios are stored with a composite key structure in client-specific tables:
    - **Hash Key**: client (client identifier for data partitioning)
    - **Range Key**: portfolio (portfolio name within client namespace)
    - **Attributes**: Portfolio-specific metadata, contacts, and project information

Schema Structure:
    The portfolio registry schema includes:
    - **Client**: Hash key (client identifier)
    - **Portfolio**: Range key (portfolio name within client)
    - **description**: Human-readable portfolio description
    - **contact_email**: Primary contact email for the portfolio
    - **environment_strategy**: Deployment strategy (blue-green, rolling, canary)
    - **deployment_regions**: List of AWS regions for deployment
    - **budget_allocation**: Budget limits and tracking per environment
    - **compliance_requirements**: Required compliance standards
    - **contacts**: ContactFacts for team member information
    - **approvers**: ApproverFacts for approval workflow management
    - **owners**: OwnerFacts for ownership and responsibility tracking
    - **projects**: ProjectFacts for project metadata and tracking

Examples:
    >>> from core_db.registry.portfolio import (
    ...     PortfolioActions, PortfolioFactsModel, PortfolioFactsFactory,
    ...     ContactFacts, ApproverFacts, OwnerFacts, ProjectFacts
    ... )

    >>> # Create a new portfolio with organizational structure
    >>> result = PortfolioActions.create(
    ...     client="acme",
    ...     portfolio="web-services",
    ...     description="Web-based applications and APIs",
    ...     contact_email="webteam@acme.com",
    ...     environment_strategy="blue-green",
    ...     deployment_regions=["us-east-1", "us-west-2"],
    ...     budget_allocation={
    ...         "development": {"monthly_limit": 1000},
    ...         "staging": {"monthly_limit": 2000},
    ...         "production": {"monthly_limit": 10000}
    ...     },
    ...     contacts=[
    ...         ContactFacts(name="Alice Johnson", email="alice@acme.com", role="tech_lead"),
    ...         ContactFacts(name="Bob Smith", email="bob@acme.com", role="product_owner")
    ...     ],
    ...     approvers=[
    ...         ApproverFacts(name="Carol Davis", email="carol@acme.com", level="manager"),
    ...         ApproverFacts(name="David Wilson", email="david@acme.com", level="director")
    ...     ]
    ... )

    >>> # List all portfolios for a client
    >>> portfolios = PortfolioActions.list(client="acme")
    >>> for portfolio in portfolios.data:
    ...     print(f"Portfolio: {portfolio['Portfolio']}")
    ...     print(f"Description: {portfolio.get('description')}")
    ...     print(f"Strategy: {portfolio.get('environment_strategy')}")

    >>> # Get specific portfolio with full metadata
    >>> portfolio = PortfolioActions.get(client="acme", portfolio="web-services")
    >>> if portfolio.data:
    ...     print(f"Contact: {portfolio.data.get('contact_email')}")
    ...     print(f"Regions: {portfolio.data.get('deployment_regions', [])}")
    ...     print(f"Budget: {portfolio.data.get('budget_allocation', {})}")

    >>> # Update portfolio with new organizational information
    >>> result = PortfolioActions.patch(
    ...     client="acme",
    ...     portfolio="web-services",
    ...     environment_strategy="canary",
    ...     owners=[
    ...         OwnerFacts(name="Eve Martinez", email="eve@acme.com", responsibility="technical"),
    ...         OwnerFacts(name="Frank Brown", email="frank@acme.com", responsibility="business")
    ...     ],
    ...     projects=[
    ...         ProjectFacts(name="API Gateway", status="active", priority="high"),
    ...         ProjectFacts(name="Service Mesh", status="planning", priority="medium")
    ...     ]
    ... )

    >>> # Use model factory directly for advanced operations
    >>> PortfolioModel = PortfolioFactsFactory.get_model("acme")
    >>> portfolios = list(PortfolioModel.query("acme"))
    >>> web_portfolios = [
    ...     p for p in portfolios
    ...     if "web" in p.description.lower()
    ... ]

Usage Patterns:
    **Portfolio Organization**: Create hierarchical structure within client namespaces

    **Team Management**: Track contacts, approvers, and owners for each portfolio

    **Project Tracking**: Associate projects with portfolios for better organization

    **Environment Management**: Configure deployment strategies per portfolio

    **Budget Control**: Set and track budget limits across different environments

    **Compliance Tracking**: Maintain compliance requirements per portfolio

Table Information:
    - **Table Name**: {client}-core-automation-registry (client-specific)
    - **Hash Key**: Client (client identifier)
    - **Range Key**: Portfolio (portfolio name within client)
    - **Schema Type**: Portfolio registry with organizational metadata
    - **Billing Mode**: PAY_PER_REQUEST
    - **Client Isolation**: Each client has separate table

Portfolio Configuration Examples:
    ```python
    # Web services portfolio
    web_portfolio = {
        "client": "acme",
        "portfolio": "web-services",
        "description": "Web applications and REST APIs",
        "contact_email": "web-team@acme.com",
        "environment_strategy": "blue-green",
        "deployment_regions": ["us-east-1", "us-west-2"],
        "budget_allocation": {
            "development": {"monthly_limit": 1000, "alerts_at": 800},
            "staging": {"monthly_limit": 2000, "alerts_at": 1600},
            "production": {"monthly_limit": 10000, "alerts_at": 8000}
        },
        "compliance_requirements": ["SOC2", "PCI-DSS"],
        "contacts": [
            {"name": "Alice Johnson", "email": "alice@acme.com", "role": "tech_lead"},
            {"name": "Bob Smith", "email": "bob@acme.com", "role": "product_owner"}
        ],
        "approvers": [
            {"name": "Carol Davis", "email": "carol@acme.com", "level": "manager"},
            {"name": "David Wilson", "email": "david@acme.com", "level": "director"}
        ],
        "owners": [
            {"name": "Eve Martinez", "email": "eve@acme.com", "responsibility": "technical"},
            {"name": "Frank Brown", "email": "frank@acme.com", "responsibility": "business"}
        ],
        "projects": [
            {"name": "API Gateway", "status": "active", "priority": "high"},
            {"name": "User Authentication", "status": "completed", "priority": "high"},
            {"name": "Rate Limiting", "status": "planning", "priority": "medium"}
        ]
    }

    # Mobile services portfolio
    mobile_portfolio = {
        "client": "acme",
        "portfolio": "mobile-apps",
        "description": "Mobile applications and backend services",
        "contact_email": "mobile-team@acme.com",
        "environment_strategy": "rolling",
        "deployment_regions": ["us-east-1", "eu-west-1", "ap-southeast-1"],
        "budget_allocation": {
            "development": {"monthly_limit": 800},
            "staging": {"monthly_limit": 1500},
            "production": {"monthly_limit": 8000}
        },
        "compliance_requirements": ["GDPR", "COPPA"],
        "contacts": [
            {"name": "Grace Lee", "email": "grace@acme.com", "role": "mobile_lead"},
            {"name": "Henry Kim", "email": "henry@acme.com", "role": "ux_designer"}
        ],
        "projects": [
            {"name": "iOS App v2.0", "status": "active", "priority": "high"},
            {"name": "Android App v2.0", "status": "active", "priority": "high"},
            {"name": "Push Notifications", "status": "completed", "priority": "medium"}
        ]
    }

    # Data services portfolio
    data_portfolio = {
        "client": "acme",
        "portfolio": "data-platform",
        "description": "Data processing, analytics, and ML services",
        "contact_email": "data-team@acme.com",
        "environment_strategy": "canary",
        "deployment_regions": ["us-east-1", "us-west-2"],
        "budget_allocation": {
            "development": {"monthly_limit": 2000},
            "staging": {"monthly_limit": 5000},
            "production": {"monthly_limit": 20000}
        },
        "compliance_requirements": ["SOC2", "HIPAA", "GDPR"],
        "contacts": [
            {"name": "Iris Chen", "email": "iris@acme.com", "role": "data_engineer"},
            {"name": "Jack Taylor", "email": "jack@acme.com", "role": "ml_engineer"}
        ],
        "projects": [
            {"name": "Data Lake Migration", "status": "active", "priority": "critical"},
            {"name": "ML Model Pipeline", "status": "planning", "priority": "high"},
            {"name": "Real-time Analytics", "status": "research", "priority": "medium"}
        ]
    }
    ```

Environment Strategy Examples:
    ```python
    # Different deployment strategies
    environment_strategies = {
        "blue-green": {
            "description": "Switch between two identical environments",
            "rollback_time": "immediate",
            "risk_level": "low",
            "suitable_for": ["web_apps", "apis", "services"]
        },
        "rolling": {
            "description": "Gradual replacement of instances",
            "rollback_time": "moderate",
            "risk_level": "medium",
            "suitable_for": ["microservices", "stateless_apps"]
        },
        "canary": {
            "description": "Gradual traffic shift to new version",
            "rollback_time": "fast",
            "risk_level": "very_low",
            "suitable_for": ["critical_services", "high_traffic_apps"]
        },
        "feature_toggle": {
            "description": "Feature flags for gradual rollout",
            "rollback_time": "immediate",
            "risk_level": "very_low",
            "suitable_for": ["feature_rollouts", "a_b_testing"]
        }
    }
    ```

Organizational Models:
    **ContactFacts**: Team member contact information
    ```python
    contact = ContactFacts(
        name="Alice Johnson",
        email="alice@acme.com",
        role="tech_lead",
        phone="+1-555-0123",
        timezone="America/New_York"
    )
    ```

    **ApproverFacts**: Approval workflow participants
    ```python
    approver = ApproverFacts(
        name="Carol Davis",
        email="carol@acme.com",
        level="manager",
        department="engineering",
        approval_threshold=5000
    )
    ```

    **OwnerFacts**: Portfolio ownership and responsibility
    ```python
    owner = OwnerFacts(
        name="Eve Martinez",
        email="eve@acme.com",
        responsibility="technical",
        backup_contact="frank@acme.com",
        escalation_level=2
    )
    ```

    **ProjectFacts**: Project tracking within portfolios
    ```python
    project = ProjectFacts(
        name="API Gateway",
        status="active",
        priority="high",
        start_date="2024-01-15",
        target_completion="2024-06-30",
        budget_allocated=50000
    )
    ```

Integration Points:
    - **Application Registry**: Portfolios contain applications for deployment
    - **Budget Management**: Integration with cost tracking and billing systems
    - **Approval Workflows**: Integration with change management systems
    - **Project Management**: Integration with project tracking tools
    - **Team Management**: Integration with HR and identity systems
    - **Compliance Systems**: Integration with audit and compliance tools

Related Modules:
    - core_db.registry: Base registry system and common functionality
    - core_db.registry.actions: Base RegistryAction class with shared methods
    - core_db.registry.app: Application registry within portfolios
    - core_deploy: Deployment automation consuming portfolio strategies
    - core_budget: Budget tracking and management integration

Error Handling:
    All operations may raise:
    - BadRequestException: Invalid parameters or missing required fields
    - ConflictException: Portfolio already exists (create operations)
    - NotFoundException: Portfolio not found (get/update/delete operations)
    - UnknownException: Database connection issues or unexpected errors

Best Practices:
    - **Logical Grouping**: Group related applications and services in portfolios
    - **Clear Ownership**: Define clear technical and business ownership
    - **Budget Planning**: Set realistic budget limits with appropriate alerts
    - **Strategy Selection**: Choose deployment strategies based on risk tolerance
    - **Team Structure**: Maintain current contact and approval information
    - **Project Tracking**: Keep project status updated for visibility

Operational Considerations:
    - **Portfolio Lifecycle**: Plan for portfolio creation, evolution, and retirement
    - **Resource Management**: Monitor resource usage across portfolio environments
    - **Access Control**: Implement proper RBAC for portfolio management
    - **Audit Trails**: Track changes to portfolio configurations
    - **Disaster Recovery**: Ensure portfolio configurations are backed up

Note:
    Portfolio registry provides the organizational structure for application deployment
    and management. Proper portfolio design and maintenance is crucial for effective
    multi-tenant operations and team collaboration.
"""

from .models import (
    PortfolioFact,
    PortfolioFactsFactory,
    PortfolioFactsModel,
    ContactFacts,
    ApproverFacts,
    OwnerFacts,
    ProjectFacts,
    ContactFactsItem,
    ApproverFactsItem,
    OwnerFactsItem,
    ProjectFactsItem,
)
from .actions import PortfolioActions

__all__ = [
    "PortfolioFact",
    "PortfolioActions",
    "PortfolioFactsFactory",
    "PortfolioFactsModel",
    "ContactFacts",
    "ApproverFacts",
    "OwnerFacts",
    "ProjectFacts",
    "ContactFactsItem",
    "ApproverFactsItem",
    "OwnerFactsItem",
    "ProjectFactsItem",
]
