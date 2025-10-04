"""Component item management actions for the core-automation-items DynamoDB table.

This module provides CRUD operations for component items in the Configuration Management Database (CMDB).
Component items represent the actual AWS resources deployed as part of a build, serving as the leaf nodes
in the deployment hierarchy and enabling complete infrastructure traceability.

The ComponentActions class extends ItemTableActions to provide component-specific CRUD operations
while inheriting common item management functionality.
"""

from typing import List, Tuple

from ...models import Paginator
from ..actions import ItemTableActions
from .models import ComponentItem


class ComponentActions(ItemTableActions):
    """Implements CRUD operations for component items in the CMDB.

    This class provides component-specific item management functionality by extending
    the base ItemTableActions class. Component items represent individual AWS resources
    like EC2 instances, S3 buckets, RDS databases, Lambda functions, etc.

    All methods delegate to the parent class with ComponentItem as the record type,
    ensuring consistent behavior across all item types while maintaining
    component-specific validation and processing.
    """

    @classmethod
    def list(cls, *, client: str, **kwargs) -> Tuple[List[ComponentItem], Paginator]:
        """List component items with optional filtering and pagination.

        Args:
            **kwargs: Query parameters including parent_prn, pagination options,
                     and time-based filtering criteria.

        Returns:
            BaseModel: BaseModel object containing list of component items and pagination metadata.
        """
        return super().list(ComponentItem, client=client, **kwargs)

    @classmethod
    def get(cls, *, client: str, **kwargs) -> ComponentItem:
        """Retrieve a specific component item by PRN.

        Args:
            **kwargs: Parameters including prn or component_prn to identify the component item.

        Returns:
            BaseModel: BaseModel object containing the component item data.
        """
        return super().get(ComponentItem, client=client, **kwargs)

    @classmethod
    def create(cls, *, client: str, **kwargs) -> ComponentItem:
        """Create a new component item in the CMDB.

        Args:
            **kwargs: Component item attributes including name, component_type, build_prn,
                     and other component-specific fields.

        Returns:
            BaseModel: BaseModel object containing the created component item data.
        """
        return super().create(ComponentItem, client=client, **kwargs)

    @classmethod
    def patch(cls, *, client: str, **kwargs) -> ComponentItem:
        """Update an existing component item using PATCH semantics.

        Args:
            **kwargs: Component item attributes to update, including prn to identify
                     the item and fields to modify.

        Returns:
            BaseModel: BaseModel object containing the updated component item data.
        """
        return super().patch(ComponentItem, client=client, **kwargs)

    @classmethod
    def update(cls, *, client: str, **kwargs) -> ComponentItem:
        """Update an existing component item using PUT semantics.

        Args:
            **kwargs: Component item attributes to update, including prn to identify
                     the item and fields to modify.

        Returns:
            BaseModel: BaseModel object containing the updated component item data.
        """
        return super().update(ComponentItem, client=client, **kwargs)

    @classmethod
    def delete(cls, *, client: str, **kwargs) -> bool:
        """Delete a component item from the CMDB.

        Args:
            **kwargs: Parameters including prn or component_prn to identify the component item to delete.

        Returns:
            BaseModel: BaseModel object with structure:
                - data (Dict): Deletion confirmation dictionary
        """
        return super().delete(ComponentItem, client=client, **kwargs)
