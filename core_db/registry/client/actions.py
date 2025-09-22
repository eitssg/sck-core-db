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

from typing import List, Tuple
from pydantic import ValidationError
from pynamodb.exceptions import (
    DoesNotExist,
    PutError,
    DeleteError,
    ScanError,
    UpdateError,
)
from pynamodb.expressions.update import Action

import core_logging as log

from core_framework.time_utils import make_default_time

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

    @classmethod
    def list(cls, *, client_id: str | None = None, **kwargs) -> Tuple[list[ClientFact], Paginator]:

        if client_id:
            return cls._list_by_client_id(client_id, **kwargs)
        else:
            return cls._list_all_clients(**kwargs)

    @classmethod
    def _list_all_clients(cls, **kwargs) -> Tuple[List[ClientFact], Paginator]:

        try:
            # load the search parameters into a Paginator instance
            paginator = Paginator(**kwargs)
        except Exception as e:
            raise BadRequestException(f"Invalid pagination parameters: {str(e)}") from e

        model_class = ClientFact.model_class()

        try:

            results = model_class.scan(**paginator.get_scan_args())

            # Convert PynamoDB items to ClientFact instances and then into dicts for the response
            data = [ClientFact.from_model(item) for item in results]

            paginator.last_evaluated_key = getattr(results, "last_evaluated_key", None)
            paginator.total_count = len(data)

            return data, paginator

        except ScanError as e:
            raise UnknownException(f"Failed to list clients: {str(e)}") from e
        except Exception as e:
            raise UnknownException(f"Unexpected error while listing clients: {str(e)}") from e

    @classmethod
    def _list_by_client_id(cls, client_id: str, **kwargs) -> Tuple[List[ClientFact], Paginator]:

        try:
            # load the search parameters into a Paginator instance
            paginator = Paginator(**kwargs)
        except Exception as e:
            raise BadRequestException(f"Invalid pagination parameters: {str(e)}") from e

        model_class = ClientFact.model_class()

        try:
            # Retrieve the client item from the database
            items = model_class.scan(
                filter_condition=(model_class.client_id == client_id),
                **paginator.get_scan_args(),
            )

            # Validate and convert PynamoDB item to ClientFact instance
            return [ClientFact.from_model(item) for item in items], paginator

        except ScanError as e:
            if "ResourceNotFoundException" in str(e):
                raise NotFoundException(f"Client with client_id '{client_id}' not found") from e

            log.error(f"GetError while retrieving client by client_id '{client_id}': {str(e)}")
            raise UnknownException(f"Failed to retrieve client '{client_id}'") from e

        except Exception as e:
            log.error(f"Error while retrieving client by client_id '{client_id}': {str(e)}")
            raise UnknownException(f"Failed to retrieve client '{client_id}'") from e

    @classmethod
    def get(cls, client: str) -> ClientFact:

        if not client:
            raise BadRequestException("Client identifier is required to load ClientFact")

        model_class = ClientFact.model_class()

        try:

            item = model_class.get(client)

            return ClientFact.from_model(item)

        except DoesNotExist:
            raise NotFoundException(f"Client '{client}' not found")

        except Exception as e:
            raise UnknownException(f"Failed to retrieve client '{client}'") from e

    @classmethod
    def create(cls, *, record: ClientFact | None = None, **kwargs) -> ClientFact:

        model_class = ClientFact.model_class()

        try:
            if not record:
                record = ClientFact(**kwargs)

        except Exception as e:
            raise BadRequestException(f"Invalid Client Record {str(e)}") from e

        try:

            item = record.to_model()
            item.save(model_class.client.does_not_exist())

            return record

        except PutError as e:
            raise ConflictException(f"Client '{record.client}' already exists") from e
        except Exception as e:
            raise UnknownException(f"Failed to create client '{record.client}'") from e

    @classmethod
    def update(cls, *, record: ClientFact | None = None, **kwargs) -> ClientFact:
        return cls._update(remove_none=True, record=record, **kwargs)

    @classmethod
    def patch(cls, *, remove_none: bool = False, **kwargs) -> ClientFact:
        return cls._update(remove_none=remove_none, **kwargs)

    @classmethod
    def delete(cls, *, client: str) -> bool:
        if not client:
            raise ValueError("Client identifier is required to delete ClientFact")

        model_class = ClientFact.model_class()

        try:

            item = model_class(client)
            item.delete(condition=model_class.client.exists())

            return True

        except DeleteError as e:
            if "ConditionalCheckFailedException" in str(e):
                raise NotFoundException(f"Client '{client}' not found") from e
            raise UnknownException(f"Failed to delete client '{client}'") from e

        except Exception as e:
            raise UnknownException(f"Failed to delete client '{client}': {str(e)}") from e

    @classmethod
    def _update(cls, *, remove_none: bool, record: ClientFact | None = None, **kwargs) -> ClientFact:

        excluded_fields = {"client", "created_at", "updated_at"}

        if record:
            client = record.client
            values = record.model_dump(by_alias=False, exclude_none=False)
        else:
            client = kwargs.get("client")
            values = {k: v for k, v in kwargs.items() if k not in excluded_fields}

        if not client:
            raise BadRequestException("Client identifier is required to update")

        model_class = ClientFact.model_class()

        try:

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

            return ClientFact.from_model(item)

        except (ValueError, ValidationError) as e:
            raise BadRequestException(f"Invalid client data: {str(e)}") from e

        except UpdateError as e:
            if "ConditionalCheckFailedException" in str(e):
                raise NotFoundException(f"Client '{client}' not found") from e
            raise UnknownException(f"Failed to update client '{client}': {str(e)}") from e

        except Exception as e:
            raise UnknownException(f"Failed to update client '{client}': {str(e)}") from e
