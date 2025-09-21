"""Base registry model for consistent serialization across all registry items.

This module provides the RegistryFact base class that extends DatabaseRecord with
registry-specific serialization behavior. All registry facts (Client, Portfolio, Zone, App)
inherit from this class to ensure uniform PascalCase API output and DynamoDB compatibility.

Key Features:
    - **PascalCase Serialization**: Default API output uses PascalCase field names
    - **DynamoDB Compatibility**: Matches DynamoDB attribute naming conventions
    - **Consistent Behavior**: Uniform serialization across all registry endpoints
    - **Flexible Options**: Supports snake_case output when needed
"""

from ..models import DatabaseRecord


class RegistryFact(DatabaseRecord):

    pass
