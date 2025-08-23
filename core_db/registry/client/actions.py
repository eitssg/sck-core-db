"""Client registry actions for the core-automation-clients DynamoDB table.

This module provides comprehensive CRUD operations for client management within the registry
system. Clients represent top-level organizational entities that contain portfolios and
applications, with proper isolation and validation throughout all operations.

Key Features:
    - **Client Management**: Complete client lifecycle management with metadata
    - **Global Table Operations**: Uses global registry table for client-wide data
    - **Client Isolation**: Ensures proper tenant separation between clients
    - **Comprehensive Error Handling**: Detailed exception mapping for different failure scenarios
    - **Flexible Parameter Handling**: Supports various client identifier formats
"""

from typing import Any, Dict
from pydantic import ValidationError
from pynamodb.exceptions import (
    DoesNotExist,
    PutError,
    DeleteError,
    ScanError,
    GetError,
    UpdateError,
)
from pynamodb.expressions.update import Action

import core_framework as util
from core_framework.time_utils import make_default_time

from ...response import Response, SuccessResponse
from ...models import Paginator
from ...exceptions import (
    ConflictException,
    NotFoundException,
    BadRequestException,
    UnknownException,
)
from ..actions import RegistryAction
from .models import ClientFact


class ClientActions(RegistryAction):
    """Actions for managing client records in the registry.

    Provides comprehensive CRUD operations for client management with proper error handling
    and validation. Clients represent top-level organizational entities within the registry
    system and are stored in a global table for system-wide access.

    The class handles client lifecycle operations including creation, retrieval, updates,
    and deletion with appropriate isolation and validation for multi-tenant environments.
    """

    @classmethod
    def list(cls, **kwargs) -> Response:
        """List all client records with complete metadata.

        Args:
            **kwargs: Optional parameters for filtering and pagination.

        Returns:
            Response: SuccessResponse containing list of client records and pagination metadata.
        """
        client = kwargs.get("client") or kwargs.get("Client")

        if not client:
            raise BadRequestException("Client identifier is required to load ClientFact")

        model_class = ClientFact.model_class(client)

        try:
            # load the search parameters into a Paginator instance
            paginator = Paginator(**kwargs)
        except (ValueError, ValidationError) as e:
            raise BadRequestException(f"Invalid pagination parameters: {str(e)}") from e

        try:
            scan_kwargs: Dict[str, Any] = {
                "limit": paginator.limit if paginator.limit else None,
            }

            if paginator.cursor:
                scan_kwargs["last_evaluated_key"] = paginator.cursor

            results = model_class.scan(**scan_kwargs)

            # Convert PynamoDB items to ClientFact instances and then into dicts for the response
            data = [ClientFact.from_model(item).model_dump(mode="json") for item in results]

            paginator.total_count = getattr(results, "total_count", len(data))
            paginator.cursor = getattr(results, "last_evaluated_key", None)

            return SuccessResponse(data=data, metadata=paginator.get_metadata())
        except ScanError as e:
            raise UnknownException(f"Failed to list clients: {str(e)}") from e
        except Exception as e:
            raise UnknownException(f"Unexpected error while listing clients: {str(e)}") from e

    @classmethod
    def get(cls, **kwargs) -> Response:
        """Retrieve a specific client record.

        Args:
            **kwargs: Parameters including client identifier.

        Returns:
            Response: SuccessResponse containing the client data.
        """
        client = kwargs.get("client") or kwargs.get("Client")
        client_id = kwargs.get("client_id") or kwargs.get("ClientId")

        if not client and not client_id:
            raise BadRequestException("Client identifier is required to load ClientFact")

        if client_id:
            return cls._lookup_by_client_id(client_id)
        else:
            return cls._lookup_by_client(client)

    @classmethod
    def _lookup_by_client(cls, client: str) -> ClientFact | None:

        model_class = ClientFact.model_class("global")

        try:
            # Retrieve the client item from the database
            item = model_class.get(client)
            # Validate and convert PynamoDB item to ClientFact instance
            data = ClientFact.from_model(item).model_dump(mode="json")

            return SuccessResponse(data=data)
        except DoesNotExist:
            raise NotFoundException(f"Client '{client}' not found")
        except Exception as e:
            raise UnknownException(f"Failed to retrieve client '{client}'") from e

    @classmethod
    def _lookup_by_client_id(cls, client_id: str) -> ClientFact | None:

        model_class = ClientFact.model_class("global")

        try:
            # Retrieve the client item from the database
            item = model_class.scan(filter_condition=(model_class.client_id == client_id)).next()

            # Validate and convert PynamoDB item to ClientFact instance
            data = ClientFact.from_model(item).model_dump(mode="json")

            return SuccessResponse(data=data)
        except GetError as e:
            raise UnknownException(f"Failed to retrieve client '{client_id}'") from e
        except Exception as e:
            raise UnknownException(f"Failed to retrieve client '{client_id}'") from e

    @classmethod
    def create(cls, **kwargs) -> Response:
        """Create a new client record.

        Args:
            **kwargs: Client attributes including client identifier and configuration.

        Returns:
            Response: SuccessResponse containing the created client data.
        """

        client = kwargs.get("client") or kwargs.get("Client")
        if not client:
            raise BadRequestException("Client identifier is required to create ClientFact")

        model_class = ClientFact.model_class(client)

        try:

            # Validate and prepare data for creation
            data = ClientFact(**kwargs)
            # Create pynademoDB item
            item = data.to_model(model_class)
            # Save the item to the database
            item.save(model_class.client.does_not_exist())

            return SuccessResponse(data=data.model_dump(mode="json"))
        except PutError as e:
            raise ConflictException(f"Client '{client}' already exists") from e
        except Exception as e:
            raise UnknownException(f"Failed to create client '{client}'") from e

    @classmethod
    def update(cls, **kwargs) -> Response:
        """Create or completely replace a client record using PUT semantics.

        Args:
            **kwargs: Complete client configuration parameters.

        Returns:
            Response: SuccessResponse containing the updated client data.
        """
        return cls._update(True, **kwargs)

    @classmethod
    def patch(cls, **kwargs) -> Response:
        """Partially update specific fields of a client record using PATCH semantics.

        Args:
            **kwargs: Partial client update parameters.

        Returns:
            Response: SuccessResponse containing the complete updated client data.
        """
        return cls._update(False, **kwargs)

    @classmethod
    def delete(cls, **kwargs) -> Response:
        """Delete a client record.

        Args:
            **kwargs: Parameters including client identifier to delete.

        Returns:
            Response: SuccessResponse with deletion confirmation.
        """

        client = kwargs.get("client") or kwargs.get("Client")

        if not client:
            raise ValueError("Client identifier is required to delete ClientFact")

        model_class = ClientFact.model_class(client)

        try:
            item = model_class.get(client)
            item.delete()
            return SuccessResponse(message=f"Client {client} deleted")
        except DeleteError as e:
            raise UnknownException(f"Failed to delete client '{client}'") from e
        except Exception as e:
            raise UnknownException(f"Failed to delete client '{client}': {str(e)}") from e

    @classmethod
    def _update(cls, remove_none: bool = True, **kwargs) -> Response:
        """Update a client record with new attributes using atomic operations.

        Args:
            remove_none (bool): Whether to remove attributes with None values from the database

        Returns:
            Response: SuccessResponse containing the updated client data.

        Raises:
            BadRequestException: If client identifier is missing or validation fails
            NotFoundException: If the client record is not found in the database
            UnknownException: If database update operation fails
        """
        client = kwargs.get("client") or kwargs.get("Client")

        if not client:
            raise BadRequestException("Client identifier is required to update")

        try:
            if remove_none:
                # Full validation for PUT semantics
                data = ClientFact(**kwargs)
            else:
                # Skip validation for PATCH semantics (allow partial data)
                data = ClientFact.model_construct(**kwargs)
        except (ValueError, ValidationError) as e:
            raise BadRequestException(f"Invalid client data: {str(e)}") from e

        model_class = ClientFact.model_class(client)

        excluded_fields = {"client", "created_at", "updated_at"}

        try:
            values = data.model_dump(by_alias=False, exclude_none=False, exclude=excluded_fields)

            attributes = model_class.get_attributes()

            actions: list[Action] = []
            for key, value in values.items():
                if key in excluded_fields:
                    continue

                if key in attributes:
                    attr = attributes[key]

                    if value is None:
                        if remove_none:
                            # Remove field from database when None and remove_none=True
                            actions.append(attr.remove())
                        # Skip None values when remove_none=False (PATCH semantics)
                    else:
                        actions.append(attr.set(value))

            actions.append(model_class.updated_at.set(make_default_time()))

            item = model_class(client)
            item.update(actions=actions, condition=model_class.client.exists())
            item.refresh()

            data = ClientFact.from_model(item).model_dump(mode="json")

            return SuccessResponse(data=data)

        except UpdateError as e:
            if "ConditionalCheckFailedException" in str(e):
                raise NotFoundException(f"Client '{client}' not found") from e
            raise UnknownException(f"Failed to update client '{client}': {str(e)}") from e
        except Exception as e:
            raise UnknownException(f"Failed to update client '{client}': {str(e)}") from e
