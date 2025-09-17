"""Profile management for the core-automation-profiles DynamoDB table.

This module provides comprehensive profile management functionality for user and system
profiles stored in the DynamoDB profiles table. Profiles contain authentication,
authorization, and configuration data for users, service accounts, and system entities
within the Simple Cloud Kit ecosystem.

Key Components:
    - **ProfileActions**: CRUD operations for profile items with validation
    - **ProfileModel**: PynamoDB model for DynamoDB profile table operations
    - **ProfileModelFactory**: Factory for creating profile models with client isolation

Features:
    - **User Profile Management**: Complete user profile lifecycle management
    - **Service Account Profiles**: System and service account profile support
    - **Client Isolation**: Each client has their own profiles table namespace
    - **Authentication Integration**: Profile data for authentication and authorization
    - **Configuration Storage**: User preferences and system configuration
    - **Audit Trail**: Automatic creation/modification timestamp tracking

Profile Types:
    - **User Profiles**: Individual user accounts with authentication data
    - **Service Profiles**: Service accounts for automated systems
    - **System Profiles**: Internal system entities and configurations
    - **API Key Profiles**: API key-based authentication profiles

Schema Structure:
    The profile schema in the core-automation-profiles table includes:
    - **profile_id**: Primary key identifier for the profile
    - **profile_type**: Type of profile (user, service, system, api_key)
    - **email**: Email address for user profiles (unique)
    - **name**: Display name for the profile
    - **status**: Current profile status (active, inactive, suspended)
    - **authentication**: Authentication configuration and credentials
    - **permissions**: Role-based access control permissions
    - **preferences**: User preferences and configuration settings
    - **metadata**: Additional profile metadata and tags
    - **created_at/updated_at**: Automatic audit timestamps

Examples:
    >>> from core_db.profile import ProfileActions, ProfileModel

    >>> # Create a user profile
    >>> result = ProfileActions.create(
    ...     profile_id="user:john.smith@acme.com",
    ...     profile_type="user",
    ...     email="john.smith@acme.com",
    ...     name="John Smith",
    ...     status="active",
    ...     authentication={
    ...         "method": "sso",
    ...         "provider": "okta",
    ...         "last_login": "2025-01-15T10:30:00Z"
    ...     },
    ...     permissions={
    ...         "roles": ["developer", "portfolio-admin"],
    ...         "portfolios": ["web-services", "mobile-apps"]
    ...     },
    ...     preferences={
    ...         "theme": "dark",
    ...         "notifications": {
    ...             "email": True,
    ...             "slack": True
    ...         }
    ...     }
    ... )

    >>> # Create a service account profile
    >>> ProfileActions.create(
    ...     profile_id="service:ci-cd-pipeline",
    ...     profile_type="service",
    ...     name="CI/CD Pipeline Service Account",
    ...     status="active",
    ...     authentication={
    ...         "method": "api_key",
    ...         "key_id": "AKIA...",
    ...         "permissions": "deployment"
    ...     },
    ...     metadata={
    ...         "purpose": "automated deployments",
    ...         "owner": "devops-team@acme.com"
    ...     }
    ... )

    >>> # Retrieve profile data
    >>> profile_data = ProfileActions.get(
    ...     profile_id="user:john.smith@acme.com"
    ... )
    >>> print(f"User: {profile_data.data['name']}")
    >>> print(f"Roles: {profile_data.data['permissions']['roles']}")

    >>> # Update profile preferences
    >>> ProfileActions.update(
    ...     profile_id="user:john.smith@acme.com",
    ...     preferences={
    ...         "theme": "light",
    ...         "notifications": {
    ...             "email": True,
    ...             "slack": False
    ...         }
    ...     }
    ... )

    >>> # List all active user profiles
    >>> active_users = ProfileActions.list_by_type_and_status(
    ...     profile_type="user",
    ...     status="active"
    ... )

    >>> # Create API key profile
    >>> ProfileActions.create(
    ...     profile_id="api_key:mobile-app-prod",
    ...     profile_type="api_key",
    ...     name="Mobile App Production API Key",
    ...     status="active",
    ...     authentication={
    ...         "method": "api_key",
    ...         "key_hash": "sha256:abc123...",
    ...         "scopes": ["read:apps", "write:builds"]
    ...     },
    ...     metadata={
    ...         "application": "mobile-app",
    ...         "environment": "production",
    ...         "expires_at": "2025-12-31T23:59:59Z"
    ...     }
    ... )

    >>> # Suspend a profile
    >>> ProfileActions.update(
    ...     profile_id="user:former.employee@acme.com",
    ...     status="suspended",
    ...     metadata={
    ...         "suspension_reason": "employee departure",
    ...         "suspended_by": "hr-admin@acme.com",
    ...         "suspended_at": "2025-01-15T17:00:00Z"
    ...     }
    ... )

    >>> # Delete old API key profile
    >>> ProfileActions.delete(profile_id="api_key:old-mobile-key")

Usage Patterns:
    **Creating Profiles**: Use ProfileActions.create() with appropriate profile_type and data

    **Authentication**: Retrieve profile data for authentication and authorization

    **User Management**: Manage user lifecycle from creation to suspension/deletion

    **Service Accounts**: Create and manage automated system profiles

    **API Key Management**: Generate and track API key-based access profiles

    **Preference Storage**: Store and retrieve user configuration preferences

Table Information:
    - **Table Name**: {client}-core-automation-profiles (client-specific)
    - **Hash Key**: profile_id (user:email, service:name, api_key:name, etc.)
    - **Schema Type**: Profile schema with type discriminator
    - **Billing Mode**: PAY_PER_REQUEST
    - **Client Isolation**: Each client has separate table

Profile ID Format:
    ```python
    # Profile ID format by type
    profile_id_formats = {
        "user": "user:email@domain.com",
        "service": "service:service-name",
        "system": "system:system-component",
        "api_key": "api_key:key-identifier"
    }
    ```

Authentication Methods:
    ```python
    # Supported authentication methods
    auth_methods = {
        "sso": "Single Sign-On (OIDC/SAML)",
        "password": "Username/password authentication",
        "api_key": "API key-based authentication",
        "service_token": "Service-to-service authentication",
        "certificate": "Certificate-based authentication"
    }
    ```

Permission Structure:
    ```python
    # Role-based access control structure
    permissions_example = {
        "roles": ["developer", "portfolio-admin"],
        "portfolios": ["web-services", "mobile-apps"],
        "permissions": [
            "read:portfolios",
            "write:apps",
            "deploy:staging"
        ],
        "restrictions": {
            "ip_whitelist": ["192.168.1.0/24"],
            "time_restrictions": "business_hours"
        }
    }
    ```

Profile Status Lifecycle:
    ```python
    # Profile status progression
    profile_statuses = [
        "pending",     # Profile created, awaiting activation
        "active",      # Profile active and usable
        "inactive",    # Profile temporarily disabled
        "suspended",   # Profile suspended due to policy violation
        "expired",     # Profile expired (API keys, temporary accounts)
        "archived"     # Profile archived for compliance retention
    ]
    ```

Configuration Examples:
    ```python
    # User profile configuration
    user_profile = {
        "profile_id": "user:alice.developer@acme.com",
        "profile_type": "user",
        "email": "alice.developer@acme.com",
        "name": "Alice Developer",
        "status": "active",
        "authentication": {
            "method": "sso",
            "provider": "okta",
            "external_id": "alice.developer",
            "mfa_enabled": True,
            "last_login": "2025-01-15T10:30:00Z"
        },
        "permissions": {
            "roles": ["developer", "team-lead"],
            "portfolios": ["web-services"],
            "permissions": [
                "read:portfolios",
                "write:apps",
                "write:branches",
                "deploy:staging"
            ]
        },
        "preferences": {
            "theme": "dark",
            "timezone": "America/New_York",
            "notifications": {
                "email": True,
                "slack": True,
                "desktop": False
            },
            "dashboard": {
                "default_view": "portfolios",
                "items_per_page": 20
            }
        }
    }

    # Service account profile
    service_profile = {
        "profile_id": "service:github-actions-ci",
        "profile_type": "service",
        "name": "GitHub Actions CI Service",
        "status": "active",
        "authentication": {
            "method": "api_key",
            "key_id": "SCKA1234567890ABCDEF",
            "key_hash": "sha256:def456...",
            "scopes": ["read:apps", "write:builds", "deploy:staging"]
        },
        "permissions": {
            "roles": ["ci-service"],
            "portfolios": ["web-services", "mobile-apps"],
            "permissions": [
                "read:apps",
                "write:builds",
                "write:components",
                "deploy:staging"
            ]
        },
        "metadata": {
            "purpose": "CI/CD automation",
            "owner": "devops-team@acme.com",
            "repository": "https://github.com/acme/web-services",
            "created_by": "devops-admin@acme.com"
        }
    }

    # API key profile
    api_key_profile = {
        "profile_id": "api_key:mobile-app-staging",
        "profile_type": "api_key",
        "name": "Mobile App Staging Environment",
        "status": "active",
        "authentication": {
            "method": "api_key",
            "key_hash": "sha256:789abc...",
            "scopes": ["read:apps", "read:builds"],
            "rate_limit": {
                "requests_per_minute": 100,
                "burst_limit": 200
            }
        },
        "metadata": {
            "application": "mobile-app",
            "environment": "staging",
            "created_by": "mobile-team@acme.com",
            "expires_at": "2025-06-30T23:59:59Z"
        }
    }
    ```

Related Modules:
    - core_db.client: Client management and tenant isolation
    - core_db.item: Deployment hierarchy items that profiles have access to
    - core_auth: Authentication and authorization services
    - core_api: API endpoints that consume profile data

Error Handling:
    All operations may raise:
    - NotFoundException: Profile not found
    - ConflictException: Profile already exists (create operations)
    - BadRequestException: Invalid profile data or ID format
    - ValidationException: Profile data fails validation rules
    - UnauthorizedException: Missing or invalid authentication
    - ForbiddenException: Insufficient permissions for operation

Integration Points:
    - **Authentication Services**: Profile data for login and token validation
    - **Authorization Services**: Role and permission enforcement
    - **API Gateway**: Profile-based rate limiting and access control
    - **Audit Logging**: Profile activity tracking and compliance
    - **User Interface**: Profile management and preference settings

Best Practices:
    - **Use appropriate profile types**: Choose the right profile type for each use case
    - **Secure credential storage**: Hash API keys and never store plaintext passwords
    - **Regular access review**: Periodically review and clean up unused profiles
    - **Principle of least privilege**: Grant minimum necessary permissions
    - **Audit trail maintenance**: Track profile changes for compliance
    - **Expire temporary profiles**: Set expiration dates for API keys and temporary accounts

Note:
    Profile management is critical for security and access control. Always validate
    profile data, follow security best practices for credential storage, and maintain
    proper audit trails. Consider data privacy regulations when storing user information.
"""

from .actions import ProfileActions
from .model import UserProfile, ProfileModelFactory

__all__ = ["ProfileActions", "UserProfile", "ProfileModelFactory"]
