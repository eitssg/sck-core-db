"""App item management actions for the core-automation-items DynamoDB table.

This module provides CRUD operations for app items in the Configuration Management Database (CMDB).
App items represent functional components or modules within a portfolio, serving as containers
for branches and their associated builds.

The AppActions class extends ItemTableActions to provide app-specific CRUD operations
while inheriting common item management functionality.
"""

from typing import Tuple, List

from ...models import Paginator
from ..actions import ItemTableActions

from .models import AppItem


class AppActions(ItemTableActions):
    """Convenience wrapper for app-specific CRUD operations in the CMDB.

    This class provides a type-safe interface for app item management by automatically
    injecting the AppItem type into the parent ItemTableActions methods. App items
    represent functional components or modules within a portfolio, serving as organizational
    containers for branches and their associated builds.

    All methods are convenience wrappers that delegate to the parent class with AppItem
    as the record type, ensuring type safety and reducing the chance of using incorrect item types.
    """

    @classmethod
    def list(cls, *, client: str, **kwargs) -> Tuple[List[AppItem], Paginator]:
        """List app items with optional filtering and pagination.

        Convenience method that automatically uses AppItem type.

        Args:
            **kwargs: Query parameters including:
                - client (str): Client identifier for table isolation
                - prn (str, optional): Specific app PRN to query
                - parent_prn (str, optional): Portfolio PRN to filter apps by portfolio
                - limit (int, optional): Maximum number of items to return
                - cursor (str, optional): Pagination cursor for next page
                - earliest_time (datetime, optional): Filter by creation date range
                - latest_time (datetime, optional): Filter by creation date range
                - sort_forward (bool, optional): Sort order (default: True)

        Returns:
            BaseModel: BaseModel object with structure:
                - data (List[Dict]): List of app item dictionaries, each containing:
                    - prn (str): App PRN
                    - parent_prn (str): Portfolio PRN
                    - portfolio_prn (str): Portfolio PRN (same as parent_prn)
                    - item_type (str): "app"
                    - name (str): App name
                    - contact_email (str): Contact email
                    - metadata (dict): App metadata including description, tags, etc.
                    - created_at (str): ISO timestamp
                    - updated_at (str): ISO timestamp
                - metadata (Dict): Pagination information containing:
                    - cursor (str): Cursor token for next page (if more results exist)
                    - total_count (int): Total number of items returned in this page
        """
        return super().list(AppItem, client=client, **kwargs)

    @classmethod
    def get(cls, *, client: str, **kwargs) -> AppItem:
        """Retrieve a specific app item by PRN.

        Convenience method that automatically uses AppItem type.

        Args:
            **kwargs: Parameters including:
                - client (str): Client identifier for table isolation
                - prn (str): App PRN to retrieve (e.g., "prn:ecommerce-platform:user-service")

        Returns:
            BaseModel: BaseModel object with structure:
                - data (Dict): Single app item dictionary containing:
                    - prn (str): App PRN
                    - parent_prn (str): Portfolio PRN
                    - portfolio_prn (str): Portfolio PRN (same as parent_prn)
                    - item_type (str): "app"
                    - name (str): App name
                    - contact_email (str): Contact email
                    - metadata (dict): App metadata including description, tags, etc.
                    - created_at (str): ISO timestamp
                    - updated_at (str): ISO timestamp

        Raises:
            NotFoundException: If the app item does not exist
            BadRequestException: If required parameters are missing
        """
        return super().get(AppItem, client=client, **kwargs)

    @classmethod
    def create(cls, *, client: str, **kwargs) -> AppItem:
        """Create a new app item in the CMDB.

        Convenience method that automatically uses AppItem type.

        Args:
            **kwargs: App item attributes including:
                - client (str): Client identifier for table isolation
                - portfolio (str): Portfolio name (used for PRN generation)
                - name (str): App name (used for PRN generation)
                - contact_email (str): Primary contact email for the app
                - metadata (dict, optional): Additional app information including:
                    - description (str): App description
                    - repository_url (str): Source code repository URL
                    - tags (dict): Key-value pairs for tagging
                    - Any other custom metadata fields

        Returns:
            BaseModel: BaseModel object with structure:
                - data (Dict): Created app item dictionary containing:
                    - prn (str): Generated app PRN (e.g., "prn:portfolio:app-name")
                    - parent_prn (str): Portfolio PRN this app belongs to
                    - portfolio_prn (str): Portfolio PRN (same as parent_prn)
                    - item_type (str): "app"
                    - name (str): App name
                    - contact_email (str): Contact email
                    - metadata (dict): App metadata
                    - created_at (str): ISO timestamp of creation
                    - updated_at (str): ISO timestamp of last update

        Raises:
            BadRequestException: If required fields are missing or invalid
            ConflictException: If app with same PRN already exists
        """
        return super().create(AppItem, client=client, **kwargs)

    @classmethod
    def update(cls, *, client: str, **kwargs) -> AppItem:
        """Update an existing app item using PUT semantics (full replacement).

        Convenience method that automatically uses AppItem type.

        Args:
            **kwargs: App item attributes including:
                - client (str): Client identifier for table isolation
                - prn (str): App PRN to update
                - contact_email (str): Updated contact email
                - metadata (dict, optional): Updated metadata (replaces existing)
                - Any other updatable app fields

        Returns:
            BaseModel: BaseModel object with structure:
                - data (Dict): Updated app item dictionary with all current values

        Raises:
            NotFoundException: If the app item does not exist
            BadRequestException: If required parameters are missing

        Note:
            This is a full replacement operation. All updatable fields should be provided.
            Use patch() for partial updates.
        """
        return super().update(AppItem, client=client, **kwargs)

    @classmethod
    def delete(cls, *, client: str, **kwargs) -> bool:
        """Delete an app item from the CMDB.

        Convenience method that automatically uses AppItem type.

        Args:
            **kwargs: Parameters including:
                - client (str): Client identifier for table isolation
                - prn (str): App PRN to delete

        Returns:
            BaseModel: BaseModel object with structure:
                - data (Dict): Confirmation containing deleted item information

        Raises:
            NotFoundException: If the app item does not exist
            BadRequestException: If required parameters are missing

        Warning:
            Deleting an app may affect child items (branches, builds, components).
            Ensure proper cleanup of dependent resources before deletion.
        """
        return super().delete(AppItem, client=client, **kwargs)

    @classmethod
    def patch(cls, *, client: str, **kwargs) -> AppItem:
        """Partially update an app item using PATCH semantics.

        Convenience method that automatically uses AppItem type.

        Args:
            **kwargs: App item attributes to modify including:
                - client (str): Client identifier for table isolation
                - prn (str): App PRN to update
                - contact_email (str, optional): New contact email
                - metadata (dict, optional): Metadata fields to merge/update
                - Any other updatable app fields

        Returns:
            BaseModel: BaseModel object with structure:
                - data (Dict): Updated app item dictionary with merged values

        Raises:
            NotFoundException: If the app item does not exist
            BadRequestException: If required parameters are missing

        Note:
            This performs a partial update, merging provided fields with existing data.
            Only specified fields will be updated.
        """
        return super().patch(AppItem, client=client, **kwargs)
