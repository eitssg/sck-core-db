"""The Item module provides CRUD interface to the core-automation-items DynamoDB table.

This module serves as the main entry point for managing hierarchical deployment items
in the DynamoDB items table. It provides a unified interface for creating, reading,
updating, and deleting deployment hierarchy items including portfolios, apps, branches,
builds, and components.

Key Components:
    - **ItemModel**: PynamoDB model for DynamoDB table operations
    - **ItemActions**: High-level CRUD actions with validation and business logic

Features:
    - **Hierarchical Data Management**: Support for nested deployment hierarchy
    - **Client Isolation**: Each client has their own items table namespace
    - **Type-Safe Operations**: Strongly typed CRUD operations with validation
    - **Audit Trail**: Automatic creation/modification timestamp tracking
    - **Flexible Querying**: Support for complex queries across item hierarchies

Deployment Hierarchy:
    ```
    Portfolio (top-level)
    ├── App (portfolio children)
    │   ├── Branch (app children)
    │   │   ├── Build (branch children)
    │   │   │   └── Component (build children - leaf nodes)
    ```

Schema Structure:
    The core-automation-items table uses a flexible schema with:
    - **prn**: Primary key with format "type:client:portfolio:app:branch:build:component"
    - **item_type**: Type discriminator (portfolio, app, branch, build, component)
    - **name**: Human-readable display name
    - **parent_prn**: Reference to parent item (except portfolios)
    - **status**: Current item status (active, inactive, archived)
    - **created_at/updated_at**: Automatic audit timestamps
    - **type-specific fields**: Additional fields based on item type

Examples:
    >>> from core_db.item import ItemActions, ItemModel

    >>> # Create a new portfolio item
    >>> result = ItemActions.create(
    ...     prn="portfolio:acme:web-services",
    ...     item_type="portfolio",
    ...     name="Web Services Portfolio",
    ...     description="Customer-facing web applications and APIs",
    ...     owner={
    ...         "name": "John Smith",
    ...         "email": "john.smith@acme.com"
    ...     },
    ...     status="active"
    ... )

    >>> # Create an app item
    >>> ItemActions.create(
    ...     prn="app:acme:web-services:api",
    ...     item_type="app",
    ...     name="Web API Application",
    ...     parent_prn="portfolio:acme:web-services",
    ...     repository="https://github.com/acme/web-api.git",
    ...     default_branch="main",
    ...     status="active"
    ... )

    >>> # Retrieve item data
    >>> item_data = ItemActions.get(
    ...     prn="portfolio:acme:web-services"
    ... )
    >>> print(f"Portfolio: {item_data.name}")
    >>> print(f"Owner: {item_data.owner['email']}")

    >>> # Query items by type
    >>> portfolios = ItemActions.query_by_type(
    ...     client="acme",
    ...     item_type="portfolio"
    ... )
    >>> for portfolio in portfolios:
    ...     print(f"Portfolio: {portfolio.name}")

    >>> # Query child items
    >>> apps = ItemActions.query_children(
    ...     parent_prn="portfolio:acme:web-services"
    ... )
    >>> for app in apps:
    ...     print(f"App: {app.name} - {app.repository}")

    >>> # Update item status
    >>> ItemActions.update(
    ...     prn="app:acme:web-services:api",
    ...     status="inactive",
    ...     notes="Migrating to new architecture"
    ... )

    >>> # Create complete hierarchy
    >>> # Portfolio -> App -> Branch -> Build -> Component
    >>> ItemActions.create(
    ...     prn="branch:acme:web-services:api:main",
    ...     item_type="branch",
    ...     name="Main Branch",
    ...     parent_prn="app:acme:web-services:api",
    ...     git_branch="main",
    ...     environment="production",
    ...     auto_deploy=True
    ... )
    >>>
    >>> ItemActions.create(
    ...     prn="build:acme:web-services:api:main:123",
    ...     item_type="build",
    ...     name="Build #123",
    ...     parent_prn="branch:acme:web-services:api:main",
    ...     build_number="123",
    ...     git_commit="a1b2c3d4e5f6789012345678901234567890abcd"
    ... )
    >>>
    >>> ItemActions.create(
    ...     prn="component:acme:web-services:api:main:123:lambda",
    ...     item_type="component",
    ...     name="API Lambda Function",
    ...     parent_prn="build:acme:web-services:api:main:123",
    ...     component_type="lambda",
    ...     artifact_location="s3://acme-artifacts/api/123/lambda.zip"
    ... )

    >>> # Bulk operations
    >>> all_items = ItemActions.scan_all(client="acme")
    >>> active_items = [item for item in all_items if item.status == "active"]

    >>> # Delete item (consider cascading effects)
    >>> ItemActions.delete(prn="component:acme:web-services:api:main:120:old-lambda")

Usage Patterns:
    **Creating Items**: Use ItemActions.create() with appropriate item_type and hierarchy

    **Querying Items**: Use ItemActions.get() for single items, query methods for collections

    **Hierarchy Navigation**: Use parent_prn relationships to traverse the deployment tree

    **Type-Specific Operations**: Different item types have specific fields and validation

    **Bulk Operations**: Use scan and query methods for large-scale data operations

Table Information:
    - **Table Name**: {client}-core-automation-items (client-specific)
    - **Hash Key**: prn (type:client:portfolio:app:branch:build:component)
    - **Schema Type**: Flexible schema with type discriminator
    - **Billing Mode**: PAY_PER_REQUEST
    - **Client Isolation**: Each client has separate table

PRN (Primary Resource Name) Format:
    ```python
    # PRN format by item type
    prn_formats = {
        "portfolio": "portfolio:client:portfolio_name",
        "app": "app:client:portfolio:app_name",
        "branch": "branch:client:portfolio:app:branch_name",
        "build": "build:client:portfolio:app:branch:build_number",
        "component": "component:client:portfolio:app:branch:build:component_name"
    }
    ```

Item Types and Validation:
    ```python
    # Supported item types with validation rules
    item_types = {
        "portfolio": {
            "required_fields": ["name", "owner"],
            "optional_fields": ["description", "cost_center", "contacts"],
            "parent_required": False
        },
        "app": {
            "required_fields": ["name", "parent_prn"],
            "optional_fields": ["repository", "default_branch", "zone"],
            "parent_required": True,
            "parent_type": "portfolio"
        },
        "branch": {
            "required_fields": ["name", "parent_prn", "git_branch"],
            "optional_fields": ["environment", "auto_deploy"],
            "parent_required": True,
            "parent_type": "app"
        },
        "build": {
            "required_fields": ["name", "parent_prn", "build_number"],
            "optional_fields": ["git_commit", "artifacts", "test_results"],
            "parent_required": True,
            "parent_type": "branch"
        },
        "component": {
            "required_fields": ["name", "parent_prn", "component_type"],
            "optional_fields": ["artifact_location", "aws_resources"],
            "parent_required": True,
            "parent_type": "build"
        }
    }
    ```

Common Query Patterns:
    ```python
    # Query all portfolios for a client
    portfolios = ItemActions.query_by_type("acme", "portfolio")

    # Query all apps in a portfolio
    apps = ItemActions.query_children("portfolio:acme:web-services")

    # Query all components in a build
    components = ItemActions.query_children("build:acme:web-services:api:main:123")

    # Get deployment hierarchy for an app
    app_hierarchy = ItemActions.get_hierarchy("app:acme:web-services:api")

    # Query items by status across all types
    active_items = ItemActions.query_by_status("acme", "active")
    ```

Integration with Specialized Modules:
    ```python
    # This module provides the base functionality
    # Specialized modules provide type-specific operations:

    from core_db.item.portfolio import PortfolioActions  # Portfolio-specific
    from core_db.item.app import AppActions              # App-specific
    from core_db.item.branch import BranchActions        # Branch-specific
    from core_db.item.build import BuildActions          # Build-specific
    from core_db.item.component import ComponentActions  # Component-specific

    # Use specialized modules for type-specific operations
    # Use this module for generic item operations
    ```

Related Modules:
    - core_db.item.portfolio: Portfolio-specific operations and validation
    - core_db.item.app: Application-specific operations and validation
    - core_db.item.branch: Branch-specific operations and validation
    - core_db.item.build: Build-specific operations and validation
    - core_db.item.component: Component-specific operations and validation

Error Handling:
    All operations may raise:
    - NotFoundException: Item not found
    - ConflictException: Item already exists (create operations)
    - BadRequestException: Invalid item data or PRN format
    - ValidationException: Item data fails validation rules
    - UnauthorizedException: Missing or invalid authentication
    - ForbiddenException: Insufficient permissions for operation

Best Practices:
    - **Use PRN consistently**: Follow the established PRN format for all items
    - **Validate hierarchy**: Ensure parent items exist before creating children
    - **Handle cascading**: Consider impact when deleting items with children
    - **Use appropriate modules**: Use specialized modules for type-specific operations
    - **Implement pagination**: Use pagination for large result sets
    - **Monitor performance**: Be aware of query patterns and table design

Note:
    This module provides the foundation for the deployment hierarchy system.
    While it can handle all item types generically, consider using the specialized
    modules (portfolio, app, branch, build, component) for type-specific operations
    and validation. The generic interface is best for cross-cutting concerns and
    administrative operations.
"""

from .models import ItemModel
from .actions import ItemTableActions as ItemActions

__all__ = ["ItemModel", "ItemActions"]
