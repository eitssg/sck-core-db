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
    """Base class for all registry fact models with consistent PascalCase serialization.

    Extends DatabaseRecord to provide uniform API behavior across all registry items.
    Inherits model_dump behavior that uses PascalCase aliases by default, matching DynamoDB
    attribute naming while allowing Python snake_case field names.

    Attributes:
        Inherits all attributes from DatabaseRecord including created_at and updated_at timestamps.

    Note:
        Uses dual naming convention: snake_case for Python code, PascalCase for APIs/DynamoDB.
        Inherits serialization with by_alias=True and exclude_none=True for consistent output.
    """

    pass
