"""Application Registry module for the core-automation-registry DynamoDB table.

This module provides comprehensive application deployment pattern management for the registry
system. It combines both data models and action classes to enable complete CRUD operations
for application registry entries with proper client isolation and flexible parameter handling.

Key Components:
    - **AppActions**: CRUD operations for application deployment patterns
    - **AppFactsModel**: PynamoDB model for DynamoDB registry table operations
    - **AppFactsFactory**: Factory for creating client-specific model instances

Features:
    - **Application Pattern Management**: Define regex patterns for deployment automation
    - **Client Isolation**: Each client has their own registry table namespace
    - **Flexible Parameters**: Supports both composite and separate parameter formats
    - **Deployment Configuration**: Store environment-specific deployment settings
    - **Template Management**: Associate applications with deployment templates

Application Structure:
    Applications are stored with a composite key structure in the registry table:
    - **Hash Key**: "client:portfolio" (formatted client-portfolio identifier)
    - **Range Key**: app-regex (regex pattern for application matching)
    - **Attributes**: Application-specific deployment configuration and metadata

Parameter Formats:
    The module supports flexible parameter formats for maximum API compatibility:
    - **Composite format**: client-portfolio="acme:web-services"
    - **Separate format**: client="acme", portfolio="web-services"
    - **Mixed usage**: Both formats can be used together with app-regex parameter

Schema Structure:
    The application registry schema includes:
    - **ClientPortfolio**: Hash key (client:portfolio format)
    - **AppRegex**: Range key (regex pattern for matching applications)
    - **description**: Human-readable application description
    - **deployment_template**: Path to deployment template file
    - **build_image**: Docker image for building applications
    - **environment_configs**: Environment-specific configuration settings
    - **custom_fields**: Additional application-specific metadata

Examples:
    >>> from core_db.registry.app import AppActions, AppFactsModel, AppFactsFactory

    >>> # Create application with composite parameters
    >>> result = AppActions.create(
    ...     **{
    ...         "client-portfolio": "acme:web-services",
    ...         "app-regex": "api-.*",
    ...         "description": "REST API applications",
    ...         "deployment_template": "api-template.yaml",
    ...         "environment_configs": {
    ...             "staging": {"replicas": 2, "cpu": "200m"},
    ...             "production": {"replicas": 5, "cpu": "500m"}
    ...         }
    ...     }
    ... )

    >>> # Create application with separate parameters
    >>> result = AppActions.create(
    ...     client="acme",
    ...     portfolio="mobile-apps",
    ...     **{"app-regex": "mobile-.*"},
    ...     description="Mobile applications",
    ...     build_image="mobile-builder:v2.0"
    ... )

    >>> # List all applications in a portfolio
    >>> apps = AppActions.list(client="acme", portfolio="web-services")
    >>> for app in apps.data:
    ...     print(f"Pattern: {app['AppRegex']} - {app.get('description')}")

    >>> # Get specific application
    >>> app = AppActions.get(
    ...     **{"client-portfolio": "acme:web-services", "app-regex": "api-.*"}
    ... )
    >>> print(f"Template: {app.data.get('deployment_template')}")

    >>> # Update application configuration
    >>> result = AppActions.patch(
    ...     client="acme",
    ...     portfolio="web-services",
    ...     **{"app-regex": "api-.*"},
    ...     environment_configs={
    ...         "staging": {"replicas": 3},
    ...         "production": {"replicas": 8}
    ...     }
    ... )

    >>> # Use model factory directly
    >>> AppModel = AppFactsFactory.get_model("acme")
    >>> apps = list(AppModel.query("acme:web-services"))
    >>> print(f"Found {len(apps)} applications")

Usage Patterns:
    **Application Creation**: Define regex patterns that match application names for deployment

    **Environment Configuration**: Store environment-specific settings for different deployment stages

    **Template Association**: Link applications to deployment templates for automated deployments

    **Pattern Matching**: Use regex patterns to automatically categorize and deploy applications

    **Client Isolation**: Separate application registries per client for multi-tenant deployments

Table Information:
    - **Table Name**: {client}-core-automation-registry (client-specific)
    - **Hash Key**: ClientPortfolio (client:portfolio format)
    - **Range Key**: AppRegex (application regex pattern)
    - **Schema Type**: Application registry with deployment configuration
    - **Billing Mode**: PAY_PER_REQUEST
    - **Client Isolation**: Each client has separate table

Application Examples:
    ```python
    # API applications pattern
    api_app = {
        "client-portfolio": "acme:web-services",
        "app-regex": "api-.*",
        "description": "REST API applications",
        "deployment_template": "kubernetes/api-template.yaml",
        "build_image": "api-builder:v1.2",
        "environment_configs": {
            "development": {
                "replicas": 1,
                "cpu": "100m",
                "memory": "256Mi",
                "env_vars": {"LOG_LEVEL": "debug"}
            },
            "staging": {
                "replicas": 2,
                "cpu": "200m",
                "memory": "512Mi",
                "env_vars": {"LOG_LEVEL": "info"}
            },
            "production": {
                "replicas": 5,
                "cpu": "500m",
                "memory": "1Gi",
                "env_vars": {"LOG_LEVEL": "warn"}
            }
        }
    }

    # Frontend applications pattern
    frontend_app = {
        "client-portfolio": "acme:web-services",
        "app-regex": "frontend-.*",
        "description": "React frontend applications",
        "deployment_template": "kubernetes/frontend-template.yaml",
        "build_image": "node:18-alpine",
        "environment_configs": {
            "staging": {
                "replicas": 2,
                "cdn_enabled": True,
                "cache_ttl": 300
            },
            "production": {
                "replicas": 4,
                "cdn_enabled": True,
                "cache_ttl": 3600
            }
        }
    }

    # Mobile backend services
    mobile_app = {
        "client-portfolio": "acme:mobile-apps",
        "app-regex": "mobile-.*",
        "description": "Mobile backend services",
        "deployment_template": "kubernetes/mobile-template.yaml",
        "build_image": "mobile-builder:v2.0",
        "environment_configs": {
            "staging": {
                "replicas": 2,
                "push_notifications": True,
                "analytics_enabled": False
            },
            "production": {
                "replicas": 6,
                "push_notifications": True,
                "analytics_enabled": True
            }
        }
    }
    ```

Regex Pattern Examples:
    ```python
    # Common application regex patterns
    patterns = {
        "api_services": "api-.*",           # Matches: api-users, api-orders, api-payments
        "web_apps": "web-.*",              # Matches: web-portal, web-dashboard, web-admin
        "mobile_services": "mobile-.*",    # Matches: mobile-api, mobile-auth, mobile-sync
        "worker_jobs": "worker-.*",        # Matches: worker-email, worker-reports, worker-cleanup
        "data_services": "data-.*",        # Matches: data-etl, data-warehouse, data-analytics
        "auth_services": "auth-.*",        # Matches: auth-service, auth-gateway, auth-provider
        "frontend_apps": "frontend-.*",    # Matches: frontend-react, frontend-vue, frontend-angular
        "microservices": "service-.*",     # Matches: service-users, service-inventory, service-billing
    }
    ```

Integration Points:
    - **Deployment Automation**: Registry patterns trigger automated deployments
    - **CI/CD Pipelines**: Application patterns determine build and deployment strategies
    - **Environment Management**: Configuration templates for different environments
    - **Resource Management**: Define resource requirements per application type
    - **Monitoring Setup**: Configure monitoring and alerting based on application patterns

Related Modules:
    - core_db.registry: Base registry system and common functionality
    - core_db.registry.actions: Base RegistryAction class with shared methods
    - core_deploy: Deployment automation consuming registry patterns
    - core_build: Build system integration with application configurations

Error Handling:
    All operations may raise:
    - BadRequestException: Invalid parameters or missing required fields
    - ConflictException: Application pattern already exists (create operations)
    - NotFoundException: Application pattern not found (get/update/delete operations)
    - UnknownException: Database connection issues or unexpected errors

Best Practices:
    - **Use descriptive regex patterns**: Make patterns specific enough to avoid conflicts
    - **Environment consistency**: Use consistent environment names across applications
    - **Template organization**: Group related applications with shared templates
    - **Resource planning**: Define appropriate resource limits for each environment
    - **Pattern testing**: Validate regex patterns match intended applications

Note:
    Application registry patterns are critical for deployment automation. Ensure regex
    patterns are specific enough to avoid unintended matches while being flexible enough
    to accommodate application naming conventions. Always test patterns before production use.
"""

from .models import AppFact
from .actions import AppActions

__all__ = ["AppFact", "AppActions"]
