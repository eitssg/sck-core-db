"""Defines the data model and attributes stored in DynamoDB using the pynamdb interface"""

from typing import Union
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
        table_name = get_table_name(EVENTS)
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
