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

    def __repr__(self) -> str:
        client = getattr(self, "client", "unknown")
        return f"<{self.__class__.__name__}(client={client})>"
