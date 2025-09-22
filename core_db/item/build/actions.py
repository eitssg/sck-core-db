"""Build item management actions for the core-automation-items DynamoDB table.

This module provides CRUD operations for build items in the Configuration Management Database (CMDB).
Build items represent specific infrastructure deployment instances within branches, tracking the
deployment lifecycle from initiation to completion.

The BuildActions class extends ItemTableActions to provide build-specific CRUD operations
while inheriting common item management functionality.
"""

from typing import List, Tuple

from ...models import Paginator
from ..actions import ItemTableActions
from .models import BuildItem


class BuildActions(ItemTableActions):
    """Implements CRUD operations for build items in the CMDB.

    This class provides build-specific item management functionality by extending
    the base ItemTableActions class. Build items represent deployment instances
    within branches and serve as containers for AWS components.

    All methods delegate to the parent class with BuildItem as the record type,
    ensuring consistent behavior across all item types while maintaining
    build-specific validation and processing.
    """

    @classmethod
    def list(cls, *, client: str, **kwargs) -> Tuple[List[BuildItem], Paginator]:
        """List build items with optional filtering and pagination.

        Args:
            **kwargs: Query parameters including parent_prn, pagination options,
                     and time-based filtering criteria.

        Returns:
            Tuple containing list of build items and pagination metadata.
        """
        return super().list(BuildItem, client=client, **kwargs)

    @classmethod
    def get(cls, *, client: str, **kwargs) -> BuildItem:
        """Retrieve a specific build item by PRN.

        Args:
            **kwargs: Parameters including prn or build_prn to identify the build item.

        Returns:
            BuildItem containing the build item data.
        """
        return super().get(BuildItem, client=client, **kwargs)

    @classmethod
    def create(cls, *, client: str, **kwargs) -> BuildItem:
        """Create a new build item in the CMDB.

        Args:
            **kwargs: Build item attributes including name, status, branch_prn,
                     and other build-specific fields.

        Returns:
            BuildItem containing the created build item data.
        """
        return super().create(BuildItem, client=client, **kwargs)

    @classmethod
    def update(cls, *, client: str, **kwargs) -> BuildItem:
        """Update an existing build item using PUT semantics.

        Args:
            **kwargs: Build item attributes to update, including prn to identify
                     the item and fields to modify.

        Returns:
            BuildItem containing the updated build item data.
        """
        return super().update(BuildItem, client=client, **kwargs)

    @classmethod
    def delete(cls, *, client: str, **kwargs) -> bool:
        """Delete a build item from the CMDB.

        Args:
            **kwargs: Parameters including prn or build_prn to identify the build item to delete.

        Returns:
            bool with confirmation of the deletion.
        """
        return super().delete(BuildItem, client=client, **kwargs)
