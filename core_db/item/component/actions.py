"""Component item management actions for the core-automation-items DynamoDB table.

This module provides CRUD operations for component items in the Configuration Management Database (CMDB).
Component items represent the actual AWS resources deployed as part of a build, serving as the leaf nodes
in the deployment hierarchy and enabling complete infrastructure traceability.

The ComponentActions class extends ItemTableActions to provide component-specific CRUD operations
while inheriting common item management functionality.
"""

from ...response import Response
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
    def list(cls, **kwargs) -> Response:
        """List component items with optional filtering and pagination.

        Args:
            **kwargs: Query parameters including parent_prn, pagination options,
                     and time-based filtering criteria.

        Returns:
            Response: SuccessResponse containing list of component items and pagination metadata.
        """
        return super().list(record_type=ComponentItem, **kwargs)

    @classmethod
    def get(cls, **kwargs) -> Response:
        """Retrieve a specific component item by PRN.

        Args:
            **kwargs: Parameters including prn or component_prn to identify the component item.

        Returns:
            Response: SuccessResponse containing the component item data.
        """
        return super().get(record_type=ComponentItem, **kwargs)

    @classmethod
    def create(cls, **kwargs) -> Response:
        """Create a new component item in the CMDB.

        Args:
            **kwargs: Component item attributes including name, component_type, build_prn,
                     and other component-specific fields.

        Returns:
            Response: SuccessResponse containing the created component item data.
        """
        return super().create(record_type=ComponentItem, **kwargs)

    @classmethod
    def update(cls, **kwargs) -> Response:
        """Update an existing component item using PUT semantics.

        Args:
            **kwargs: Component item attributes to update, including prn to identify
                     the item and fields to modify.

        Returns:
            Response: SuccessResponse containing the updated component item data.
        """
        return super().update(record_type=ComponentItem, **kwargs)

    @classmethod
    def delete(cls, **kwargs) -> Response:
        """Delete a component item from the CMDB.

        Args:
            **kwargs: Parameters including prn or component_prn to identify the component item to delete.

        Returns:
            Response: SuccessResponse with confirmation of the deletion.
        """
        return super().delete(record_type=ComponentItem, **kwargs)
