import os
import pytest

from pydantic import BaseModel

import core_framework as util

from core_db.dbhelper import actions_routes

from .test_table_actions_data import test_data

from core_db.event.models import EventModelFactory
from core_db.registry.client.models import ClientFactsFactory
from core_db.registry.portfolio.models import PortfolioFactsFactory
from core_db.registry.app.models import AppFactsFactory
from core_db.registry.zone.models import ZoneFactsFactory

import core_logging as logging

from .bootstrap import *


def get_table_command(action: str) -> tuple[str, str]:

    i = action.rindex(":")

    assert i > 0

    return action[:i], action[i + 1 :]


@pytest.mark.skip(reason="This test is skipped by default. Enable it if you want to run it.")
@pytest.mark.parametrize("request_data,expected_result", test_data)
def test_table_actions(bootstrap_dynamo, request_data, expected_result):

    try:
        logging.debug(f"Environment: {os.environ}")
        logging.debug(f"request_data: {request_data}")

        client = util.get_client()

        assert client is not None

        # see environment variables in .env
        assert client == "test-client"

        # "action": "portfolio:create", "data": {"prn": "prn:portfolio"}
        assert "action" in request_data

        assert "data" in request_data

        action = request_data["action"]
        data = request_data["data"]

        table, cmd = get_table_command(action)

        assert table in actions_routes

        klazz = actions_routes[table]

        assert klazz is not None

        assert hasattr(klazz, cmd)

        method = getattr(klazz, cmd)

        assert method is not None

        response = method(client=client, **data)

        assert isinstance(response, BaseModel)

        response_data = response.model_dump()

        expected_data = expected_result.get("data", None)

        assert expected_data is not None

        if isinstance(response_data, dict):
            check_dictionary(response_data, expected_data)

        elif isinstance(response_data, list):
            assert len(response_data) == len(expected_data)
            for i in range(0, len(expected_data)):
                data = response_data[i]
                if isinstance(data, dict):
                    check_dictionary(data, expected_data[i])
                elif isinstance(data, str):
                    assert data == expected_data[i]

        elif isinstance(response_data, str):
            assert response_data == expected_data

    except AssertionError as e:
        logging.error(f"AssertionError: {e}")
        # Output all the details of the error
        errors = getattr(e, "errors", [])
        for error in errors:
            logging.error(f"Error: {error}")
        assert False, f"AssertionError: {e}"
    except Exception as e:
        assert False, f"Error: {e}"


def check_dictionary(data: dict, expected_data: dict):

    for k, v in expected_data.items():
        if k == "CreatedAt" or k == "UpdatedAt":
            # These fields are datetime objects, so we can skip them in the comparison
            continue
        assert k in data
        assert data[k] == v
