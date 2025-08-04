import os
import pytest

import boto3

import core_framework as util

from core_db.response import Response
from core_db.dbhelper import actions_routes

from .test_table_actions_data import test_data

from core_db.event.models import EventModelFactory
from core_db.item.models import ItemModelFactory
from core_db.registry.client.models import ClientFactsFactory
from core_db.registry.portfolio.models import PortfolioFactsFactory
from core_db.registry.app.models import AppFactsFactory
from core_db.registry.zone.models import ZoneFactsFactory

import core_logging as logging


@pytest.fixture(scope="module")
def bootstrap_dynamo():

    os.environ["CLIENT"] = "client"  # The client name for all tests should be "client"

    # see environment variables in .env
    host = util.get_dynamodb_host()

    assert host == "http://localhost:8000", "DYNAMODB_HOST must be set to http://localhost:8000"

    try:

        client_name = "client"

        dynamodb = boto3.resource("dynamodb", endpoint_url=host)

        tables = dynamodb.tables.all()
        if tables:
            # delete all tables
            for table in tables:
                logging.debug(f"Deleting table: {table.name}")
                table.delete()
                table.wait_until_not_exists()
                logging.debug(f"Table {table.name} deleted successfully.")

        ClientFacts = ClientFactsFactory.get_model(client_name)
        ClientFacts.create_table(wait=True)

        PortfolioFacts = PortfolioFactsFactory.get_model(client_name)
        PortfolioFacts.create_table(wait=True)

        AppFacts = AppFactsFactory.get_model(client_name)
        AppFacts.create_table(wait=True)

        ZoneFacts = ZoneFactsFactory.get_model(client_name)
        ZoneFacts.create_table(wait=True)

        ItemModel = ItemModelFactory.get_model(client_name)
        ItemModel.create_table(wait=True)

        EventModel = EventModelFactory.get_model(client_name)
        EventModel.create_table(wait=True)

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
        assert client == "client"

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
