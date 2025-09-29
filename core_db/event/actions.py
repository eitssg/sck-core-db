"""Event management actions for the core-automation-events DynamoDB table.

This module provides CRUD operations and utilities for managing events in the Core Automation Event table.
Events serve as the primary audit trail for all deployment operations and status changes across the
Simple Cloud Kit ecosystem.

Key Components:
    - **EventActions**: Main class providing CRUD operations for event management
    - **Event validation**: Business rules and constraints for event data integrity
    - **Time filtering**: Advanced querying with date ranges and pagination
    - **PRN-based organization**: Events organized by Pipeline Reference Numbers

Features:
    - **CRUD Operations**: Complete create, read, update, delete functionality
    - **Time Range Queries**: Filter events by earliest and latest timestamps
    - **Pagination Support**: Handle large result sets with efficient pagination
    - **PRN Validation**: Automatic PRN generation and validation
    - **Item Type Detection**: Automatic scope detection from PRN structure
"""

from typing import List, Tuple
from pynamodb.expressions.update import Action
from pynamodb.exceptions import (
    DoesNotExist,
    PutError,
    UpdateError,
    DeleteError,
    GetError,
    QueryError,
    ScanError,
    TableError,
)

import core_logging as log
import core_framework as util
from core_framework.time_utils import make_default_time

from ..actions import TableActions
from ..models import Paginator

from .models import Any, EventItem


from ..exceptions import (
    BadRequestException,  # http 400
    NotFoundException,  # http 404
    ConflictException,  # http 409
    UnknownException,  # http 500
)


