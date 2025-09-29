"""Defines the data model and attributes stored in DynamoDB using the pynamdb interface."""

from typing import Type, Union, Dict, Any, Optional
from datetime import datetime, timezone
import dateutil

from pydantic import Field, field_validator, model_validator

from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute, MapAttribute


import core_logging as log
import core_framework as util
from core_framework.constants import (
    SCOPE_PORTFOLIO,
    SCOPE_APP,
    SCOPE_BRANCH,
    SCOPE_BUILD,
    SCOPE_COMPONENT,
)
from core_framework.time_utils import make_default_time

from ..models import DatabaseTable, TableFactory, DatabaseRecord


def convert_level_name(value: Union[int, str]) -> str:
    """Convert numeric log levels to their string names.

    Args:
        value (Union[int, str]): Integer log level or string level name

    Returns:
        str: String representation of the log level

    Examples:
        >>> convert_level_name(10)
        'DEBUG'
        >>> convert_level_name(20)
        'INFO'
        >>> convert_level_name('ERROR')
        'ERROR'
    """
    if isinstance(value, int):
        return log.getLevelName(value)
    return value


class EventModel(DatabaseTable):
    """DynamoDB model for storing event records during deployment operations.

    Records critical status messages and events that occur during pipeline deployments,
    providing deployment status tracking and audit trail capabilities. Inherits
    PascalCase/snake_case conversion functionality.

    Attributes:
        prn (str): Pipeline Reference Number (PRN) of the event (hash key).
            Format: "prn:portfolio[:app[:branch[:build[:component]]]]" (e.g., "prn:core:api")
        timestamp (datetime): Timestamp of the event (range key). Auto-generated if not provided.
        event_type (str): Type of event (e.g., 'INFO', 'ERROR', 'STATUS', 'WARNING') like a LogLevel.
            Default: "STATUS"
        item_type (str, optional): Type of item this event relates to such as portfolio, app, branch, build, component, account, etc.
        status (str, optional): The status name. Common values: "ok", "error", "running", "pending"
        message (str, optional): Event message details providing context about the deployment event
        details (dict, optional): Additional detailed information about the event (e.g., stack outputs, error details, metadata)

    Note:
        Events provide deployment audit trail and status tracking capabilities.
        They are keyed by PRN and timestamp, allowing chronological event history
        for any item in the deployment hierarchy.

        The hierarchy is: Portfolio -> App -> Branch -> Build -> Component

    Examples:
        Both formats work identically (thanks to __init__ conversion):

        >>> event1 = EventModel(
        ...     prn="prn:core:api",
        ...     event_type="STATUS",
        ...     item_type="app",
        ...     status="ok",
        ...     message="Application deployed successfully"
        ... )

        >>> event2 = EventModel(
        ...     Prn="prn:core:api",
        ...     EventType="ERROR",
        ...     ItemType="component",
        ...     Status="error",
        ...     Message="EC2 instance failed to start"
        ... )

        Build deployment event with details:

        >>> build_event = EventModel(
        ...     prn="prn:ecommerce:api:master:build-123",
        ...     event_type="INFO",
        ...     item_type="build",
        ...     status="running",
        ...     message="Starting deployment of build-123",
        ...     details={
        ...         "stack_name": "ecommerce-api-master-build-123",
        ...         "region": "us-east-1",
        ...         "parameters": {"InstanceType": "t3.micro", "Environment": "prod"}
        ...     }
        ... )
    """

    class Meta(DatabaseTable.Meta):
        """Meta class for EventModel DynamoDB table configuration.

        Inherits configuration from DatabaseTable.Meta including table naming,
        region settings, and billing mode.
        """

        pass

    # Keys for events
    prn = UnicodeAttribute(hash_key=True, attr_name="Prn")
    timestamp = UTCDateTimeAttribute(range_key=True, default_for_new=make_default_time, attr_name="Timestamp")

    # Event details
    event_type = UnicodeAttribute(default_for_new="STATUS", attr_name="EventType")
    item_type = UnicodeAttribute(null=True, attr_name="ItemType")
    status = UnicodeAttribute(null=True, attr_name="Status")
    message = UnicodeAttribute(null=True, attr_name="Message")
    details = MapAttribute(null=True, attr_name="Details")

    def __repr__(self) -> str:
        """Return string representation of the EventModel.

        Returns:
            str: String representation showing key fields

        Examples:
            >>> event = EventModel(prn="prn:core:api", event_type="STATUS", status="ok")
            >>> repr(event)
            '<Event(prn=prn:core:api,timestamp=2023-01-01T00:00:00+00:00,item_type=app,status=ok,message=Deployment successful)>'
        """
        return f"<Event(prn={self.prn},timestamp={self.timestamp},item_type={self.item_type},status={self.status},message={self.message})>"


