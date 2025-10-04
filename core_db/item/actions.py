"""Generic CRUD operations for the core-automation-items DynamoDB table.

This module defines the base TableActions implementation for the Items table,
providing generic list, get, create, update, and delete methods that work across
all item types (portfolio, app, branch, build, component). These actions serve
as the foundation for schema-specific operations in subclassed modules.

Key Components:
    - **ItemTableActions**: Generic CRUD operations with validation and business logic
    - **PRN validation**: Primary Resource Name format validation for all item types
    - **Date validation**: ISO8601 datetime validation and conversion utilities
    - **Pagination support**: Cursor-based pagination for large result sets

Features:
    - **Type-agnostic operations**: Works with any item type in the deployment hierarchy
    - **Conditional writes**: Prevents duplicate item creation with existence checks
    - **Automatic timestamps**: Manages created_at and updated_at fields automatically
    - **Range queries**: Supports time-based filtering with earliest/latest parameters
    - **Partial updates**: Efficient field-level updates with remove operations
    - **Error handling**: Comprehensive exception mapping for different failure scenarios

Usage Patterns:
    This module provides the base functionality that gets specialized by:
    - core_db.item.portfolio: Portfolio-specific operations
    - core_db.item.app: Application-specific operations
    - core_db.item.branch: Branch-specific operations
    - core_db.item.build: Build-specific operations
    - core_db.item.component: Component-specific operations
"""

from typing import List, Tuple, Type
from datetime import datetime

import core_logging as log

from core_framework.time_utils import make_default_time

from pynamodb.expressions.update import Action
from pynamodb.exceptions import (
    DoesNotExist,
    PutError,
    UpdateError,
    DeleteError,
    GetError,
    QueryError,
    ScanError,
)
from ..actions import TableActions

from ..models import Paginator
from .models import ItemModel, ItemModelRecordType


from ..exceptions import (
    BadRequestException,  # http 400
    NotFoundException,  # http 404
    ConflictException,  # http 409
    UnknownException,  # http 500
)


