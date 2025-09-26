"""Portfolio item management for the core-automation-items table.

This module provides comprehensive portfolio item management functionality including
actions, models, and data validation for portfolio records in the DynamoDB items table.
Portfolio items represent top-level organizational units for deployment hierarchies.

Key Components:
    - **PortfolioActions**: CRUD operations for portfolio items with validation
    - **PortfolioModel**: PynamoDB model for DynamoDB portfolio table operations
    - **PortfolioRecord**: Pydantic model for API serialization and validation
    - **Portfolio validation**: Business rules and constraints for portfolio data

Features:
    - **Hierarchical Organization**: Portfolio items serve as parent containers for apps
    - **Client Isolation**: Each client has their own portfolio namespace
    - **Contact Management**: Contact information tracking for portfolio ownership
    - **Status Tracking**: Portfolio lifecycle status management
    - **Audit Trail**: Automatic creation/modification timestamp tracking

Portfolio Hierarchy:
    
    Portfolio (this module)
    ├── App (portfolio_prn references this)
    │   ├── Branch (app_prn references app)
    │   │   ├── Build (branch_prn references branch)
    │   │   │   └── Component (build_prn references build)
    

Schema Structure:
    The portfolio schema in the core-automation-items table includes:
    - **prn**: Primary key in format "portfolio:client:portfolio_name"
    - **name**: Human-readable portfolio display name
    - **contact_email**: Primary contact for the portfolio
    - **status**: Current portfolio status (active, inactive, etc.)
    - **created_at/updated_at**: Automatic audit timestamps

Examples:
    >>> from core_db.item.portfolio import PortfolioActions, PortfolioRecord

    >>> # Create a new portfolio
    >>> result = PortfolioActions.create(
    ...     prn="portfolio:acme:web-services",
    ...     name="Web Services Portfolio",
    ...     contact_email="webteam@acme.com",
    ...     status="active"
    ... )

    >>> # Retrieve portfolio data
    >>> portfolio_data = PortfolioActions.get(
    ...     prn="portfolio:acme:web-services"
    ... )

    >>> # Convert to API response format
    >>> portfolio_record = PortfolioRecord.from_dynamodb(portfolio_data.data)
    >>> api_response = portfolio_record.model_dump()

    >>> # List all portfolios for a client
    >>> portfolios = PortfolioActions.list_by_client("acme")

    >>> # Update portfolio information
    >>> PortfolioActions.update(
    ...     prn="portfolio:acme:web-services",
    ...     contact_email="newteam@acme.com",
    ...     status="maintenance"
    ... )

    >>> # Delete portfolio (cascading considerations apply)
    >>> PortfolioActions.delete(prn="portfolio:acme:web-services")

Usage Patterns:
    **Creating Portfolios**: Use PortfolioActions.create() with full PRN and metadata

    **Querying Portfolios**: Use PortfolioActions.get() for single items or
    PortfolioActions.list() for bulk operations

    **API Integration**: Use PortfolioRecord for JSON serialization and API responses

    **Hierarchy Management**: Portfolio PRNs serve as parent_prn for app items

Table Information:
    - **Table Name**: {client}-core-automation-items (client-specific)
    - **Hash Key**: prn (portfolio:client:portfolio_name)
    - **Schema Type**: Items.Portfolio
    - **Billing Mode**: PAY_PER_REQUEST
    - **Client Isolation**: Each client has separate table

Validation Rules:
    - PRN must follow format: "portfolio:client:portfolio_name"
    - Portfolio name must be unique within client namespace
    - Contact email must be valid email format
    - Status must be from allowed status constants
    - Client name must be lowercase alphanumeric with hyphens

Related Modules:
    - core_db.item.app: Child app items that reference portfolios
    - core_db.item.branch: Grandchild branch items in the hierarchy
    - core_db.item.build: Build items for specific branch deployments
    - core_db.item.component: Component items for build artifacts

Error Handling:
    All operations may raise:
    - NotFoundException: Portfolio not found
    - ConflictException: Portfolio already exists (create operations)
    - BadRequestException: Invalid portfolio data or PRN format
    - UnauthorizedException: Missing or invalid authentication
    - ForbiddenException: Insufficient permissions for operation

Note:
    Portfolio items are foundational to the deployment hierarchy. Deleting a portfolio
    may impact all child app, branch, build, and component items. Consider cascading
    effects and implement appropriate cleanup or prevention logic.
"""

from .actions import PortfolioActions
from .models import PortfolioModel, PortfolioModelFactory, PortfolioItem