EventModelType = Type[EventModel]


class EventModelFactory:
    """Factory class for creating client-specific EventModel instances and managing tables.

    Provides methods for getting client-specific models, creating/deleting tables,
    and checking table existence. Acts as a wrapper around TableFactory for EventModel.

    Examples:
        >>> # Get client-specific model
        >>> client_model = EventModelFactory.get_model("acme")

        >>> # Create table for client
        >>> EventModelFactory.create_table("acme", wait=True)

        >>> # Check if table exists
        >>> exists = EventModelFactory.exists("acme")

        >>> # Delete table
        >>> EventModelFactory.delete_table("acme", wait=True)
    """

    @classmethod
    def get_model(cls, client: str) -> EventModelType:
        """Get the EventModel class for the given client.

        Args:
            client (str): The name of the client

        Returns:
            EventModelType: Client-specific EventModel class

        Examples:
            >>> model_class = EventModelFactory.get_model("acme")
            >>> event = model_class(prn="prn:core:api", event_type="STATUS")
        """
        return TableFactory.get_model(EventModel, client=client)

    @classmethod
    def create_table(cls, client: str, wait: bool = True) -> bool:
        """Create the EventModel table for the given client.

        Args:
            client (str): The name of the client
            wait (bool): Whether to wait for table creation to complete

        Returns:
            bool: True if table was created, False if it already exists

        Examples:
            >>> EventModelFactory.create_table("acme", wait=True)
            True
        """
        return TableFactory.create_table(EventModel, client=client, wait=wait)

    @classmethod
    def delete_table(cls, client: str, wait: bool = True) -> bool:
        """Delete the EventModel table for the given client.

        Args:
            client_name (str): The name of the client
            wait (bool): Whether to wait for table deletion to complete

        Returns:
            bool: True if table was deleted, False if it did not exist

        Examples:
            >>> EventModelFactory.delete_table("acme", wait=True)
            True
        """
        return TableFactory.delete_table(EventModel, client=client, wait=wait)

    @classmethod
    def exists(cls, client: str) -> bool:
        """Check if the EventModel table exists for the given client.

        Args:
            client (str): The name of the client

        Returns:
            bool: True if the table exists, False otherwise

        Examples:
            >>> EventModelFactory.exists("acme")
            True
        """
        return TableFactory.exists(EventModel, client=client)


