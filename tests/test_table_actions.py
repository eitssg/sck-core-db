import os
import pytest
import core_framework as util

from core_db.response import Response
from core_db.dbhelper import actions_routes

from .test_table_actions_data import test_data

from core_db.event.models import EventModel
from core_db.item.models import ItemModel
from core_db.registry.client.models import ClientFacts
from core_db.registry.portfolio.models import PortfolioFacts
from core_db.registry.app.models import AppFacts
from core_db.registry.zone.models import ZoneFacts

import logging

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture(scope="module")
def bootstrap_dynamo():

    # see environment variables in .env
    host = util.get_dynamodb_host()

    assert (
        host == "http://localhost:8000"
    ), "DYNAMODB_HOST must be set to http://localhost:8000"

    try:
        if EventModel.exists():
            EventModel.delete_table()
        EventModel.create_table(wait=True)

        if ItemModel.exists():
            ItemModel.delete_table()
        ItemModel.create_table(wait=True)

        if ClientFacts.exists():
            ClientFacts.delete_table()
        ClientFacts.create_table(wait=True)

        if PortfolioFacts.exists():
            PortfolioFacts.delete_table()
        PortfolioFacts.create_table(wait=True)

        if AppFacts.exists():
            AppFacts.delete_table()
        AppFacts.create_table(wait=True)

        if ZoneFacts.exists():
            ZoneFacts.delete_table()
        ZoneFacts.create_table(wait=True)

    except Exception as e:
        print(e)
        assert False

    return True


def get_table_command(action: str) -> tuple[str, str]:

    i = action.rindex(":")

    assert i > 0

    return action[:i], action[i + 1 :]


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

        response = method(**data)

        assert isinstance(response, Response)

        assert response.status == expected_result["status"]
        assert response.code == expected_result["code"]
        assert response.data is not None

        response_data = response.data
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

    except Exception as e:
        assert False, f"Error: {e}"


def check_dictionary(data: dict, expected_data: dict):

    for k, v in expected_data.items():
        assert k in data
        assert data[k] == v
