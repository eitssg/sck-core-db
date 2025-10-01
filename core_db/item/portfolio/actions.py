"""Portfolio item management actions for the core-automation-items DynamoDB table.

This module provides CRUD operations for portfolio items in the Configuration Management Database (CMDB).
Portfolio items represent the highest level organizational units, serving as containers for applications
and their associated infrastructure in the deployment hierarchy.

The PortfolioActions class extends ItemTableActions to provide portfolio-specific CRUD operations
while inheriting common item management functionality.
"""

from typing import List, Tuple, Type

from core_db.models import Paginator

from ..actions import ItemTableActions
from .models import PortfolioItem


class PortfolioActions(ItemTableActions):
    """Convenience wrapper for portfolio-specific CRUD operations in the CMDB.

    This class provides a type-safe interface for portfolio item management by automatically
    injecting the PortfolioItem type into the parent ItemTableActions methods. Portfolio items
    represent top-level organizational units that contain applications and their infrastructure.

    All methods are convenience wrappers that delegate to the parent class with PortfolioItem
    as the record type, ensuring type safety and reducing the chance of using incorrect item types.
    """

    @classmethod
    def list(cls, *, client: str, **kwargs) -> Tuple[List[PortfolioItem], Paginator]:
        """List portfolio items with optional filtering and pagination.

        Convenience method that automatically uses PortfolioItem type.

        Args:
            **kwargs: Query parameters including:
                - client (str): Client identifier for table isolation
                - prn (str, optional): Specific portfolio PRN to query
                - parent_prn (str, optional): Parent PRN for hierarchical queries
                - limit (int, optional): Maximum number of items to return
                - cursor (str, optional): Pagination cursor for next page
                - earliest_time (datetime, optional): Filter by creation date range
                - latest_time (datetime, optional): Filter by creation date range
                - sort_forward (bool, optional): Sort order (default: True)

        Returns:
            BaseModel: BaseModel object with structure:
                - data (List[Dict]): List of portfolio item dictionaries, each containing:
                    - prn (str): Portfolio PRN
                    - parent_prn (str): Parent PRN (same as prn for top-level items)
                    - item_type (str): "portfolio"
                    - name (str): Portfolio name
                    - contact_email (str): Contact email
                    - metadata (dict): Portfolio metadata including description, tags, etc.
                    - created_at (str): ISO timestamp
                    - updated_at (str): ISO timestamp
                - metadata (Dict): Pagination information containing:
                    - cursor (str): Cursor token for next page (if more results exist)
                    - total_count (int): Total number of items returned in this page
        """
        return super().list(PortfolioItem, client=client, **kwargs)

    @classmethod
    def get(cls, *, client: str, **kwargs) -> PortfolioItem:
        """Retrieve a specific portfolio item by PRN.

        Convenience method that automatically uses PortfolioItem type.

        Args:
            **kwargs: Parameters including:
                - client (str): Client identifier for table isolation
                - prn (str): Portfolio PRN to retrieve (e.g., "prn:ecommerce-platform")

        Returns:
            BaseModel: BaseModel object with structure:
                - data (Dict): Single portfolio item dictionary containing:
                    - prn (str): Portfolio PRN
                    - parent_prn (str): Parent PRN (same as prn for top-level items)
                    - item_type (str): "portfolio"
                    - name (str): Portfolio name
                    - contact_email (str): Contact email
                    - metadata (dict): Portfolio metadata including description, tags, etc.
                    - created_at (str): ISO timestamp
                    - updated_at (str): ISO timestamp

        Raises:
            NotFoundException: If the portfolio item does not exist
            BadRequestException: If required parameters are missing
        """
        return super().get(PortfolioItem, client=client, **kwargs)

    @classmethod
    def create(cls, *, client: str, **kwargs) -> PortfolioItem:
        """Create a new portfolio item in the CMDB.

        Convenience method that automatically uses PortfolioItem type.

        Args:
            **kwargs: Portfolio item attributes including:
                - client (str): Client identifier for table isolation
                - name (str): Portfolio name (used for PRN generation)
                - contact_email (str): Primary contact email for the portfolio
                - metadata (dict, optional): Additional portfolio information including:
                    - description (str): Portfolio description
                    - tags (dict): Key-value pairs for tagging
                    - Any other custom metadata fields

        Returns:
            BaseModel: BaseModel object with structure:
                - data (Dict): Created portfolio item dictionary containing:
                    - prn (str): Generated portfolio PRN
                    - parent_prn (str): Parent PRN (same as prn for top-level items)
                    - item_type (str): "portfolio"
                    - name (str): Portfolio name
                    - contact_email (str): Contact email
                    - metadata (dict): Portfolio metadata
                    - created_at (str): ISO timestamp of creation
                    - updated_at (str): ISO timestamp of last update

        Raises:
            BadRequestException: If required fields are missing or invalid
            ConflictException: If portfolio with same PRN already exists
        """
        return super().create(PortfolioItem, client=client, **kwargs)

    @classmethod
    def update(cls, *, client: str, **kwargs) -> PortfolioItem:
        """Update an existing portfolio item using PUT semantics (full replacement).

        Convenience method that automatically uses PortfolioItem type.

        Args:
            **kwargs: Portfolio item attributes including:
                - client (str): Client identifier for table isolation
                - prn (str): Portfolio PRN to update
                - contact_email (str): Updated contact email
                - metadata (dict, optional): Updated metadata (replaces existing)
                - Any other updatable portfolio fields

        Returns:
            BaseModel: BaseModel object with structure:
                - data (Dict): Updated portfolio item dictionary with all current values

        Raises:
            NotFoundException: If the portfolio item does not exist
            BadRequestException: If required parameters are missing

        Note:
            This is a full replacement operation. All updatable fields should be provided.
            Use patch() for partial updates.
        """
        return super().update(PortfolioItem, client=client, **kwargs)

    @classmethod
    def delete(cls, *, client: str, **kwargs) -> bool:
        """Delete a portfolio item from the CMDB.

        Convenience method that automatically uses PortfolioItem type.

        Args:
            **kwargs: Parameters including:
                - client (str): Client identifier for table isolation
                - prn (str): Portfolio PRN to delete

        Returns:
            BaseModel: BaseModel object with structure:
                - data (Dict): Confirmation containing deleted item information

        Raises:
            NotFoundException: If the portfolio item does not exist
            BadRequestException: If required parameters are missing

        Warning:
            Deleting a portfolio may affect child items (apps, branches, builds, components).
            Ensure proper cleanup of dependent resources before deletion.
        """
        return super().delete(PortfolioItem, client=client, **kwargs)

    @classmethod
    def patch(cls, *, client: str, **kwargs) -> PortfolioItem:
        """Partially update a portfolio item using PATCH semantics.

        Convenience method that automatically uses PortfolioItem type.

        Args:
            **kwargs: Portfolio item attributes to modify including:
                - client (str): Client identifier for table isolation
                - prn (str): Portfolio PRN to update
                - contact_email (str, optional): New contact email
                - metadata (dict, optional): Metadata fields to merge/update
                - Any other updatable portfolio fields

        Returns:
            BaseModel: BaseModel object with structure:
                - data (Dict): Updated portfolio item dictionary with merged values

        Raises:
            NotFoundException: If the portfolio item does not exist
            BadRequestException: If required parameters are missing

        Note:
            This performs a partial update, merging provided fields with existing data.
            Only specified fields will be updated.
        """
        return super().patch(PortfolioItem, client=client, **kwargs)
