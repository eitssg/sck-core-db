"""Defines the data model and attributes stored in DynamoDB using the pynamdb interface."""

from typing import Type, Union
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

import core_logging as log

from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute

import core_framework as util

from core_framework.time_utils import make_default_time

from ..config import get_table_name
from ..constants import EVENTS


def convert_level_name(value: Union[int, str]) -> str:
    """
    Convert numeric log levels to their string names.

    :param value: Integer log level or string level name.
    :type value: Union[int, str]
    :return: String representation of the log level.
    :rtype: str
    """
    if isinstance(value, int):
        return log.getLevelName(value)
    return value


class EventModel(Model):
    """
    DynamoDB model for storing event records.

    Attributes
    ----------
    prn : UnicodeAttribute
        Pipeline Reference Number (PRN) of the event (a.k.a identity).
    timestamp : UTCDateTimeAttribute
        Timestamp of the event. Let the system auto-generate.
    event_type : UnicodeAttribute
        Type of event (e.g., 'INFO', 'ERROR', 'STATUS') like a LogLevel.
    item_type : UnicodeAttribute
        Type of item this event relates to such as portfolio, app, branch, build, component, account, etc.
    status : UnicodeAttribute
        The status name. Two possible values "ok" or "error".
    message : UnicodeAttribute
        Event message details.
    """

    class Meta:
        region = util.get_dynamodb_region()
        host = util.get_dynamodb_host()
        read_capacity_units = 1
        write_capacity_units = 1

    # Keys for events
    prn = UnicodeAttribute(hash_key=True)
    timestamp = UTCDateTimeAttribute(range_key=True, default_for_new=make_default_time)
    # Event details
    event_type = UnicodeAttribute(default_for_new="STATUS")
    item_type = UnicodeAttribute(null=True)
    status = UnicodeAttribute(null=True)
    message = UnicodeAttribute(null=True)

    def __init__(self, *args, **kwargs):
        """
        Initialize the EventModel instance.

        :param args: Positional arguments.
        :type args: tuple
        :param kwargs: Keyword arguments.
        :type kwargs: dict
        """
        super().__init__(*args, **kwargs)

    def __repr__(self):
        """
        Return a string representation of the EventModel instance.

        :return: String representation of the event.
        :rtype: str
        """
        return f"<Event(prn={self.prn},timestamp={self.timestamp},item_type={self.item_type},status={self.status},message={self.message})>"


class EventModelFactory:
    """
    Factory class to create EventModel instances with client-specific table names.

    Attributes
    ----------
    _model_cache : dict
        Cache for storing created model classes by client.
    """

    _model_cache = {}

    @classmethod
    def get_model(cls, client: str, auto_create_table: bool = False) -> Type[EventModel]:
        """
        Get the EventModel class for a specific client.

        :param client: The client name to use for table naming.
        :type client: str
        :param auto_create_table: Whether to automatically create the table if it doesn't exist.
        :type auto_create_table: bool
        :return: The EventModel class configured for the client.
        :rtype: EventModelType
        """
        if client not in cls._model_cache:
            model_class = cls._create_model(client)
            if auto_create_table:
                cls._ensure_exists(model_class, client)
            cls._model_cache[client] = model_class

        return cls._model_cache[client]

    @classmethod
    def _ensure_exists(cls, model_class: EventModel, client: str):
        """
        Ensure that the DynamoDB table for the model exists.

        :param model_class: The model class to check.
        :type model_class: EventModelType
        :param client: The client name.
        :type client: str
        """
        try:
            if not model_class.exists():
                log.info("Creating events table: %s", model_class.Meta.table_name)
                model_class.create_table(wait=True)
                log.info("Successfully created events table: %s", model_class.Meta.table_name)
        except Exception as e:
            log.error("Error creating events table: %s", e)

    @classmethod
    def _create_model(cls, client: str) -> EventModel:
        """
        Create an EventModel class with a specific table name based on the client.

        :param client: The client name to use for the table name.
        :type client: str
        :return: A new EventModel class with the specified table name.
        :rtype: EventModelType
        """

        class EventModelClass(EventModel):
            class Meta(EventModel.Meta):
                table_name = get_table_name(EVENTS, client)

        return EventModelClass

    @classmethod
    def create_table(cls, client: str, wait: bool = True):
        """
        Create the events table if it does not exist.

        :param wait: Whether to wait for the table creation to complete.
        :type wait: bool
        """
        model_class = cls.get_model(client)
        if not model_class.exists():
            log.info("Creating events table: %s", model_class.Meta.table_name)
            model_class.create_table(wait=wait)
            log.info("Successfully created events table: %s", model_class.Meta.table_name)


class EventModelSchema(BaseModel):
    """
    Pydantic model representing an Event. NOT_IN_USE!!!  This is a placeholder for
    future use with Pydantic validation.

    Attributes
    ----------
    prn : str
        Pipeline Reference Number (PRN) of the event (a.k.a identity).
    timestamp : datetime
        Timestamp of the event. Let the system auto-generate.
    event_type : str
        Type of event (e.g., 'INFO', 'ERROR', 'STATUS').
    item_type : Optional[str]
        Type of item this event relates to such as portfolio, app, branch, build, component, account, etc.
    status : Optional[str]
        The status name. Two possible values "ok" or "error".
    message : Optional[str]
        Event message details.
    """

    prn: str = Field(..., description="Pipeline Reference Number (PRN) of the event (a.k.a identity)")
    timestamp: datetime = Field(
        description="Timestamp of the event. Let the system auto-generate",
        default_factory=datetime.now,
    )
    event_type: str = Field(description="Type of event (e.g., 'INFO', 'ERROR', 'STATUS')", default="STATUS")
    item_type: Optional[str] = Field(
        None,
        description="Type of item this event relates to such as portfolio, app, branch, build, component, account, etc.",
    )
    status: Optional[str] = Field(None, description='The status name. Two possible values "ok" or "error"')
    message: Optional[str] = Field(None, description="Event message details")

    class Config:
        """Pydantic configuration class."""

        orm_mode = True

    def __repr__(self):
        """
        Return a string representation of the EventModelSchema instance.

        :return: String representation of the event schema.
        :rtype: str
        """
        return f"<Event(prn={self.prn},timestamp={self.timestamp},item_type={self.item_type},status={self.status},message={self.message})>"
