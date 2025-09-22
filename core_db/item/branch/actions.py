"""Branch item management actions for the core-automation-items DynamoDB table.

This module provides CRUD operations for branch items in the Configuration Management Database (CMDB).
Branch items represent version control branches within applications, serving as containers for builds
and their associated infrastructure deployments.

The BranchActions class extends ItemTableActions to provide branch-specific CRUD operations
while inheriting common item management functionality.
"""

from ..actions import ItemTableActions
from .models import BranchItem


class BranchActions(ItemTableActions):
    """Implements CRUD operations for branch items in the CMDB.

    This class provides branch-specific item management functionality by extending
    the base ItemTableActions class. Branch items represent version control branches
    within applications and serve as organizational containers for builds.

    All methods delegate to the parent class with BranchItem as the record type,
    ensuring consistent behavior across all item types while maintaining
    branch-specific validation and processing.
    """

    @classmethod
    def list(cls, **kwargs):
        """List branch items with optional filtering and pagination.

        Args:
            **kwargs: Query parameters including parent_prn, pagination options,
                     and time-based filtering criteria.

        Returns:
            BaseModel: BaseModel object with structure:
                - data (List[Dict]): List of branch item dictionaries
                - metadata (Dict): Pagination information with cursor and total_count
        """
        return super().list(record_type=BranchItem, **kwargs)

    @classmethod
    def get(cls, **kwargs):
        """Retrieve a specific branch item by PRN.

        Args:
            **kwargs: Parameters including prn or branch_prn to identify the branch item.

        Returns:
            BaseModel: BaseModel object with structure:
                - data (Dict): Single branch item dictionary
        """
        return super().get(record_type=BranchItem, **kwargs)

    @classmethod
    def create(cls, **kwargs):
        """Create a new branch item in the CMDB.

        Args:
            **kwargs: Branch item attributes including name, app_prn,
                     and other branch-specific fields.

        Returns:
            BaseModel: BaseModel object with structure:
                - data (Dict): Created branch item dictionary
        """
        return super().create(record_type=BranchItem, **kwargs)

    @classmethod
    def update(cls, **kwargs):
        """Update an existing branch item using PUT semantics.

        Args:
            **kwargs: Branch item attributes to update, including prn to identify
                     the item and fields to modify.

        Returns:
            BaseModel: BaseModel object with structure:
                - data (Dict): Updated branch item dictionary
        """
        return super().update(record_type=BranchItem, **kwargs)

    @classmethod
    def delete(cls, **kwargs):
        """Delete a branch item from the CMDB.

        Args:
            **kwargs: Parameters including prn or branch_prn to identify the branch item to delete.

        Returns:
            BaseModel: BaseModel object with structure:
                - data (Dict): Deletion confirmation dictionary
        """
        return super().delete(record_type=BranchItem, **kwargs)

    @classmethod
    def patch(cls, **kwargs):
        """Partially update a branch item using PATCH semantics.

        Args:
            **kwargs: Branch item attributes to modify, including prn to identify
                     the item and specific fields to update.

        Returns:
            BaseModel: BaseModel object with structure:
                - data (Dict): Updated branch item dictionary
        """
        return super().patch(record_type=BranchItem, **kwargs)
