"""Registry action interface for specialized registry table operations.

This module provides the RegistryAction base class that extends TableActions with
registry-specific functionality. Registry tables store configuration and metadata
for the Core Automation platform (clients, portfolios, zones, apps) and require
specialized handling for client isolation and hierarchical data management.

Key Features:
    - **Client-Specific Tables**: Separate registry tables per client for data isolation
    - **Hierarchical Structure**: Client -> Portfolio -> Zone -> App relationships
    - **Factory Pattern**: Uses factory classes for client-specific table models
    - **Registry Patterns**: Common operations for configuration and metadata tables
"""

from ..actions import TableActions


class RegistryAction(TableActions):
    """Registry-specific action interface extending TableActions for registry table operations.

    This class provides a specialized interface for registry tables (clients, portfolios, zones, apps)
    that inherit common CRUD operations from TableActions while allowing for registry-specific
    customizations and behaviors.

    Registry tables store configuration and metadata for the Core Automation platform,
    including client organizations, portfolio definitions, zone configurations, and application
    specifications. This class serves as the base for all registry-specific action implementations.

    Key Registry Features:
        - **Client-Specific Tables**: Each client has separate registry tables for data isolation
        - **Hierarchical Structure**: Client -> Portfolio -> Zone -> App -> Branch -> Build -> Component
        - **Factory Pattern**: Uses factory classes to get client-specific table models
        - **Dual Naming**: Supports both snake_case (Python) and PascalCase (API/DynamoDB) field names
        - **Access Control**: Client-scoped access with role-based permissions
        - **Audit Tracking**: Automatic created_at/updated_at timestamps
    """

    def __repr__(self) -> str:
        """Return string representation of RegistryAction.

        Returns:
            str: String representation showing class name and client
        """
        client = getattr(self, "client", "unknown")
        return f"<{self.__class__.__name__}(client={client})>"