class EventActions(TableActions):
    """Implements CRUD operations for the Event table using the PynamoDB model.

    This class provides comprehensive event management functionality for the core-automation-events
    DynamoDB table. Events serve as audit trails for all deployment operations, status changes,
    and system activities across the Simple Cloud Kit ecosystem.

    Attributes:
        item_types (list[str]): List of supported item types for events, corresponding to
            different PRN scopes (portfolio, app, branch, build, component).
    """

    @classmethod
    def create(cls, *, client: str, **kwargs) -> EventItem:
        """Create a new event in the event table.

        Creates a new audit event with the provided attributes. Automatically generates
        PRN if not provided, determines item type from PRN structure, and sets default
        event type if not specified.

        Args:
            client (str): Client identifier for table isolation
            **kwargs: Event attributes including:
                - prn (str, optional): Pipeline Reference Number. Auto-generated if not provided.
                - status (str, optional): Event status (success, failure, in_progress, etc.)
                - message (str, optional): Human-readable event description
                - event_type (str, optional): Event classification. Defaults to current log level.
                - metadata (dict, optional): Additional event context and details
                - item_type (str, optional): Explicit item type. Auto-detected if not provided.
                - client (str, optional): Client identifier for table isolation.

        Returns:
            BaseModel: BaseModel object containing the created event data.

        Raises:
            BadRequestException: If event data is invalid or PRN cannot be generated.
            ConflictException: If creation fails due to a database conflict (rare with UUID keys).
            UnknownException: For other unexpected errors during event creation.
        """
        if not client:
            raise BadRequestException("Client identifier is required for event creation.")

        try:
            event_data = EventItem(**kwargs)
        except Exception as e:
            log.error("Failed to construct EventItem", details=str(e))
            raise BadRequestException("Invalid event data provided.") from e

        try:
            # Convert to PynamoDB model instance
            item = event_data.to_model(client)
            item.save()
            return event_data
        except PutError as e:
            log.error("Failed to save event to database", details=str(e))
            raise ConflictException("Event already exists or database error occurred.") from e
        except Exception as e:
            log.error("Unexpected error during event creation", details=str(e))
            raise UnknownException("An unexpected error occurred while creating the event.") from e

    @classmethod
    def get(cls, *, client: str, **kwargs) -> EventItem:
        """Retrieve an event from the event table.

        Fetches a single event by its PRN and timestamp. If only PRN is provided,
        returns the latest event for that PRN.

        Args:
            client (str): Client identifier for table isolation
            **kwargs: Event identifying attributes including:

                - prn (str, required): Pipeline Reference Number for the event.
                - timestamp (str, optional): Specific timestamp to retrieve a single event.
                  If not provided, retrieves the latest event for the PRN.
                - client (str, optional): Client identifier for table access.

        Returns:
            BaseModel: BaseModel object with the requested event data.

        Raises:
            BadRequestException: If required parameters are missing.
            NotFoundException: If no events found for the specified PRN or timestamp.
            UnknownException: If database operation fails.
        """
        prn = kwargs.get("prn")
        timestamp = kwargs.get("timestamp")

        if not client:
            raise BadRequestException("Client identifier is required for event retrieval.")

        if not prn:
            raise BadRequestException("PRN is required to retrieve an event.")

        if not timestamp:
            raise BadRequestException("Timestamp is required to retrieve a specific event.")

        try:
            model_class = EventItem.model_class(client)

            # Retrieve specific event by PRN and timestamp
            item = model_class.get(prn, timestamp)

            return EventItem.from_model(item)

        except DoesNotExist:
            raise NotFoundException(f"Event with PRN {prn} and timestamp {timestamp} not found.")
        except GetError as e:
            log.error("Database error during event retrieval", details=str(e))
            raise UnknownException(f"Database error during retrieval: {str(e)}") from e
        except (BadRequestException, NotFoundException):
            raise
        except Exception as e:
            log.error("Unexpected error during event retrieval", details=str(e))
            raise UnknownException(f"Unexpected error during retrieval: {str(e)}") from e

    @classmethod
    def update(cls, *, client: str, **kwargs) -> EventItem:
        return cls._update(remove_none=True, client=client, **kwargs)

    @classmethod
    def patch(cls, *, client: str, **kwargs) -> EventItem:
        return cls._update(remove_none=False, client=client, **kwargs)

    @classmethod
    def delete(cls, *, client: str, prn: str | None = None, timestamp: str | None = None, **kwargs) -> bool:
        """Delete event(s) from the event table.

        Removes event record(s) from the database based on the provided PRN and optional timestamp.
        If only PRN is provided, deletes ALL events for that PRN using pagination to handle large
        result sets. If both PRN and timestamp are provided, deletes the specific event.

        Args:
            **kwargs: Event identifying attributes including:

                - prn (str, required): Pipeline Reference Number for the event(s).
                - timestamp (str, optional): Specific timestamp for single event deletion.
                  If not provided, ALL events for the PRN will be deleted.
                - client (str, optional): Client identifier for table access.

        Returns:
            BaseModel: BaseModel object with confirmation message about the deleted event(s).

        Raises:
            BadRequestException: If required parameters are missing.
            NotFoundException: If no events found for the specified PRN.
            UnknownException: If database operation fails.

        .. warning::
            Deleting events removes audit trail information. This operation should
            be used carefully and is primarily intended for testing and cleanup
            scenarios rather than normal operational use.
        """
        if not client:
            raise BadRequestException("Client identifier is required for event deletion.")

        if not prn:
            raise BadRequestException("PRN is required for event deletion.")

        try:
            if timestamp:
                return cls._delete_event(client, prn, timestamp)
            else:
                return cls._delete_events_for_prn(client, prn)

        except DoesNotExist:
            raise NotFoundException(f"Event with PRN {prn} and timestamp {timestamp} not found.")
        except (DeleteError, GetError, TableError) as e:
            log.error("Database error during event deletion: %s", str(e))
            raise UnknownException(f"Database error during deletion: {str(e)}") from e
        except (BadRequestException, NotFoundException):
            raise
        except Exception as e:
            log.error("Unexpected error during event deletion: %s", str(e))
            raise UnknownException(f"Unexpected error during deletion: {str(e)}") from e

    @classmethod
    def _delete_event(cls, client: str, prn: str, timestamp: str) -> bool:
        """Delete a specific event by PRN and timestamp.

        Args:
            prn (str): Pipeline Reference Number of the event.
            timestamp (str): Timestamp of the event to delete.
            client (str): Client identifier for table access.

        Returns:
            BaseModel: BaseModel object with confirmation message.
        """
        model_class = EventItem.model_class(client)
        item = model_class.get(prn, timestamp)
        item.delete()
        return True

    @classmethod
    def _delete_events_for_prn(cls, client: str, prn: str) -> bool:
        """Helper method to delete all events for a given PRN.

        Args:
            prn (str): Pipeline Reference Number to delete events for.
            client (str): Client identifier for table access.

        Returns:
            int: Total number of events deleted.
        """
        # Delete ALL events for the PRN using pagination
        log.debug("Deleting all events for PRN: %s", prn)

        paginator = Paginator(limit=100)
        total_deleted_count = 0  # Track total across all pages
        pages_processed = 0

        model_class = EventItem.model_class(client)

        while True:
            # Build query kwargs properly
            query_args = paginator.get_query_args()

            try:
                # Fix: Remove extra parenthesis and use proper query syntax
                result = model_class.query(prn, **query_args)

                # Convert result to list to get items
                events = list(result)

                if pages_processed == 0 and len(events) == 0:
                    raise NotFoundException(f"No events found for PRN {prn}.")

                # Update paginator cursor from results
                paginator.last_evaluated_key = getattr(result, "last_evaluated_key", None)
                paginator.total_count += len(events)

                # Delete each event in this page
                page_deleted_count = 0
                for event in events:
                    try:
                        event.delete()
                        page_deleted_count += 1
                        total_deleted_count += 1  # Add to total count

                    except Exception as e:
                        log.warning(
                            "Failed to delete event %s at %s: %s",
                            prn,
                            getattr(event, "timestamp", "unknown"),
                            str(e),
                        )

                pages_processed += 1
                log.debug(
                    "Deleted %d events from page %d for PRN %s",
                    page_deleted_count,
                    pages_processed,
                    prn,
                )

                # Break if no more pages
                if not paginator.cursor:
                    break

            except QueryError as e:
                log.error(
                    "Failed to query events for PRN %s on page %d: %s",
                    prn,
                    pages_processed + 1,
                    str(e),
                )
                raise UnknownException(f"Failed to query events for PRN {prn}") from e

        if total_deleted_count == 0:
            raise UnknownException(f"Failed to delete any events for PRN {prn}")

        return True

    @classmethod
    def list(cls, *, client: str, prn: str | None = None, **kwargs) -> Tuple[List[EventItem], Paginator]:
        """List events with optional PRN filtering and time range constraints.

        Retrieves events from the database with support for PRN filtering, time-based filtering,
        sorting, and pagination. When PRN is provided, uses efficient Query operation. When PRN
        is not provided, performs table Scan to retrieve all events.

        Args:
            **kwargs: Filtering and pagination options including:

                - prn (str, optional): Pipeline Reference Number. If not provided, scans all events.
                - earliest_time (str, optional): ISO8601 timestamp for start of time range.
                - latest_time (str, optional): ISO8601 timestamp for end of time range.
                - sort_forward (bool, optional): Sort order (True for ascending, False for descending).
                  Defaults to True.
                - limit (int, optional): Maximum number of events to return. Defaults to 100.
                - cursor (str, optional): Base64-encoded pagination token for continuing queries.
                - client (str, optional): Client identifier for table isolation.

        Returns:
            BaseModel: BaseModel object containing:
                - data: List of event dictionaries with all event attributes
                - metadata: Dictionary with pagination cursor and total count

        Raises:
            BadRequestException: If client identifier is missing.
            UnknownException: If an unexpected error occurs during event retrieval.

        Performance Notes:
            - Uses DynamoDB Query operation when PRN is specified (efficient)
            - Uses DynamoDB Scan operation when PRN is not specified (less efficient)
            - Time range filtering applied as conditions
            - Pagination tokens allow efficient continuation of large result sets
            - Sort order affects query performance and pagination behavior
        """
        if not client:
            raise BadRequestException("Client identifier is required for event listing.")

        try:
            if prn:
                return cls._list_by_prn(client=client, prn=prn, **kwargs)
            else:
                return cls._list_all_events(client=client, **kwargs)

        except (QueryError, ScanError) as e:
            log.error("Database error during event listing: %s", str(e))
            raise UnknownException(f"Database error during event retrieval: {str(e)}") from e

        except Exception as e:
            log.error("Unexpected error during event listing: %s", str(e))
            raise UnknownException(f"Unexpected error during event retrieval: {str(e)}") from e

    @classmethod
    def _list_by_prn(cls, *, client: str, prn: str, **kwargs) -> tuple[List[EventItem], Paginator]:
        """List events filtered by Pipeline Reference Number (PRN).

        Uses the Query operation to efficiently retrieve events associated with
        the specified PRN with optional time range filtering and pagination.

        Args:
            client (str): Client identifier for table access
            **kwargs: Additional filtering and pagination options including:
                - prn (str): Pipeline Reference Number to filter by
                - earliest_time (datetime, optional): Start of time range filter
                - latest_time (datetime, optional): End of time range filter
                - sort_forward (bool, optional): Sort direction for timestamp
                - limit (int, optional): Maximum items to return
                - cursor (str, optional): Pagination cursor

        Returns:
            BaseModel: BaseModel object containing the list of events for the specified PRN
        """

        if not prn:
            raise BadRequestException("PRN is required for listing events by PRN.")

        # Query by PRN (hash key) - efficient
        log.debug("Querying events for PRN: %s", prn)

        paginator = Paginator(**kwargs)

        model_class = EventItem.model_class(client)

        # Build range key condition based on time filters
        if paginator.earliest_time and paginator.latest_time:
            range_key_condition = model_class.timestamp.between(paginator.earliest_time, paginator.latest_time)
        elif paginator.earliest_time:
            range_key_condition = model_class.timestamp >= paginator.earliest_time
        elif paginator.latest_time:
            range_key_condition = model_class.timestamp <= paginator.latest_time
        else:
            range_key_condition = None

        # Build query kwargs
        query_kwargs = paginator.get_query_args()

        if range_key_condition is not None:
            query_kwargs["range_key_condition"] = range_key_condition

        # Execute query
        try:
            results = model_class.query(prn, **query_kwargs)

            # Convert results to EventItem instances
            data: List[EventItem] = [EventItem.from_model(item) for item in results]

            # Update paginator with results metadata
            paginator.last_evaluated_key = getattr(results, "last_evaluated_key", None)
            paginator.total_count = len(data)

            log.info("Retrieved %d events for PRN: %s", len(data), prn)

            return data, paginator

        except QueryError as e:
            log.error("Failed to query events for PRN %s: %s", prn, str(e))
            raise UnknownException(f"Failed to query events for PRN {prn}") from e
        except Exception as e:
            log.error("Unexpected error querying events for PRN %s: %s", prn, str(e))
            raise UnknownException(f"Unexpected error querying events for PRN {prn}") from e

    @classmethod
    def _list_all_events(cls, **kwargs) -> Tuple[List[EventItem], Paginator]:  # noqa: C901
        """Scan all events for client with pagination."""
        client = kwargs.get("client") or util.get_client()
        if not client:
            raise BadRequestException("Client identifier is required for event listing.")

        log.debug("Scanning all events for client: %s", client)

        paginator = Paginator(**kwargs)

        model_class = EventItem.model_class(client)

        # Build filter conditions for scan
        filter_conditions = []
        if paginator.earliest_time and paginator.latest_time:
            filter_conditions.append(model_class.timestamp.between(paginator.earliest_time, paginator.latest_time))
        elif paginator.earliest_time:
            filter_conditions.append(model_class.timestamp >= paginator.earliest_time)
        elif paginator.latest_time:
            filter_conditions.append(model_class.timestamp <= paginator.latest_time)

        # Build scan kwargs
        scan_kwargs: dict[str, Any] = {
            "limit": paginator.limit,
            "page_size": paginator.limit,
        }

        if filter_conditions:
            if len(filter_conditions) == 1:
                scan_kwargs["filter_condition"] = filter_conditions[0]
            else:
                combined_condition = filter_conditions[0]
                for condition in filter_conditions[1:]:
                    combined_condition = combined_condition & condition
                scan_kwargs["filter_condition"] = combined_condition

        # Add pagination cursor if available decoded automatically
        if paginator.cursor:
            scan_kwargs["last_evaluated_key"] = paginator.last_evaluated_key

        # Execute scan
        results = model_class.scan(**scan_kwargs)

        # Convert results to EventItem instances
        data: List[EventItem] = []
        for item in results:
            try:
                event_item = EventItem.from_model(item)
                data.append(event_item)
            except Exception as e:
                log.warning("Failed to convert event item: %s", str(e))
                continue

        # Update paginator with results metadata
        paginator.last_evaluated_key = getattr(results, "last_evaluated_key", None)

        return data, paginator

    @classmethod
    def _update(cls, remove_none: bool, **kwargs) -> EventItem:  # noqa: C901
        """Update an existing event in the database with Action statements.

        Creates PynamoDB Action statements for efficient updates. By default,
        performs complete replacement by removing None fields (PUT semantics).

        Args:
            remove_none: If True, fields set to None will be removed from the database.
                        If False, None fields are skipped (not updated).

        Returns:
            Self: Updated event instance with fresh data from database

        Raises:
            BadRequestException: If prn or timestamp is missing
            NotFoundException: If event doesn't exist
            UnknownException: If database operation fails
        """
        client = kwargs.get("client") or util.get_client()
        if not client:
            raise BadRequestException("Client identifier is required for event update.")

        if remove_none:
            try:
                update_data = EventItem(**kwargs)
            except Exception as e:
                log.error("Failed to construct EventItem for update", details=str(e))
                raise BadRequestException("Invalid event data provided for update.") from e
        else:
            # If not removing None, we can use the existing instance
            update_data = EventItem.model_construct(**kwargs)

        try:
            model_class = EventItem.model_class(client)

            # Get all field values from self
            values = update_data.model_dump(by_alias=False, exclude_none=False)

            attributes = model_class.get_attributes()

            # Build update actions
            actions: list[Action] = []
            for key, value in values.items():
                # Skip primary key fields (can't be updated) and system fields
                if key in ["prn", "timestamp", "created_at", "updated_at"]:
                    continue

                # Get the model attribute for this field
                if key in attributes:
                    attr = attributes[key]
                    if value is None:
                        if remove_none:
                            # Remove the field from the database
                            actions.append(attr.remove())
                    else:
                        # Set the field to the new value
                        actions.append(attr.set(value))

            actions.append(model_class.updated_at.set(make_default_time()))

            # Create item instance for update operation
            item = model_class(prn=update_data.prn, timestamp=update_data.timestamp)

            # Perform the update with actions
            item.update(actions=actions)

            # Refresh to get the latest data from database
            item.refresh()

            return EventItem.from_model(item)  # Serialize to JSON with ISO date strings

        except UpdateError as e:
            log.error("Failed to update event in database", details=str(e))
            raise ConflictException(f"Event update failed: {str(e)}") from e
        except DoesNotExist:
            raise NotFoundException(f"Event not found: prn={update_data.prn}, timestamp={update_data.timestamp}")
        except Exception as e:
            raise UnknownException(f"Failed to update event: {str(e)}") from e
