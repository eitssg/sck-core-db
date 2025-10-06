"""App item management for the core-automation-items table.

This module provides comprehensive app item management functionality including
actions, models, and data validation for app records in the DynamoDB items table.
App items represent application-level organizational units within portfolio hierarchies.

Key Components:
    - **AppActions**: CRUD operations for app items with validation
    - **AppModel**: PynamoDB model for DynamoDB app table operations
    - **AppRecord**: Pydantic model for API serialization and validation
    - **App validation**: Business rules and constraints for app data

Features:
    - **Hierarchical Organization**: App items serve as children of portfolios and parents of branches
    - **Client Isolation**: Each client has their own app namespace within portfolios
    - **Repository Management**: Git repository configuration and branch tracking
    - **Deployment Configuration**: Build and deployment parameter management
    - **Approval Workflows**: Configurable approval chains for deployments
    - **Audit Trail**: Automatic creation/modification timestamp tracking

App Hierarchy:

    Portfolio (parent)
    ├── App (this module)
    │   ├── Branch (app_prn references this)
    │   │   ├── Build (branch_prn references branch)
    │   │   │   └── Component (build_prn references build)


Schema Structure:
    The app schema in the core-automation-items table includes:
    - **prn**: Primary key in format "app:client:portfolio:app_name"
    - **name**: Human-readable app display name
    - **portfolio_prn**: Reference to parent portfolio
    - **repository**: Git repository URL for source code
    - **default_branch**: Primary branch for deployments
    - **zone**: Target deployment zone/environment
    - **approvers**: List of approval workflow configurations
    - **contact_email**: Primary contact for the app
    - **status**: Current app status (active, inactive, etc.)
    - **created_at/updated_at**: Automatic audit timestamps

Examples:
    >>> from core_db.item.app import AppActions, AppRecord

    >>> # Create a new app
    >>> result = AppActions.create(
    ...     prn="app:acme:web-services:api",
    ...     name="Web API Application",
    ...     portfolio_prn="portfolio:acme:web-services",
    ...     repository="https://github.com/acme/web-api.git",
    ...     default_branch="main",
    ...     zone="production",
    ...     contact_email="api-team@acme.com",
    ...     status="active"
    ... )

    >>> # Retrieve app data
    >>> app_data = AppActions.get(
    ...     prn="app:acme:web-services:api"
    ... )

    >>> # Convert to API response format
    >>> app_record = AppRecord.from_dynamodb(app_data.data)
    >>> api_response = app_record.model_dump()

    >>> # List all apps in a portfolio
    >>> apps = AppActions.list_by_portfolio("portfolio:acme:web-services")

    >>> # Update app configuration
    >>> AppActions.update(
    ...     prn="app:acme:web-services:api",
    ...     default_branch="develop",
    ...     contact_email="new-api-team@acme.com"
    ... )

    >>> # Add approval workflow
    >>> AppActions.update(
    ...     prn="app:acme:web-services:api",
    ...     approvers=[
    ...         {
    ...             "sequence": 1,
    ...             "email": "lead-dev@acme.com",
    ...             "name": "Lead Developer",
    ...             "enabled": True,
    ...             "depends_on": []
    ...         },
    ...         {
    ...             "sequence": 2,
    ...             "email": "ops-manager@acme.com",
    ...             "name": "Operations Manager",
    ...             "enabled": True,
    ...             "depends_on": ["lead-dev@acme.com"]
    ...         }
    ...     ]
    ... )

    >>> # Delete app (cascading considerations apply)
    >>> AppActions.delete(prn="app:acme:web-services:api")

Usage Patterns:
    **Creating Apps**: Use AppActions.create() with portfolio reference and repository info

    **Querying Apps**: Use AppActions.get() for single items or AppActions.list() for bulk operations

    **API Integration**: Use AppRecord for JSON serialization and API responses

    **Hierarchy Management**: App PRNs serve as parent_prn for branch items

    **Repository Integration**: Configure Git repository and branch settings for CI/CD

    **Approval Workflows**: Set up multi-stage approval processes for production deployments

Table Information:
    - **Table Name**: {client}-core-automation-items (client-specific)
    - **Hash Key**: prn (app:client:portfolio:app_name)
    - **Schema Type**: Items.App
    - **Billing Mode**: PAY_PER_REQUEST
    - **Client Isolation**: Each client has separate table

Validation Rules:
    - PRN must follow format: "app:client:portfolio:app_name"
    - App name must be unique within portfolio namespace
    - Portfolio PRN must reference existing portfolio
    - Repository must be valid Git URL (if provided)
    - Contact email must be valid email format
    - Status must be from allowed status constants
    - Zone must reference valid deployment zone
    - Approvers must follow workflow sequence rules

Configuration Examples:
    .. code: python
        # Basic app configuration
        app_config = {
            "prn": "app:acme:web-services:api",
            "name": "Web API Service",
            "portfolio_prn": "portfolio:acme:web-services",
            "repository": "https://github.com/acme/web-api.git",
            "default_branch": "main",
            "zone": "production",
            "contact_email": "api-team@acme.com",
            "status": "active"
        }

        # Advanced app with approval workflow
        app_with_workflow = {
            "prn": "app:enterprise:platform:auth",
            "name": "Authentication Service",
            "portfolio_prn": "portfolio:enterprise:platform",
            "repository": "https://github.com/enterprise/auth-service.git",
            "default_branch": "main",
            "zone": "production",
            "contact_email": "auth-team@enterprise.com",
            "approvers": [
                {
                    "sequence": 1,
                    "email": "security-lead@enterprise.com",
                    "name": "Security Lead",
                    "enabled": True,
                    "depends_on": []
                },
                {
                    "sequence": 2,
                    "email": "platform-manager@enterprise.com",
                    "name": "Platform Manager",
                    "enabled": True,
                    "depends_on": ["security-lead@enterprise.com"]
                }
            ],
            "deployment_config": {
                "auto_deploy": False,
                "require_tests": True,
                "security_scan": True
            }
        }


Related Modules:
    - core_db.item.portfolio: Parent portfolio items that apps reference
    - core_db.item.branch: Child branch items that reference apps
    - core_db.item.build: Build items for specific app deployments
    - core_db.item.component: Component items for app artifacts

Error Handling:
    All operations may raise:
    - NotFoundException: App not found
    - ConflictException: App already exists (create operations)
    - BadRequestException: Invalid app data or PRN format
    - UnauthorizedException: Missing or invalid authentication
    - ForbiddenException: Insufficient permissions for operation

Integration Points:
    - **CI/CD Pipelines**: Repository and branch configuration for automated builds
    - **Approval Systems**: Workflow integration for deployment approvals
    - **Monitoring**: Contact information for alerts and notifications
    - **Security**: Zone-based deployment controls and access management

Note:
    App items are central to the deployment hierarchy. They connect portfolios to
    specific codebases and define deployment parameters. Deleting an app may impact
    all child branch, build, and component items. Consider cascading effects and
    implement appropriate cleanup or prevention logic.
"""

from .actions import AppActions
from .models import AppModel, AppItem

__all__ = ["AppActions", "AppModel", "AppItem"]
