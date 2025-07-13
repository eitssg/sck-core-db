"""Defines the list, get, create, update, delete methods for the Event table core-automation-events"""

from typing import Any

from datetime import datetime
import base64
import json

from pynamodb.exceptions import DeleteError, PutError

import core_logging as log
import core_framework as util
import core_helper.aws as aws

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
from ..config import get_table_name
from ..constants import EVENTS
from ..response import Response, SuccessResponse

from .models import EventModel, EventModelSchema

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
            raise BadRequestException(f"Invalid Event Data- {str(e)}") from e
        except PutError as e:
            raise ConflictException(f"Creation failed - {str(e)}") from e
        except Exception as e:
            raise UnknownException(f"Creation failed - {str(e)}") from e

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
            raise BadRequestException(f"Failed to delete - {str(e)}") from e

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


class EventService(TableActions):
    """
    Service class implementing the TableActions interface for CRUD operations on the Event table.
    All methods accept keyword arguments corresponding to the EventModelSchema fields.
    """

    def __init__(self):
        # Get the DynamoDB resource and table name from utility methods.
        region_name = util.get_dynamodb_region()
        self.dynamodb = aws.dynamodb_resource(region_name=region_name)
        self.table = self.dynamodb.Table(get_table_name(EVENTS))

    @classmethod
    def create(cls, **kwargs) -> Response:
        """
        Creates a new event record in DynamoDB.
        Expects all event fields as keyword arguments.
        """
        try:
            instance = cls()

            # Validate input against the Pydantic schema.
            event = EventModelSchema(**kwargs)
            item = event.model_dump()

            # Convert datetime to ISO string before storing.
            if isinstance(item.get("timestamp"), datetime):
                item["timestamp"] = item["timestamp"].isoformat()
            instance.table.put_item(Item=item)

            return SuccessResponse(data=item)

        except Exception as e:
            raise BadRequestException(str(e))

    @classmethod
    def get(cls, **kwargs) -> Response:
        """
        Retrieves an event by its primary key.
        Expects at least 'prn' and 'timestamp' as keyword arguments.
        """
        try:
            prn = kwargs.get("prn")
            timestamp = kwargs.get("timestamp")
            if not prn or not timestamp:
                raise ValueError(
                    "Both 'prn' and 'timestamp' are required to get an item."
                )
            if isinstance(timestamp, datetime):
                timestamp = timestamp.isoformat()
            instance = cls()
            key = {"prn": prn, "timestamp": timestamp}
            response = instance.table.get_item(Key=key)
            item = response.get("Item")
            if not item:
                raise NotFoundException("Item not found")

            # Convert the timestamp string back to a datetime object.
            item["timestamp"] = datetime.fromisoformat(item["timestamp"])

            return SuccessResponse(data=item)

        except Exception as e:
            raise UnknownException(str(e)) from e

    @classmethod
    def update(cls, **kwargs) -> Response:
        """
        Updates specified attributes of an event.
        Expects 'prn' and 'timestamp' to identify the record.
        Other provided keyword arguments specify the fields to update.
        """
        try:
            prn = kwargs.get("prn")
            timestamp = kwargs.get("timestamp")
            if not prn or not timestamp:
                raise ValueError(
                    "Both 'prn' and 'timestamp' are required to update an item."
                )
            # Remove primary key fields from update parameters.
            update_data = kwargs.copy()
            update_data.pop("prn", None)
            update_data.pop("timestamp", None)
            if not update_data:
                raise ValueError("No update fields provided.")
            update_expression = "SET " + ", ".join(f"#{k} = :{k}" for k in update_data)
            expression_attribute_names = {f"#{k}": k for k in update_data}
            expression_attribute_values = {
                f":{k}": v.isoformat() if isinstance(v, datetime) else v
                for k, v in update_data.items()
            }
            if isinstance(timestamp, datetime):
                timestamp = timestamp.isoformat()
            instance = cls()
            key = {"prn": prn, "timestamp": timestamp}
            instance.table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
            )

            return SuccessResponse(data=kwargs)

        except Exception as e:
            raise BadRequestException(str(e)) from e

    @classmethod
    def delete(cls, **kwargs) -> Response:
        """
        Deletes an event from the DynamoDB table.
        Expects 'prn' and 'timestamp' as keyword arguments.
        """
        try:
            prn = kwargs.get("prn")
            timestamp = kwargs.get("timestamp")
            if not prn or not timestamp:
                raise ValueError(
                    "Both 'prn' and 'timestamp' are required to delete an item."
                )
            if isinstance(timestamp, datetime):
                timestamp = timestamp.isoformat()

            instance = cls()

            key = {"prn": prn, "timestamp": timestamp}
            instance.table.delete_item(Key=key)

            return SuccessResponse(data={"prn": prn, "timestamp": timestamp})

        except Exception as e:
            raise UnknownException(str(e)) from e

    @classmethod
    def patch(cls, **kwargs) -> Response:
        """
        Partially updates an event record.
        This method fetches the existing record, updates the specified fields, and saves it back.
        Expects 'prn' and 'timestamp' to identify the record.
        """
        try:
            # Retrieve the existing record.
            get_response = cls.get(**kwargs)

            if isinstance(get_response.data, dict):
                current_data = get_response.data
            else:
                current_data = {}

            # Merge the update fields with the current record.
            update_fields = kwargs.copy()
            update_fields.pop("prn", None)
            update_fields.pop("timestamp", None)
            updated_data = {**current_data, **update_fields}

            # Use the update method to update the record.
            cls.update(**updated_data)

            return cls.get(**kwargs)

        except Exception as e:

            raise UnknownException(str(e)) from e

    @classmethod
    def list(cls, **kwargs) -> Response:
        """
        Lists all events in the table.
        This implementation performs a full table scan.
        """
        try:
            instance = cls()

            response = instance.table.scan()
            items = response.get("Items", [])

            result = []
            for item in items:
                if "timestamp" in item:
                    item["timestamp"] = datetime.fromisoformat(item["timestamp"])
                result.append(EventModelSchema(**item))

            return SuccessResponse(data=result)

        except Exception as e:

            raise UnknownException(str(e)) from e
