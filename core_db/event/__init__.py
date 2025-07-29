"""The Event module contains the function and classes to create a CRUD interface to core-automation-events DynamoDB table."""

from .models import EventModel, EventModelFactory
from .actions import EventActions

__all__ = ["EventModel", "EventActions", "EventModelFactory"]