class ItemTableActions(TableActions):
    """Generic CRUD operations for the core-automation-items DynamoDB table.

    This class provides the base implementation of TableActions for the Items table,
    supporting all item types in the deployment hierarchy (portfolio, app, branch,
    build, component). It handles common operations like validation, pagination,
    and automatic timestamp management.

    The class is designed to be subclassed by type-specific action classes that
    add validation and business logic specific to each item type.
    """

    @classmethod
    def create(
        cls, record_type: Type[ItemModelRecordType], *, client: str, record: ItemModelRecordType | None = None, **kwargs
    ) -> ItemModelRecordType:
        """Create a new item in the items table.

        Args:
            record_type: The specific ItemModelRecord subclass to create
            **kwargs: Item attributes including prn, name, and type-specific fields

        Returns:
            BaseModel: BaseModel object containing the created item data

        Raises:
            BadRequestException: If required fields are missing or invalid
            ConflictException: If item already exists with the same PRN
            UnknownException: If database operation fails
        """
        if not client:
            raise BadRequestException("Client is required for item creation")

        try:
            if record is None:
                record = record_type(**kwargs)

            item: ItemModel = record.to_model(client)
            item.save(type(item).prn.does_not_exist())

            return record

        except ValueError as e:
            raise BadRequestException(f"Invalid item data: {e}")

        except PutError as e:
            if "ConditionalCheckFailedException" in str(e):
                raise ConflictException(f"Item already exists with PRN: {kwargs.get('prn')}")

            raise UnknownException("Database operation failed while creating item") from e

        except Exception as e:
            log.error("Database operation failed", error=str(e), details=kwargs)
            raise UnknownException("Database operation failed") from e

    @classmethod
    def delete(
        cls, record_type: Type[ItemModelRecordType], *, client: str, parent_prn: str | None = None, prn: str | None = None, **kwargs
    ) -> bool:
        """Delete an item from the items table.

        Deletes the specified item if it exists. If the item is not found,
        returns a success response rather than an error (idempotent operation).

        If you specify the prn parameter, parent_prn is ignored as parent_prn is derived from prn.

        Args:
            record_type: The specific ItemModelRecord subclass to delete
            **kwargs: Delete parameters including prn (required)

        Returns:
            BaseModel: BaseModel object with confirmation message

        Raises:
            BadRequestException: If the PRN is missing or has invalid format
            NotFoundException: If item doesn't exist
            UnknownException: If database operation fails

        Note:
            This operation does not automatically delete child items. Consider
            cascading effects when deleting items that may have children in
            the deployment hierarchy.
        """
        log.debug("Received delete request:", details=kwargs)

        if not client:
            raise BadRequestException("Client is required for item deletion")

        try:

            model_class = record_type.model_class(client)

            if prn:
                # Delete the specific item with the given prn
                parent_prn = record_type.get_parent_prn(prn)

                item = model_class(parent_prn=parent_prn, prn=prn)
                item.delete(condition=model_class.prn.exists())

                return True

            elif parent_prn:
                # Delete all items with the given parent_prn
                query = model_class.query(parent_prn)
                for item in query:
                    item.delete()

                return True

            else:
                raise BadRequestException("Either parent_prn or prn is required for item deletion")

        except ValueError as e:
            raise BadRequestException(f"Invalid item data: {e}")

        except DeleteError as e:
            if "ConditionalCheckFailedException" in str(e):
                raise NotFoundException(f"Item not found for deletion: {prn}")

            raise UnknownException("Database operation failed while deleting item") from e

        except DoesNotExist as e:
            raise NotFoundException(f"Item not found for deletion: {prn}") from e

        except Exception as e:
            log.error("Database operation failed", error=str(e), details=kwargs)
            raise UnknownException("Database operation failed") from e

    @classmethod
    def get(cls, record_type: Type[ItemModelRecordType], *, client: str, prn: str, **kwargs) -> ItemModelRecordType:
        """Retrieve a single item from the items table by PRN.

        Fetches the item with the specified Primary Resource Name and returns
        its complete data as a dictionary.

        Args:
            record_type: The specific ItemModelRecord subclass to retrieve
            **kwargs: Get parameters including prn (required)

        Returns:
            BaseModel: BaseModel object containing the item data

        Raises:
            BadRequestException: If the PRN is missing or has invalid format
            NotFoundException: If no item exists with the specified PRN
            UnknownException: If database operation fails
        """
        log.debug("Received get request:", details=kwargs)

        if not client:
            raise BadRequestException("Client is required for item retrieval")

        if not prn:
            raise BadRequestException("PRN is required for item retrieval")

        model_class = record_type.model_class(client)

        try:
            parent_prn = record_type.get_parent_prn(prn)

            item = model_class.get(hash_key=parent_prn, range_key=prn)

            data: ItemModelRecordType = record_type.from_model(item)  # type: ignore[call-arg]

            return data

        except ValueError as e:
            raise BadRequestException(f"Invalid item data: {e}")
        except GetError as e:
            if "ConditionalCheckFailedException" in str(e):
                raise NotFoundException(f"Item not found for PRN: {prn}")
            else:
                raise UnknownException("Database operation failed while retrieving item") from e
        except DoesNotExist as e:
            raise NotFoundException(f"Item not found for PRN: {prn}") from e
        except Exception as e:
            log.error("Database operation failed", error=str(e), details=kwargs)
            raise UnknownException("Database operation failed") from e

    @classmethod
    def list(
        cls, record_type: Type[ItemModelRecordType], *, client: str, parent_prn: str | None = None, **kwargs
    ) -> Tuple[List[ItemModelRecordType], Paginator]:

        if not client:
            raise BadRequestException("Client is required for item listing")

        if not parent_prn:
            return cls._list_all(record_type, client=client, **kwargs)
        else:
            return cls._list_by_parent_prn(record_type, client=client, parent_prn=parent_prn, **kwargs)

    @classmethod
    def _list_all(
        cls,
        record_type: Type[ItemModelRecordType],
        *,
        client: str,
        earliest_time: datetime | None = None,
        latest_time: datetime | None = None,
        **kwargs,
    ) -> Tuple[List[ItemModelRecordType], Paginator]:
        """List all items."""

        try:
            paginator = Paginator(**kwargs)
        except ValueError as e:
            raise BadRequestException(f"Invalid item data: {e}")

        scan_args = paginator.get_scan_args()

        model_class = record_type.model_class(client)

        if earliest_time and latest_time:
            condition = model_class.created_at.between(earliest_time, latest_time)
        elif earliest_time:
            condition = model_class.created_at >= earliest_time
        elif latest_time:
            condition = model_class.created_at <= latest_time
        else:
            condition = None

        if condition is not None:
            scan_args["filter_condition"] = condition

        try:

            result = model_class.scan(**scan_args)

            data_list: List[ItemModelRecordType] = [record_type.from_model(item) for item in result]  # type: ignore[call-arg]

            paginator.last_evaluated_key = getattr(result, "last_evaluated_key", None)
            paginator.total_count = len(data_list)

            return data_list, paginator

        except ScanError as e:
            raise UnknownException("Database operation failed while scanning items") from e
        except Exception as e:
            log.error("Database operation failed", error=str(e), details=kwargs)
            raise UnknownException("Database operation failed") from e

    @classmethod
    def update(cls, record_type: Type[ItemModelRecordType], *, client: str, **kwargs) -> ItemModelRecordType:
        return cls._update(record_type, remove_none=True, client=client, **kwargs)

    @classmethod
    def patch(cls, record_type: Type[ItemModelRecordType], *, client: str, **kwargs) -> ItemModelRecordType:
        return cls._update(record_type, remove_none=False, client=client, **kwargs)

    @classmethod
    def _update(cls, record_type: Type[ItemModelRecordType], *, remove_none: bool, client: str, **kwargs) -> ItemModelRecordType:

        if not client:
            raise BadRequestException("Client is required for item update")

        prn = kwargs.get("prn")
        if not prn:
            raise BadRequestException("PRN is required for item update")

        # don't care if parent_prn is passed, we derive it from prn
        parent_prn = record_type.get_parent_prn(prn)
        kwargs["parent_prn"] = parent_prn

        try:

            exclude_fields = {"prn", "parent_prn", "created_at", "updated_at"}

            # Validate input data files
            if remove_none:
                input_data = record_type(**kwargs)
            else:
                # we do this just to filter out unknown fields
                input_data = record_type.model_construct(**kwargs, validate_fields=False)

            values = input_data.model_dump(by_alias=False, exclude_none=False, exclude=exclude_fields)

            model_class = record_type.model_class(client)

            attributes = model_class.get_attributes()

            actions: list[Action] = []
            for key, value in values.items():
                if key in exclude_fields:
                    continue

                if key in attributes:
                    attr = attributes[key]
                    if value is None:
                        if remove_none:
                            actions.append(attr.remove())
                    else:
                        actions.append(attr.set(value))

            actions.append(model_class.updated_at.set(make_default_time()))

            item = model_class.get(hash_key=parent_prn, range_key=prn)
            item.update(actions=actions, condition=model_class.prn.exists())
            item.refresh()

            data: ItemModelRecordType = record_type.from_model(item)  # type: ignore[call-arg]

            return data

        except ValueError as e:
            raise BadRequestException(f"Invalid item data: {e}")

        except UpdateError as e:
            if "ConditionalCheckFailedException" in str(e):
                raise NotFoundException(f"Item not found for update: {input_data.prn}")

            raise UnknownException("Database operation failed while updating item") from e

        except Exception as e:
            log.error("Database operation failed", error=str(e), details=kwargs)
            raise UnknownException("Database operation failed") from e

    @classmethod
    def _list_by_parent_prn(
        cls,
        record_type: Type[ItemModelRecordType],
        *,
        client: str,
        parent_prn: str,
        earliest_time: datetime | None = None,
        latest_time: datetime | None = None,
        **kwargs,
    ) -> Tuple[List[ItemModelRecordType], Paginator]:
        """uses the index to list items by parent_prn and date range"""

        if not parent_prn or not earliest_time or not latest_time:
            raise BadRequestException("parent_prn, earliest_time, and latest_time are required")

        try:
            paginator = Paginator(**kwargs)
        except ValueError as e:
            raise BadRequestException(f"Invalid pagination parameters: {e}")

        model_class = record_type.model_class(client)

        query_args = paginator.get_query_args()
        if earliest_time and latest_time:
            condition = model_class.created_at.between(earliest_time, latest_time)
        elif earliest_time:
            condition = model_class.created_at >= earliest_time
        elif latest_time:
            condition = model_class.created_at <= latest_time
        else:
            condition = None

        if condition is not None:
            query_args["range_key_condition"] = condition

        try:

            result = model_class.parent_created_at_index.query(hash_key=parent_prn, **query_args)

            data_list: List[ItemModelRecordType] = [record_type.from_model(item) for item in result]  # type: ignore[call-arg]

            paginator.last_evaluated_key = getattr(result, "last_evaluated_key", None)
            paginator.total_count = len(data_list)

            return data_list, paginator

        except QueryError as e:
            log.error("Database operation failed while querying items", error=str(e))
            raise UnknownException("Database operation failed while querying items") from e

        except Exception as e:
            log.error("Database operation failed", error=str(e))
            raise UnknownException("Database operation failed") from e
