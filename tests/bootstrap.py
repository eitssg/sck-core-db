import pytest

import boto3

from .conftest import *

import core_framework as util

from core_db.event import EventModelFactory
from core_db.item.portfolio.models import PortfolioModelFactory
from core_db.registry.client.models import ClientFactsFactory
from core_db.registry.portfolio.models import PortfolioFactsFactory
from core_db.registry.app.models import AppFactsFactory
from core_db.registry.zone.models import ZoneFactsFactory
from core_db.profile.model import ProfileModelFactory
from core_db.oauth.models import OAuthTableModelFactory

import core_logging as log


@pytest.fixture(scope="module")
def bootstrap_dynamo():

    # see environment variables in .env
    host = util.get_dynamodb_host()

    assert host == "http://localhost:8000", "DYNAMODB_HOST must be set to http://localhost:8000"

    try:
        client = util.get_client()

        if ClientFactsFactory.exists(client):
            ClientFactsFactory.delete_table(client, wait=True)
        ClientFactsFactory.create_table(client, wait=True)

        if ZoneFactsFactory.exists(client):
            ZoneFactsFactory.delete_table(client, wait=True)
        ZoneFactsFactory.create_table(client, wait=True)

        if AppFactsFactory.exists(client):
            AppFactsFactory.delete_table(client, wait=True)
        AppFactsFactory.create_table(client, wait=True)

        if PortfolioFactsFactory.exists(client):
            PortfolioFactsFactory.delete_table(client, wait=True)
        PortfolioFactsFactory.create_table(client, wait=True)

        if PortfolioModelFactory.exists(client):
            PortfolioModelFactory.delete_table(client, wait=True)
        PortfolioModelFactory.create_table(client, wait=True)

        if EventModelFactory.exists(client):
            EventModelFactory.delete_table(client, wait=True)
        EventModelFactory.create_table(client, wait=True)

        if ProfileModelFactory.exists(client):
            ProfileModelFactory.delete_table(client, wait=True)
        ProfileModelFactory.create_table(client, wait=True)

        different_client = "acme"

        if ProfileModelFactory.exists(different_client):
            ProfileModelFactory.delete_table(different_client, wait=True)
        ProfileModelFactory.create_table(different_client, wait=True)

        if OAuthTableModelFactory.exists(client):
            OAuthTableModelFactory.delete_table(client, wait=True)
        OAuthTableModelFactory.create_table(client, wait=True)

    except Exception as e:
        log.error(f"Error during bootstrap: {e}")
        assert False

    return True
