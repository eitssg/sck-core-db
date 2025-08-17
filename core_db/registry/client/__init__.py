"""Client Registry module for the core-automation-registry DynamoDB table.

This module provides comprehensive client management for the registry system, combining
both data models and action classes to enable complete CRUD operations for client FACTS
records with proper global table access and organizational metadata management.

Key Components:
    - **ClientActions**: CRUD operations for client registry management
    - **ClientFactsModel**: PynamoDB model for DynamoDB client registry operations
    - **ClientFactsFactory**: Factory for creating client-specific model instances

Features:
    - **Client FACTS Management**: Complete client lifecycle with organizational metadata
    - **Global Table Operations**: Uses global registry table for system-wide client access
    - **Client Isolation**: Proper tenant separation and data isolation
    - **Organizational Metadata**: Store complete client organizational information
    - **Billing and Feature Management**: Track billing tiers and enabled features

Client Structure:
    Clients are stored in the global registry table with:
    - **Hash Key**: client (primary client identifier)
    - **Attributes**: Complete organizational and configuration metadata

Schema Structure:
    The client registry schema includes:
    - **Client**: Primary identifier (hash key)
    - **organization**: Organization name for the client
    - **contact_email**: Primary contact email address
    - **billing_tier**: Billing tier (standard, premium, enterprise)
    - **regions**: List of enabled AWS regions
    - **features**: Dictionary of enabled features and configurations
    - **metadata**: Additional client-specific organizational data

Examples:
    >>> from core_db.registry.client import ClientActions, ClientFactsModel, ClientFactsFactory

    >>> # Create a new client with full metadata
    >>> result = ClientActions.create(
    ...     client="acme",
    ...     organization="Acme Corporation",
    ...     contact_email="admin@acme.com",
    ...     billing_tier="enterprise",
    ...     regions=["us-east-1", "us-west-2"],
    ...     features={
    ...         "multi_region": True,
    ...         "advanced_monitoring": True,
    ...         "sso": True
    ...     },
    ...     metadata={
    ...         "industry": "technology",
    ...         "employee_count": 5000
    ...     }
    ... )

    >>> # List all clients in the system
    >>> clients = ClientActions.list()
    >>> for client in clients.data:
    ...     print(f"Client: {client['Client']}")
    ...     print(f"Organization: {client.get('organization')}")
    ...     print(f"Billing: {client.get('billing_tier', 'standard')}")

    >>> # Get specific client details
    >>> client = ClientActions.get(client="acme")
    >>> if client.data:
    ...     print(f"Contact: {client.data.get('contact_email')}")
    ...     print(f"Regions: {client.data.get('regions', [])}")

    >>> # Update client billing tier
    >>> result = ClientActions.patch(
    ...     client="acme",
    ...     billing_tier="premium",
    ...     features={
    ...         "multi_region": True,
    ...         "advanced_monitoring": True,
    ...         "premium_support": True
    ...     }
    ... )

    >>> # Use model factory directly for advanced operations
    >>> ClientModel = ClientFactsFactory.get_model("global")
    >>> all_clients = list(ClientModel.scan())
    >>> enterprise_clients = [
    ...     c for c in all_clients
    ...     if c.billing_tier == "enterprise"
    ... ]

Usage Patterns:
    **Client Onboarding**: Create new client records with organizational metadata

    **Billing Management**: Track billing tiers and feature entitlements per client

    **Regional Configuration**: Manage enabled AWS regions per client

    **Feature Flags**: Control feature availability through client-specific settings

    **Contact Management**: Maintain primary contact information for each client

Table Information:
    - **Table Name**: global-core-automation-registry (global table)
    - **Hash Key**: Client (client identifier)
    - **Schema Type**: Client FACTS with organizational metadata
    - **Billing Mode**: PAY_PER_REQUEST
    - **Access Pattern**: Global table for system-wide client management

Client Configuration Examples:
    ```python
    # Startup client (basic tier)
    startup_client = {
        "client": "startup-inc",
        "organization": "Startup Inc",
        "contact_email": "admin@startup-inc.com",
        "billing_tier": "standard",
        "regions": ["us-east-1"],
        "features": {
            "basic_monitoring": True,
            "email_support": True
        },
        "metadata": {
            "industry": "fintech",
            "employee_count": 25,
            "founded": "2023"
        }
    }

    # Enterprise client (full features)
    enterprise_client = {
        "client": "megacorp",
        "organization": "MegaCorp Industries",
        "contact_email": "enterprise-admin@megacorp.com",
        "billing_tier": "enterprise",
        "regions": ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
        "features": {
            "multi_region": True,
            "advanced_monitoring": True,
            "sso": True,
            "custom_domains": True,
            "dedicated_support": True,
            "sla_guarantees": True
        },
        "metadata": {
            "industry": "technology",
            "employee_count": 50000,
            "compliance_requirements": ["SOC2", "GDPR", "HIPAA"],
            "support_tier": "platinum"
        }
    }

    # Government client (compliance focused)
    gov_client = {
        "client": "gov-agency",
        "organization": "Government Agency",
        "contact_email": "admin@gov-agency.gov",
        "billing_tier": "government",
        "regions": ["us-gov-east-1", "us-gov-west-1"],
        "features": {
            "government_cloud": True,
            "enhanced_security": True,
            "audit_logging": True,
            "encryption_at_rest": True
        },
        "metadata": {
            "sector": "government",
            "security_clearance": "secret",
            "compliance_requirements": ["FedRAMP", "FISMA"]
        }
    }
    ```

Billing Tier Examples:
    ```python
    # Different billing tiers with feature sets
    billing_tiers = {
        "standard": {
            "max_regions": 1,
            "max_portfolios": 5,
            "max_applications": 50,
            "features": ["basic_monitoring", "email_support"],
            "sla": "99.5%"
        },
        "premium": {
            "max_regions": 3,
            "max_portfolios": 20,
            "max_applications": 200,
            "features": ["advanced_monitoring", "phone_support", "backup_retention"],
            "sla": "99.9%"
        },
        "enterprise": {
            "max_regions": "unlimited",
            "max_portfolios": "unlimited",
            "max_applications": "unlimited",
            "features": ["all_features", "dedicated_support", "custom_integrations"],
            "sla": "99.99%"
        },
        "government": {
            "max_regions": "unlimited",
            "max_portfolios": "unlimited",
            "max_applications": "unlimited",
            "features": ["gov_cloud", "enhanced_security", "compliance_tools"],
            "sla": "99.99%"
        }
    }
    ```

Integration Points:
    - **Multi-tenancy**: Client records enable proper tenant isolation
    - **Billing Systems**: Integration with billing and invoicing systems
    - **Feature Flags**: Dynamic feature control based on client tier
    - **Regional Deployment**: Control deployment regions per client
    - **Support Systems**: Contact information for customer support
    - **Compliance**: Track compliance requirements per client

Related Modules:
    - core_db.registry: Base registry system and common functionality
    - core_db.registry.actions: Base RegistryAction class with shared methods
    - core_billing: Billing system integration with client tiers
    - core_auth: Authentication and authorization per client

Error Handling:
    All operations may raise:
    - BadRequestException: Invalid parameters or missing required fields
    - ConflictException: Client already exists (create operations)
    - NotFoundException: Client not found (get/update/delete operations)
    - UnknownException: Database connection issues or unexpected errors

Best Practices:
    - **Unique Client Names**: Use consistent, URL-safe client identifiers
    - **Contact Information**: Keep contact emails current for support
    - **Feature Management**: Use feature flags for gradual rollouts
    - **Regional Planning**: Plan region usage based on data locality requirements
    - **Metadata Consistency**: Use consistent metadata structure across clients

Operational Considerations:
    - **Client Lifecycle**: Plan for client onboarding and offboarding processes
    - **Data Retention**: Consider data retention policies for deleted clients
    - **Backup Strategy**: Ensure client configuration data is properly backed up
    - **Access Control**: Implement proper access controls for client management
    - **Audit Logging**: Track changes to client configurations for compliance

Note:
    Client registry is the foundation for multi-tenant operations. Ensure client
    configurations are properly validated and maintained for system stability.
    Client changes may affect related portfolios, applications, and deployments.
"""

from .models import ClientFactsModel, ClientFactsFactory
from .actions import ClientActions

__all__ = ["ClientFactsModel", "ClientActions", "ClientFactsFactory"]
