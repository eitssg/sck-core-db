from typing import Any

import json
import base64
from datetime import datetime

from pynamodb.exceptions import DoesNotExist, DeleteError, PutError
from pynamodb.expressions.update import Action

import core_framework as util
import core_logging as log

from core_framework.time_utils import make_default_time

from ..constants import (
    EARLIEST_TIME,
    LATEST_TIME,
    DATA_PAGINATOR,
    SORT,
    ASCENDING,
    LIMIT,
    PRN,
    PARENT_PRN,
    NAME,
    UPDATED_AT,
)

from ..actions import TableActions

from ..response import (
    Response,
    SuccessResponse,
    NoContentResponse,
)
from ..exceptions import (
    BadRequestException,
    ConflictException,
    UnknownException,
    NotFoundException,
)

from .models import ItemModel


class ItemTableActions(TableActions):

    item_model = ItemModel

    @classmethod
    def validate_date(cls, date: Any) -> Any:
        if not date:
            return None
        if isinstance(date, str):
            try:
                return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                return None
        return date

    @classmethod
    def validate_prn(cls, prn: str) -> str:
        if not util.validate_item_prn(prn):
            raise BadRequestException(f"Invalid prn: {prn}")
        return prn

    @classmethod
    def create(cls, **kwargs) -> Response:
        # Load the request data
        log.debug("Received create request", kwargs)

        prn = kwargs.pop(PRN, None)

        if not prn:
            raise BadRequestException(f"A [prn] is required for this item: {kwargs}")

        if NAME not in kwargs:
            raise BadRequestException(f"A [name] for this item is required: {kwargs}")

        parent_prn = kwargs.pop(PARENT_PRN, prn[0 : prn.rindex(":")])

        item: ItemModel = cls.item_model(prn=prn, parent_prn=parent_prn, **kwargs)

        # Add the new item to the database, if it doesn't already exist
        try:
            item.save(cls.item_model.prn.does_not_exist())
        except PutError as e:
            if e.cause_response_code == "ConditionalCheckFailedException":
                raise ConflictException(f"Item [{item.prn}] already exists")
            else:
                raise BadRequestException(f"Creation failed - {str(e)}")
        except AttributeError as e:
            raise BadRequestException(f"Invalid item data: {kwargs}: {str(e)}")
        except Exception as e:
            raise UnknownException(f"Creation failed - {str(e)}")

        # Return the new item
        return SuccessResponse(item.to_simple_dict())

    @classmethod
    def delete(cls, **kwargs) -> Response:
        # Load the request data
        log.debug(f"Received delete request: {kwargs}")

        prn = kwargs.get(PRN, None)
        if not cls.validate_prn(prn):
            raise BadRequestException(f"Invalid prn: {prn}")

        # Load the requested item.  If not found, it's not an error, but return 204
        try:
            item = cls.item_model.get(prn)
        except DoesNotExist:
            return NoContentResponse(f"Item not found: {prn}")

        try:
            item.delete()
        except DeleteError as e:
            raise UnknownException(f"Failed to delete - {str(e)}")

        return SuccessResponse(f"Item deleted: {prn}")

    @classmethod
    def get(cls, **kwargs) -> Response:
        # Load the request data
        log.debug(f"Received get request: {kwargs}")

        prn = kwargs.get(PRN, None)
        if not cls.validate_prn(prn):
            raise BadRequestException(f"Invalid prn: {prn}")

        try:
            item = cls.item_model.get(prn)
        except DoesNotExist:
            raise NotFoundException(f"Item not found: {prn}")

        return SuccessResponse(item.to_simple_dict())

    @classmethod
    def list(cls, **kwargs) -> Response:

        log.debug(f"Received list request: {kwargs}")

        parent_prn = kwargs.get(PARENT_PRN, None)

        # If a parent prn has not been privded, then generated it from the prn if provided
        if not parent_prn:
            prn = kwargs.get(PRN, "prn:missing")
            cls.validate_prn(prn)
            parent_prn = prn[0 : prn.rindex(":")]

        if not util.validate_item_prn(parent_prn):
            raise BadRequestException(f"Invalid parent_prn: {parent_prn}")

        log.debug(f"Retrieving items by parent [{parent_prn}]")

        earliest_time = cls.validate_date(kwargs.get(EARLIEST_TIME, None))
        latest_time = cls.validate_date(kwargs.get(LATEST_TIME, None))

        # Generate our range key condition
        if earliest_time and latest_time:
            range_key_condition = cls.item_model.created_at.between(
                earliest_time, latest_time
            )
        elif earliest_time:
            range_key_condition = cls.item_model.created_at >= earliest_time
        elif latest_time:
            range_key_condition = cls.item_model.created_at <= latest_time
        else:
            range_key_condition = None

        pagenator = kwargs.get(DATA_PAGINATOR, None)

        if pagenator:
            last_evaluated_key = json.loads(
                base64.b64decode(pagenator).decode(encoding="utf-8")
            )
        else:
            last_evaluated_key = None

        sort_forward = kwargs.get(SORT, ASCENDING) == ASCENDING
        request_limit = kwargs.get(LIMIT, 10)

        results = cls.item_model.parent_created_at_index.query(
            hash_key=parent_prn,
            range_key_condition=range_key_condition,
            scan_index_forward=sort_forward,
            limit=request_limit,
            last_evaluated_key=last_evaluated_key,
        )

        items = [i.to_simple_dict() for i in results]
        last_evaluated_key = results.last_evaluated_key
        if last_evaluated_key:
            kwargs[DATA_PAGINATOR] = base64.b64encode(
                json.dumps(last_evaluated_key).encode(encoding="utf-8")
            ).decode(encoding="utf-8")
        else:
            kwargs[DATA_PAGINATOR] = None

        return SuccessResponse(items)

    @classmethod
    def update(cls, **kwargs) -> Response:
        # Load the request data
        log.debug("Received update request", kwargs)

        prn = kwargs.get(PRN, None)
        if not cls.validate_prn(prn):
            raise BadRequestException(f"Invalid prn: {prn}")

        # Load the requested item
        try:
            item: ItemModel = cls.item_model.get(prn)
        except DoesNotExist:
            raise NotFoundException("Item not found")

        attributes = item.get_attributes()

        # Update individual fields in the table record
        actions: list[Action] = []
        for key, value in kwargs.items():
            if value is None:
                # Generate a remove() action and delete the attribute - pynamodb doesn't do this automatically
                attr = attributes[key]
                actions.append(attr.remove())
                attr.set(None)
            elif value != getattr(item, key):
                actions.append(attributes[key].set(value))

        # Execute the updates
        try:
            if len(actions) > 0:
                actions.append(attributes[UPDATED_AT].set(make_default_time()))
                item.update(actions=actions)

                # Load the full object to ensure the update is reflected in the response
                item.refresh()
        except Exception as e:
            raise UnknownException(f"Failed to update - {e}")

        # Return the updated item
        return SuccessResponse(item.to_simple_dict())