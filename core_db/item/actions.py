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

import core_logging as log
import core_framework as util
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
from ..response import (
    Response,
    SuccessResponse,  # http 200
)

from ..models import Paginator
from .models import ItemModelRecord, ItemModelType, ItemModelRecordType


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
    def create(cls, record_type: ItemModelRecordType, **kwargs) -> Response:
        """Create a new item in the items table.

        Args:
            record_type: The specific ItemModelRecord subclass to create
            **kwargs: Item attributes including prn, name, and type-specific fields

        Returns:
            Response: SuccessResponse containing the created item data

        Raises:
            BadRequestException: If required fields are missing or invalid
            ConflictException: If item already exists with the same PRN
            UnknownException: If database operation fails
        """
        client = kwargs.get("client") or util.get_client()
        if not client:
            raise BadRequestException("Client is required for item creation")

        try:
            data = record_type(**kwargs)

            item = data.to_model(client)
            item.save(type(item).prn.does_not_exist())

            data = record_type.from_model(item).model_dump(mode="json")

            return SuccessResponse(data=data, message="Item created successfully")

        except ValueError as e:
            raise BadRequestException(f"Invalid item data: {e}")
        except PutError as e:
            if "ConditionalCheckFailedException" in str(e):
                raise ConflictException(f"Item already exists with PRN: {data.prn}")
            else:
                raise UnknownException("Database operation failed while creating item") from e
        except Exception as e:
            log.error("Database operation failed", error=str(e), details=kwargs)
            raise UnknownException("Database operation failed") from e

    @classmethod
    def delete(cls, record_type: ItemModelRecordType, **kwargs) -> Response:
        """Delete an item from the items table.

        Deletes the specified item if it exists. If the item is not found,
        returns a success response rather than an error (idempotent operation).

        Args:
            record_type: The specific ItemModelRecord subclass to delete
            **kwargs: Delete parameters including prn (required)

        Returns:
            Response: SuccessResponse with confirmation message

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

        client = kwargs.get("client") or util.get_client()
        if not client:
            raise BadRequestException("Client is required for item deletion")

        prn = kwargs.get("prn")
        if not prn:
            raise BadRequestException("PRN is required for item deletion")

        parent_prn = record_type.get_parent_prn(prn)

        try:
            model_class: ItemModelType = record_type.model_class(client)
            item = model_class(parent_prn=parent_prn, prn=prn)
            item.delete(condition=model_class.prn.exists())

            return SuccessResponse(message=f"Item deleted: {prn}")
        except ValueError as e:
            raise BadRequestException(f"Invalid item data: {e}")
        except DeleteError as e:
            if "ConditionalCheckFailedException" in str(e):
                raise NotFoundException(f"Item not found for deletion: {prn}")
            else:
                raise UnknownException("Database operation failed while deleting item") from e
        except DoesNotExist as e:
            raise NotFoundException(f"Item not found for deletion: {prn}") from e
        except Exception as e:
            log.error("Database operation failed", error=str(e), details=kwargs)
            raise UnknownException("Database operation failed") from e

    @classmethod
    def get(cls, record_type: ItemModelRecord, **kwargs) -> Response:
        """Retrieve a single item from the items table by PRN.

        Fetches the item with the specified Primary Resource Name and returns
        its complete data as a dictionary.

        Args:
            record_type: The specific ItemModelRecord subclass to retrieve
            **kwargs: Get parameters including prn (required)

        Returns:
            Response: SuccessResponse containing the item data

        Raises:
            BadRequestException: If the PRN is missing or has invalid format
            NotFoundException: If no item exists with the specified PRN
            UnknownException: If database operation fails
        """
        log.debug("Received get request:", details=kwargs)

        client = kwargs.get("client") or util.get_client()
        if not client:
            raise BadRequestException("Client is required for item retrieval")

        prn = kwargs.get("prn")
        if not prn:
            raise BadRequestException("PRN is required for item retrieval")

        model_class: ItemModelType = record_type.model_class(client)
        try:
            item = model_class.get(prn, condition=model_class.prn.exists())
            data = record_type.from_model(item).model_dump(mode="json")

            return SuccessResponse(data=data)
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
    def list(cls, record_type: ItemModelRecord, **kwargs) -> Response:
        cleint = kwargs.get("client") or util.get_client()
        if not cleint:
            raise BadRequestException("Client is required for item listing")

        prn = kwargs.get("prn")
        parent_prn = kwargs.get("parent_prn")
        earliest_time = kwargs.get("earliest_time")
        latest_time = kwargs.get("latest_time")

        if prn and parent_prn:
            return cls.get(record_type, **kwargs)

        if prn:
            return cls._list_by_prn(record_type, **kwargs)

        if parent_prn and not earliest_time and not latest_time:
            return cls._list_by_parent_prn(record_type, **kwargs)

        if parent_prn and earliest_time and latest_time:
            return cls._list_by_parent_prn_in_date_range(record_type, **kwargs)

        raise BadRequestException("Either prn or parent_prn must be provided for listing items")

    @classmethod
    def _list_by_prn(cls, record_type: ItemModelRecord, **kwargs) -> Response:
        """List items by their PRN."""
        client = kwargs.get("client") or util.get_client()
        if not client:
            raise BadRequestException("Client is required for item listing")

        prn = kwargs.get("prn")
        if not prn:
            raise BadRequestException("PRN is required for listing items by PRN")

        parent_prn = record_type.get_parent_prn(prn)

        model_class = record_type.model_class(client)
        try:
            item = model_class.get(hash_key=parent_prn, range_key=prn)
            data = [record_type.from_model(item).model_dump(mode="json")]

            return SuccessResponse(data=data)
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
    def _list_by_parent_prn(cls, record_type: ItemModelRecord, **kwargs) -> Response:
        """List items by their parent PRN."""
        parent_prn = kwargs.get("parent_prn")
        if not parent_prn:
            raise BadRequestException("Parent PRN is required for listing items by parent PRN")

        client = kwargs.get("client") or util.get_client()
        if not client:
            raise BadRequestException("Client is required for item listing")

        paginator = Paginator(**kwargs)

        model_class: ItemModelType = record_type.model_class(client)
        try:
            query_args = {
                "limit": paginator.limit,
            }
            if paginator.cursor:
                query_args["last_evaluated_key"] = paginator.cursor
            if paginator.sort_forward is not None:
                query_args["scan_index_forward"] = paginator.sort_forward

            result = model_class.scan(model_class.parent_prn == parent_prn, **query_args)

            data_list = [record_type.from_model(item).model_dump(mode="json") for item in result]

            paginator.cursor = getattr(result, "last_evaluated_key", None)
            paginator.total_count = getattr(result, "total", len(data_list))

            return SuccessResponse(data=data_list, metadata=paginator.get_metadata())
        except ValueError as e:
            raise BadRequestException(f"Invalid item data: {e}")
        except ScanError as e:
            raise UnknownException("Database operation failed while scanning items") from e
        except Exception as e:
            log.error("Database operation failed", error=str(e), details=kwargs)
            raise UnknownException("Database operation failed") from e

    @classmethod
    def update(cls, record_type: ItemModelRecord, **kwargs) -> Response:
        return cls._update(record_type, remove_none=True, **kwargs)

    @classmethod
    def patch(cls, record_type: ItemModelRecord, **kwargs) -> Response:
        return cls._update(record_type, remove_none=False, **kwargs)

    @classmethod
    def _update(cls, record_type: ItemModelRecord, remove_none: bool, **kwargs) -> Response:

        client = kwargs.get("client", util.get_client())
        if not client:
            raise BadRequestException("Client is required for item update")

        prn = kwargs.get("prn")
        if not prn:
            raise BadRequestException("PRN is required for item update")

        parent_prn = kwargs.get("parent_prn", record_type.get_parent_prn(prn))
        if not parent_prn:
            raise BadRequestException("Parent PRN is required for item update")

        if remove_none:
            input_data = record_type(**kwargs)
        else:
            input_data = record_type.model_construct(**kwargs)

        try:
            values = input_data.model_dump(by_alias=False, exclude_none=False)

            model_class: ItemModelType = record_type.model_class(client)

            attribvtes = model_class.get_attributes()

            actions: list[Action] = []
            for key, value in values.items():
                if key in ["prn", "parent_prn", "created_at", "updated_at"]:
                    continue
                if key in attribvtes:
                    attr = attribvtes[key]
                    if value is None:
                        if remove_none:
                            actions.append(attr.remove())
                    else:
                        actions.append(attr.set(value))

            actions.append(model_class.updated_at.set(make_default_time()))

            item = model_class.get(hash_key=parent_prn, range_key=prn)
            item.update(actions=actions, condition=model_class.prn.exists())
            item.refresh()

            data: ItemModelRecordType = record_type.from_model(item).model_dump(mode="json")

            return SuccessResponse(
                data=data,
                message="Item updated successfully",
            )

        except ValueError as e:
            raise BadRequestException(f"Invalid item data: {e}")
        except UpdateError as e:
            if "ConditionalCheckFailedException" in str(e):
                raise NotFoundException(f"Item not found for update: {input_data.prn}")
            else:
                raise UnknownException("Database operation failed while updating item") from e
        except DoesNotExist as e:
            raise NotFoundException(f"Item not found for update: {input_data.prn}") from e
        except Exception as e:
            log.error("Database operation failed", error=str(e), details=kwargs)
            raise UnknownException("Database operation failed") from e

    @classmethod
    def _list_by_parent_prn_in_date_range(cls, record_type: ItemModelRecordType, **kwargs):
        """uses the index to list items by parent_prn and date range"""

        client = kwargs.get("client") or util.get_client()
        if not client:
            raise BadRequestException("Client is required for item listing")

        parent_prn = kwargs.get("parent_prn")
        earliest_time = kwargs.get("earliest_time")
        latest_time = kwargs.get("latest_time")

        if not parent_prn or not earliest_time or not latest_time:
            raise BadRequestException("parent_prn, earliest_time, and latest_time are required")

        try:
            model_class = record_type.model_class(client)

            paginator = Paginator(**kwargs)

            query_args = {
                "limit": paginator.limit,
                "index": model_class.parent_created_at_index,
                "range_key_condition": model_class.created_at.between(earliest_time, latest_time),
            }

            result = model_class.parent_created_at_index(hash_key=parent_prn, **query_args)

            data_list = [record_type.from_model(item).model_dump(mode="json") for item in result]

            paginator.cursor = getattr(result, "last_evaluated_key", None)
            paginator.total_count = getattr(result, "total", len(data_list))

            return SuccessResponse(
                data=data_list,
                metadata=paginator.get_metadata(),
                message=f"Items listed for parent_prn: {parent_prn} in date range",
            )
        except ValueError as e:
            raise BadRequestException(f"Invalid item data: {e}")
        except QueryError as e:
            raise UnknownException("Database operation failed while querying items") from e
        except DoesNotExist as e:
            raise NotFoundException(f"No items found for parent_prn: {parent_prn} in date range") from e
        except Exception as e:
            log.error("Database operation failed", error=str(e), details=kwargs)
            raise UnknownException("Database operation failed") from e
