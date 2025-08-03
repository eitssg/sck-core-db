"""Defines the list, get, create, update, delete methods for the Event table core-automation-events.

This module provides CRUD operations and utilities for managing events in the Core Automation Event table.
"""

from typing import Any

from datetime import datetime
import base64

from pynamodb.exceptions import DeleteError, PutError

import core_logging as log
import core_framework as util

from ..actions import TableActions

from ..constants import (
    PRN,
    ITEM_TYPE,
    EVENT_TYPE,
    EARLIEST_TIME,
    LATEST_TIME,
    SORT,
    LIMIT,
    DATA_PAGINATOR,
)
from ..item.actions import ASCENDING

from ..exceptions import (
    BadRequestException,
    ConflictException,
    UnknownException,
    NotFoundException,
)
from ..response import Response, SuccessResponse

from .models import EventModelFactory

from core_framework.constants import (
    SCOPE_PORTFOLIO,
    SCOPE_APP,
    SCOPE_BRANCH,
    SCOPE_BUILD,
    SCOPE_COMPONENT,
)


class EventActions(TableActions):
    """
    Implements CRUD operations for the Event table using the PynamoDB model.

    Attributes
    ----------
    event_model : EventModel
        The PynamoDB model for the event table.
    item_types : list
        List of supported item types for events.
    """

    @classmethod
    def get_event_model(cls):
        """
        Returns the PynamoDB model for the event table.

        :return: The EventModel class.
        :rtype: EventModel
        """
        return EventModelFactory.get_model(util.get_client())

    item_types = [
        SCOPE_PORTFOLIO,
        SCOPE_APP,
        SCOPE_BRANCH,
        SCOPE_BUILD,
        SCOPE_COMPONENT,
    ]

    @classmethod
    def get_item_type(cls, **kwargs) -> str:
        """
        Determines the item type for an event based on keyword arguments.

        :param kwargs: Keyword arguments containing ITEM_TYPE or PRN.
        :type kwargs: dict
        :raises ValueError: If PRN is invalid.
        :return: The item type string.
        :rtype: str
        """
        item_type = kwargs.get(ITEM_TYPE)
        if not item_type:
            prn = kwargs.get(PRN, "")
            num_sections = prn.count(":") - 1
            if not 0 <= num_sections <= 4:
                raise ValueError(f"Invalid prn: {prn}")
            item_type = cls.item_types[num_sections]

        return item_type

    @classmethod
    def create(cls, **kwargs) -> Response:
        """
        Creates a new event in the event table.

        :param kwargs: Event attributes.
        :type kwargs: dict
        :raises BadRequestException: If event data is invalid.
        :raises ConflictException: If creation fails due to a conflict.
        :raises UnknownException: For other errors.
        :return: Success response containing event data.
        :rtype: SuccessResponse
        """
        prn = util.generate_build_prn(kwargs)
        if not prn:
            raise ValueError(f"prn not specified: {kwargs}")

        item_type = cls.get_item_type(**kwargs)

        # Load the request data
        try:
            event_model = cls.get_event_model()

            kwargs.pop(PRN, prn)
            kwargs[ITEM_TYPE] = item_type
            kwargs[EVENT_TYPE] = kwargs.get(EVENT_TYPE, log.getLevelName(log.STATUS)).upper()
            event = event_model(prn, **kwargs)

            log.debug("Saving event {}".format(event))

            event.save()
        except ValueError as e:
            raise BadRequestException(f"Invalid Event Data- {str(e)}") from e
        except PutError as e:
            raise ConflictException(f"Creation failed - {str(e)}") from e
        except Exception as e:
            raise UnknownException(f"Creation failed - {str(e)}") from e

        # Return the new event
        return SuccessResponse(event.attribute_values)

    @classmethod
    def delete(cls, **kwargs) -> Response:
        """
        Deletes an event from the event table.

        :param kwargs: Event identifying attributes.
        :type kwargs: dict
        :raises BadRequestException: If deletion fails.
        :return: Success response confirming deletion.
        :rtype: SuccessResponse
        """
        # Load the requested event
        try:
            event_model = cls.get_event_model()

            prn = util.generate_build_prn(kwargs)
            event = event_model(prn)
            event.delete()
        except DeleteError as e:
            raise BadRequestException(f"Failed to delete - {str(e)}") from e

        return SuccessResponse(f"Event deleted: {prn}")

    @classmethod
    def NoneIfEmpty(cls, value: Any) -> Any:
        """
        Returns None if the value is an empty string or not a valid ISO8601 timestamp.

        :param value: Value to check.
        :type value: Any
        :return: None or the parsed datetime value.
        :rtype: Any
        """
        if isinstance(value, str):
            if len(value) > 0:
                try:
                    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
                except Exception:
                    pass
            return None
        return value

    @classmethod
    def list(cls, **kwargs) -> Response:
        """
        Lists events for a given PRN and optional time range.

        :param kwargs: Filtering and pagination options.
        :type kwargs: dict
        :raises BadRequestException: If PRN is not specified.
        :return: Success response containing a list of events.
        :rtype: SuccessResponse
        """
        prn = util.generate_build_prn(kwargs)
        if not prn:
            raise BadRequestException(f"prn not specified: {kwargs}")

        # set earliest_time to kwargs['earliest_time'] and seet to None if not present or length is 0
        earliest_time = cls.NoneIfEmpty(kwargs.get(EARLIEST_TIME))
        latest_time = cls.NoneIfEmpty(kwargs.get(LATEST_TIME))

        event_model = cls.get_event_model()

        # Generate our range key condition
        if earliest_time and latest_time:
            range_key_condition = event_model.timestamp.between(earliest_time, latest_time)
        elif earliest_time:
            range_key_condition = event_model.timestamp >= earliest_time
        elif latest_time:
            range_key_condition = event_model.timestamp <= latest_time
        else:
            range_key_condition = None

        date_paginator = kwargs.get(DATA_PAGINATOR)
        if date_paginator:
            last_evaluated_key = util.from_json(base64.b64decode(date_paginator).decode())
        else:
            last_evaluated_key = None

        log.debug(f"Retrieving events for prn '{prn}'")

        sort_forward = kwargs.get(SORT, ASCENDING) == ASCENDING
        limit = kwargs.get(LIMIT, 100)

        results = event_model.query(
            hash_key=prn,
            range_key_condition=range_key_condition,
            scan_index_forward=sort_forward,
            limit=limit,
            last_evaluated_key=last_evaluated_key,
        )

        events = [i.attribute_values for i in results]
        last_evaluated_key = results.last_evaluated_key
        if last_evaluated_key:
            kwargs[DATA_PAGINATOR] = base64.b64encode(util.to_json(last_evaluated_key).encode()).decode()
        else:
            kwargs[DATA_PAGINATOR] = None

        return SuccessResponse(
            events,
            additional_data=dict(kwargs),
        )