class EventItem(DatabaseRecord):
    """Pydantic model representing an Event.

    Attributes:
        prn (str): Pipeline Reference Number (PRN) of the event (identity)
        timestamp (datetime): Timestamp of the event (auto-generated by system)
        event_type (str): Type of event (e.g., 'INFO', 'ERROR', 'STATUS')
        item_type (str, optional): Type of item this event relates to (portfolio, app, branch, build, component, account, etc.)
        status (str, optional): The status name, typically "ok" or "error"
        message (str, optional): Event message details
        details (dict, optional): Additional detailed information about the event

    Examples:
        >>> # Create event item
        >>> event = EventItem(
        ...     Prn="prn:core:api",
        ...     EventType="STATUS",
        ...     ItemType="app",
        ...     Status="ok",
        ...     Message="Deployment successful"
        ... )

        >>> # Convert from DynamoDB model
        >>> db_event = EventModel(prn="prn:core:api", event_type="STATUS")
        >>> pydantic_event = EventItem.from_dynamodb(db_event)

    """

    prn: str = Field(
        ...,
        alias="Prn",
        description="Pipeline Reference Number (PRN) of the event (a.k.a identity)",
    )
    timestamp: datetime = Field(
        alias="Timestamp",
        description="Timestamp of the event. Let the system auto-generate",
        default_factory=lambda: datetime.now(timezone.utc),
    )
    event_type: Optional[str] = Field(
        None,
        alias="EventType",
        description="Type of event (e.g., 'INFO', 'ERROR', 'STATUS', 'DEPLOY_REQUESTED', 'DEPLOY_IN_PROGRESS', 'DEPLOY_COMPLETE', etc.)",
    )
    item_type: Optional[str] = Field(
        None,
        alias="ItemType",
        description="Type of item is one of [portfolio, app, branch, build, component]",
    )
    status: Optional[str] = Field(
        None,
        alias="Status",
        description='The status for the event "ok", "error", "running", etc.',
    )
    message: Optional[str] = Field(
        None,
        alias="Message",
        description="Event message details",
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        alias="Details",
        description="Additional detailed information about the event",
    )

    @model_validator(mode="before")
    def validate_event_type(cls, ov: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure event_type is a valid log level name or number.

        Converts numeric log levels to their string names.

        Args:
            values (Dict[str, Any]): Input values for the model

        Returns:
            Dict[str, Any]: Validated and possibly modified values

        """
        values = util.pascal_case_to_snake_case(ov)

        # don't touch details if it exists, let the user make the attributes whatever case they want
        values["details"] = ov.get("details", ov.get("Details", None))

        prn = values.get("prn")
        if not prn:
            raise ValueError("prn not specified in event")

        values["item_type"] = EventItem.get_item_type(prn)

        return values

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp_field(cls, value: datetime | str) -> datetime:
        """Validate the timestamp field to ensure it is a datetime object.

        Args:
            value (datetime): The timestamp value to validate

        Returns:
            datetime: Validated timestamp value

        Raises:
            ValueError: If the timestamp is not a valid datetime object
        """
        if isinstance(value, str):
            return dateutil.parser.parse(value)
        return value

    @field_validator("event_type", mode="before")
    @classmethod
    def validate_event_type_field(cls, value: str | int) -> str:
        """Validate the event_type field to ensure it is a valid log level name.

        Args:
            value (str): The event_type value to validate

        Returns:
            str: Validated event_type value

        Raises:
            ValueError: If the event_type is not a valid log level name
        """
        return convert_level_name(value)

    @classmethod
    def from_model(cls, model: EventModel) -> "EventItem":
        """Convert a PynamoDB EventModel to a Pydantic EventItem.

        Args:
            client (str): The name of the client
            model (EventModel): The PynamoDB model instance to convert

        Returns:
            Self: A new EventItem instance populated with the model data

        """
        return cls.model_validate(model.attribute_values)

    @classmethod
    def model_class(cls, client: str) -> EventModelType:
        """Convert this EventItem to a PynamoDB EventModel instance.

        Args:
            client (str): The name of the client for which to create the model

        Returns:
            EventModel: A new PynamoDB EventModel instance populated with this item's data

        Examples:
            >>> event = EventItem(prn="prn:core:api", event_type="STATUS")
            >>> db_event = event.model_class("acme")
        """
        return EventModelFactory.get_model(client)

    def to_model(self, client: str) -> EventModel:
        """Convert this EventItem to a PynamoDB EventModel instance.

        Args:
            client (str): The name of the client for which to create the model
            **kwargs: Additional keyword arguments to pass to the model constructor

        Returns:
            EventModel: A new PynamoDB EventModel instance populated with this item's data

        Examples:
            >>> event = EventItem(prn="prn:core:api", event_type="STATUS")
            >>> db_event = event.to_model("acme")
        """
        model_class = EventModelFactory.get_model(client)
        return model_class(**self.model_dump(by_alias=False, exclude_none=True))

    @classmethod
    def get_item_type(cls, prn: str) -> str:
        """Determines the item type for an event based on keyword arguments.

        Analyzes the provided arguments to determine the appropriate item type (scope)
        for the event. Can use explicit ITEM_TYPE parameter or derive from PRN structure.

        Args:
            **kwargs: Keyword arguments that may contain:
                - item_type (str, optional): Explicit item type specification
                - prn (str, optional): Pipeline Reference Number to analyze for scope

        Returns:
            str: The item type string (portfolio, app, branch, build, or component).

        Raises:
            ValueError: If PRN is invalid or has unexpected structure.

        """
        item_types = [
            SCOPE_PORTFOLIO,
            SCOPE_APP,
            SCOPE_BRANCH,
            SCOPE_BUILD,
            SCOPE_COMPONENT,
        ]

        num_sections = prn.count(":") - 1
        if not 0 <= num_sections <= 4:
            raise ValueError(f"Invalid prn: {prn}")
        item_type = item_types[num_sections]

        return item_type

    def model_dump(self, *args, **kwargs) -> Dict[str, Any]:
        """Override model_dump to ensure correct field names and types.

        Args:
            *args: Positional arguments passed to the base method
            **kwargs: Keyword arguments passed to the base method

        Returns:
            Dict[str, Any]: Dictionary representation of the model with field names in PascalCase
        """
        kwargs.setdefault("by_alias", False)
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(*args, **kwargs)

    def __repr__(self) -> str:
        """Return a string representation of the EventItem instance.

        Returns:
            str: String representation of the event item

        Examples:
            >>> event = EventItem(Prn="prn:core:api", EventType="STATUS", Status="ok")
            >>> repr(event)
            '<Event(prn=prn:core:api,timestamp=2023-01-01T00:00:00+00:00,item_type=None,status=ok,message=None)>'
        """
        return f"<Event(prn={self.prn},timestamp={self.timestamp},item_type={self.item_type},status={self.status},message={self.message})>"
