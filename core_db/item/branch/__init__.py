"""Branch item management for the core-automation-items table.

This module provides comprehensive branch item management functionality including
actions, models, and data validation for branch records in the DynamoDB items table.
Branch items represent Git branch-level organizational units within app hierarchies.

Key Components:
    - **BranchActions**: CRUD operations for branch items with validation
    - **BranchModel**: PynamoDB model for DynamoDB branch table operations
    - **BranchRecord**: Pydantic model for API serialization and validation
    - **Branch validation**: Business rules and constraints for branch data

Features:
    - **Hierarchical Organization**: Branch items serve as children of apps and parents of builds
    - **Client Isolation**: Each client has their own branch namespace within apps
    - **Git Integration**: Git branch tracking and repository synchronization
    - **Environment Mapping**: Branch-to-environment deployment configuration
    - **Build Tracking**: Parent reference for all builds created from this branch
    - **Audit Trail**: Automatic creation/modification timestamp tracking

Branch Hierarchy:
    ```
    Portfolio (grandparent)
    ├── App (parent)
    │   ├── Branch (this module)
    │   │   ├── Build (branch_prn references this)
    │   │   │   └── Component (build_prn references build)
    ```

Schema Structure:
    The branch schema in the core-automation-items table includes:
    - **prn**: Primary key in format "branch:client:portfolio:app:branch_name"
    - **name**: Human-readable branch display name
    - **app_prn**: Reference to parent app
    - **git_branch**: Actual Git branch name in repository
    - **environment**: Target deployment environment (dev, staging, production)
    - **region_alias**: Deployment region configuration
    - **auto_deploy**: Automatic deployment flag for CI/CD
    - **status**: Current branch status (active, inactive, archived)
    - **last_build**: Reference to most recent build from this branch
    - **created_at/updated_at**: Automatic audit timestamps

Examples:
    >>> from core_db.item.branch import BranchActions, BranchRecord

    >>> # Create a new branch
    >>> result = BranchActions.create(
    ...     prn="branch:acme:web-services:api:main",
    ...     name="Main Branch",
    ...     app_prn="app:acme:web-services:api",
    ...     git_branch="main",
    ...     environment="production",
    ...     region_alias="us-west-2",
    ...     auto_deploy=True,
    ...     status="active"
    ... )

    >>> # Retrieve branch data
    >>> branch_data = BranchActions.get(
    ...     prn="branch:acme:web-services:api:main"
    ... )

    >>> # Convert to API response format
    >>> branch_record = BranchRecord.from_dynamodb(branch_data.data)
    >>> api_response = branch_record.model_dump()

    >>> # List all branches in an app
    >>> branches = BranchActions.list_by_app("app:acme:web-services:api")

    >>> # Update branch configuration
    >>> BranchActions.update(
    ...     prn="branch:acme:web-services:api:main",
    ...     auto_deploy=False,
    ...     environment="staging"
    ... )

    >>> # Create development branch
    >>> BranchActions.create(
    ...     prn="branch:acme:web-services:api:develop",
    ...     name="Development Branch",
    ...     app_prn="app:acme:web-services:api",
    ...     git_branch="develop",
    ...     environment="development",
    ...     region_alias="us-east-1",
    ...     auto_deploy=True,
    ...     status="active"
    ... )

    >>> # Create feature branch
    >>> BranchActions.create(
    ...     prn="branch:acme:web-services:api:feature-auth",
    ...     name="Authentication Feature",
    ...     app_prn="app:acme:web-services:api",
    ...     git_branch="feature/authentication",
    ...     environment="development",
    ...     region_alias="us-east-1",
    ...     auto_deploy=False,
    ...     status="active"
    ... )

    >>> # Archive old branch
    >>> BranchActions.update(
    ...     prn="branch:acme:web-services:api:old-feature",
    ...     status="archived"
    ... )

    >>> # Delete branch (cascading considerations apply)
    >>> BranchActions.delete(prn="branch:acme:web-services:api:feature-auth")

Usage Patterns:
    **Creating Branches**: Use BranchActions.create() with app reference and Git branch mapping

    **Querying Branches**: Use BranchActions.get() for single items or BranchActions.list() for bulk operations

    **API Integration**: Use BranchRecord for JSON serialization and API responses

    **Hierarchy Management**: Branch PRNs serve as parent_prn for build items

    **Git Integration**: Map branch items to actual Git repository branches

    **Environment Configuration**: Set up deployment targets and auto-deploy behavior

Table Information:
    - **Table Name**: {client}-core-automation-items (client-specific)
    - **Hash Key**: prn (branch:client:portfolio:app:branch_name)
    - **Schema Type**: Items.Branch
    - **Billing Mode**: PAY_PER_REQUEST
    - **Client Isolation**: Each client has separate table

Validation Rules:
    - PRN must follow format: "branch:client:portfolio:app:branch_name"
    - Branch name must be unique within app namespace
    - App PRN must reference existing app
    - Git branch must be valid Git branch name format
    - Environment must be from allowed environment constants
    - Region alias must be valid AWS region identifier
    - Status must be from allowed status constants
    - Auto deploy flag must be boolean

Configuration Examples:
    ```python
    # Production main branch
    main_branch = {
        "prn": "branch:acme:web-services:api:main",
        "name": "Production Main",
        "app_prn": "app:acme:web-services:api",
        "git_branch": "main",
        "environment": "production",
        "region_alias": "us-west-2",
        "auto_deploy": True,
        "status": "active",
        "protection_rules": {
            "require_pull_request": True,
            "require_approvals": 2,
            "dismiss_stale_reviews": True
        }
    }

    # Development branch
    dev_branch = {
        "prn": "branch:acme:web-services:api:develop",
        "name": "Development Branch",
        "app_prn": "app:acme:web-services:api",
        "git_branch": "develop",
        "environment": "development",
        "region_alias": "us-east-1",
        "auto_deploy": True,
        "status": "active",
        "protection_rules": {
            "require_pull_request": False,
            "auto_merge": True
        }
    }

    # Feature branch
    feature_branch = {
        "prn": "branch:enterprise:platform:auth:feature-oauth2",
        "name": "OAuth2 Integration Feature",
        "app_prn": "app:enterprise:platform:auth",
        "git_branch": "feature/oauth2-integration",
        "environment": "development",
        "region_alias": "us-east-1",
        "auto_deploy": False,
        "status": "active",
        "temporary": True,
        "expires_at": "2025-03-01T00:00:00Z"
    }

    # Release branch
    release_branch = {
        "prn": "branch:acme:web-services:api:release-v2.1",
        "name": "Release v2.1",
        "app_prn": "app:acme:web-services:api",
        "git_branch": "release/v2.1",
        "environment": "staging",
        "region_alias": "us-west-2",
        "auto_deploy": False,
        "status": "active",
        "release_config": {
            "version": "2.1.0",
            "release_notes": "Major feature update",
            "rollback_branch": "main"
        }
    }
    ```

Branch Types and Strategies:
    **Main/Master Branch**: Production deployment target with strict protection rules

    **Development Branch**: Continuous integration target for active development

    **Feature Branches**: Short-lived branches for specific features or bug fixes

    **Release Branches**: Stabilization branches for versioned releases

    **Hotfix Branches**: Emergency fix branches that bypass normal development flow

Environment Mapping:
    ```python
    # Environment to region mapping
    environment_mapping = {
        "development": {
            "region_alias": "us-east-1",
            "auto_deploy": True,
            "protection_level": "low"
        },
        "staging": {
            "region_alias": "us-west-2",
            "auto_deploy": False,
            "protection_level": "medium"
        },
        "production": {
            "region_alias": "us-west-2",
            "auto_deploy": True,
            "protection_level": "high"
        }
    }
    ```

Related Modules:
    - core_db.item.app: Parent app items that branches reference
    - core_db.item.build: Child build items that reference branches
    - core_db.item.component: Component items for branch deployments
    - core_db.item.portfolio: Grandparent portfolio context

Error Handling:
    All operations may raise:
    - NotFoundException: Branch not found
    - ConflictException: Branch already exists (create operations)
    - BadRequestException: Invalid branch data or PRN format
    - UnauthorizedException: Missing or invalid authentication
    - ForbiddenException: Insufficient permissions for operation

Integration Points:
    - **Git Repositories**: Synchronization with actual Git branches
    - **CI/CD Pipelines**: Branch-based build and deployment triggers
    - **Environment Management**: Target environment configuration
    - **Build Systems**: Parent context for all builds from this branch

Note:
    Branch items represent the Git branch level in the deployment hierarchy. They
    connect app-level configuration to specific Git branches and define deployment
    targets. Deleting a branch may impact all child build and component items.
    Consider cascading effects and implement appropriate cleanup logic.
"""

from .actions import BranchActions
from .models import BranchModel, BranchItem

__all__ = ["BranchActions", "BranchModel", "BranchItem"]
