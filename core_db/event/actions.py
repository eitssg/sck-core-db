from typing import Any

from datetime import datetime
import base64
import json

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

from ..exceptions import BadRequestException, ConflictException, UnknownException

from ..response import Response, SuccessResponse

from .models import EventModel

from core_framework.constants import (
    SCOPE_PORTFOLIO,
    SCOPE_APP,
    SCOPE_BRANCH,
    SCOPE_BUILD,
    SCOPE_COMPONENT,
)


class EventActions(TableActions):

    item_model = EventModel
    item_types = [
        SCOPE_PORTFOLIO,
        SCOPE_APP,
        SCOPE_BRANCH,
        SCOPE_BUILD,
        SCOPE_COMPONENT,
    ]

    @classmethod
    def get_item_type(cls, **kwargs) -> str:
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

        prn = util.generate_build_prn(kwargs)
        if not prn:
            raise ValueError(f"prn not specified: {kwargs}")

        item_type = cls.get_item_type(**kwargs)

        # Load the request data
        try:
            kwargs.pop(PRN, prn)
            kwargs[ITEM_TYPE] = item_type
            kwargs[EVENT_TYPE] = kwargs.get(
                EVENT_TYPE, log.getLevelName(log.STATUS)
            ).upper()
            event = EventModel(prn, **kwargs)

            log.debug("Saving event {}".format(event))

            event.save()
        except ValueError as e:
            raise BadRequestException(f"Invalid Event Data- {str(e)}")
        except PutError as e:
            raise ConflictException(f"Creation failed - {str(e)}")
        except Exception as e:
            raise UnknownException(f"Creation failed - {str(e)}")

        # Return the new event
        return SuccessResponse(event.attribute_values)

    @classmethod
    def delete(cls, **kwargs) -> Response:

        # Load the requested event
        try:
            prn = util.generate_build_prn(kwargs)
            event = EventModel(prn)
            event.delete()
        except DeleteError as e:
            raise BadRequestException(f"Failed to delete - {str(e)}")

        return SuccessResponse(f"Event deleted: {prn}")

    @classmethod
    def NoneIfEmpty(cls, value: Any) -> Any:
        """
        If the value is an empty string, return None, otherwise return the value
        but, first check to see if it isa valid iso8601 timestamp, if not, then return None
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

        prn = util.generate_build_prn(kwargs)
        if not prn:
            raise BadRequestException(f"prn not specified: {kwargs}")

        # set earliest_time to kwargs['earliest_time'] and seet to None if not present or length is 0
        earliest_time = cls.NoneIfEmpty(kwargs.get(EARLIEST_TIME))
        latest_time = cls.NoneIfEmpty(kwargs.get(LATEST_TIME))

        # Generate our range key condition
        if earliest_time and latest_time:
            range_key_condition = EventModel.timestamp.between(
                earliest_time, latest_time
            )
        elif earliest_time:
            range_key_condition = EventModel.timestamp >= earliest_time
        elif latest_time:
            range_key_condition = EventModel.timestamp <= latest_time
        else:
            range_key_condition = None

        date_paginator = kwargs.get(DATA_PAGINATOR)
        if date_paginator:
            last_evaluated_key = json.loads(base64.b64decode(date_paginator).decode())
        else:
            last_evaluated_key = None

        log.debug(f"Retrieving events for prn '{prn}'")

        sort_forward = kwargs.get(SORT, ASCENDING) == ASCENDING
        limit = kwargs.get(LIMIT, 100)

        results = EventModel.query(
            hash_key=prn,
            range_key_condition=range_key_condition,
            scan_index_forward=sort_forward,
            limit=limit,
            last_evaluated_key=last_evaluated_key,
        )

        events = [i.attribute_values for i in results]
        last_evaluated_key = results.last_evaluated_key
        if last_evaluated_key:
            kwargs[DATA_PAGINATOR] = base64.b64encode(
                json.dumps(last_evaluated_key).encode()
            ).decode()
        else:
            kwargs[DATA_PAGINATOR] = None

        return SuccessResponse(
            events,
            additional_data=dict(kwargs),
        )
