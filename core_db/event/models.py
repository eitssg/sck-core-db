""" Defines the data model and attributes stored in DynamoDB using the pynamdb interface """
from typing import Union

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
        value: Integer log level or string level name

    Returns:
        string representation of the log level
    """
    if isinstance(value, int):
        return log.getLevelName(value)
    return value


class EventModel(Model):
    """
    DynamoDB model for storing event records.

    Attributes:
        prn (str): Primary Resource Name (hash key)
        timestamp (datetime): Event timestamp (range key)
        event_type (str): Type of event (e.g., 'INFO', 'ERROR')
        item_type (str, optional): Type of item this event relates to
        status (str, optional): Status of the event
        message (str, optional): Event message details
    """

    class Meta:
        table_name = get_table_name(EVENTS)
        region = util.get_region()
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

    def __repr__(self):
        return f"<Event(prn={self.prn},timestamp={self.timestamp},item_type={self.item_type},status={self.status},message={self.message})>"
