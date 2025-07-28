"""Defines the data model and attributes stored in DynamoDB using the pynamdb interface"""

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

    Args:
        value (Union[int, str]): Integer log level or string level name

    Returns:
        str: String representation of the log level
    """
    if isinstance(value, int):
        return log.getLevelName(value)
    return value


class EventModel(Model):
    """
    DynamoDB model for storing event records.
    """

    class Meta:
        region = util.get_dynamodb_region()
        host = util.get_dynamodb_host()
        read_capacity_units = 1
        write_capacity_units = 1

    # Keys for events
    prn = UnicodeAttribute(hash_key=True)
    """str: Pipeline Reference Number (PRN) of the event (a.k.a identity) """
    timestamp = UTCDateTimeAttribute(range_key=True, default_for_new=make_default_time)
    """datetime: Timestamp of the event.  Let the system auto-generate """
    # Event details
    event_type = UnicodeAttribute(default_for_new="STATUS")
    """str: Type of event (e.g., 'INFO', 'ERROR', 'STATUS') like a LogLevel """
    item_type = UnicodeAttribute(null=True)
    """str: Type of item this event relates to such as portfolio, app, branch, build, component, account, etc. """
    status = UnicodeAttribute(null=True)
    """str: The status name.  Two possible values "ok" or "error" """
    message = UnicodeAttribute(null=True)
    """str: Event message details """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<Event(prn={self.prn},timestamp={self.timestamp},item_type={self.item_type},status={self.status},message={self.message})>"


EventModelType = Type[EventModel]


class EventModelFactory:
    """
    Factory class to create EventModel instances.
    """

    _model_cache = {}

    @classmethod
    def get_model(cls, client: str, auto_create_table: bool = True) -> EventModelType:
        """
        Get the EventModel class.

        Returns:
            EventModel: The EventModel class.
        """
        if client not in cls._model_cache:
            model_class = cls._create_model(client)
            if auto_create_table:
                cls._ensure_exists(model_class, client)
            cls._model_cache[client] = model_class

        return cls._model_cache[client]

    @classmethod
    def _ensure_exists(cls, model_class: EventModelType, client: str):
        """
        Ensure that the DynamoDB table for the model exists.

        Args:
            model_class (EventModelType): The model class to check.
            client (str): The client name.
        """
        try:
            if not model_class.exists():
                log.info("Creating events table: %s", model_class.Meta.table_name)
                model_class.create_table(wait=True)
                log.info(
                    "Successfully created events table: %s", model_class.Meta.table_name
                )
        except Exception as e:
            log.error("Error creating events table: %s", e)

    @classmethod
    def _create_model(cls, client: str) -> EventModelType:
        """
        Create an EventModel class with a specific table name based on the client.

        Args:
            client (str): The client name to use for the table name.

        Returns:
            EventModelType: A new EventModel class with the specified table name.
        """

        class EventModelClass(EventModel):
            class Meta(EventModel.Meta):
                table_name = get_table_name(EVENTS, client)

        return EventModelClass

    @classmethod
    def create_table(cls, wait: bool = True):
        """
        Create the events table if it does not exist.

        Args:
            wait (bool): Whether to wait for the table creation to complete.
        """
        model_class = cls.get_model()
        if not model_class.exists():
            log.info("Creating events table: %s", model_class.Meta.table_name)
            model_class.create_table(wait=wait)
            log.info(
                "Successfully created events table: %s", model_class.Meta.table_name
            )


class EventModelSchema(BaseModel):
    """
    Pydantic model representing an Event.
    """

    prn: str = Field(
        ..., description="Pipeline Reference Number (PRN) of the event (a.k.a identity)"
    )
    timestamp: datetime = Field(
        description="Timestamp of the event. Let the system auto-generate",
        default_factory=datetime.now,
    )
    event_type: str = Field(
        description="Type of event (e.g., 'INFO', 'ERROR', 'STATUS')", default="STATUS"
    )
    item_type: Optional[str] = Field(
        None,
        description="Type of item this event relates to such as portfolio, app, branch, build, component, account, etc.",
    )
    status: Optional[str] = Field(
        None, description='The status name. Two possible values "ok" or "error"'
    )
    message: Optional[str] = Field(None, description="Event message details")

    class Config:
        orm_mode = True

    def __repr__(self):
        return f"<Event(prn={self.prn},timestamp={self.timestamp},item_type={self.item_type},status={self.status},message={self.message})>"
