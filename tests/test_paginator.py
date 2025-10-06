import datetime
import pytest
import base64
import core_framework as util
from core_db.models import Paginator


@pytest.fixture
def cursor():
    data = {"key": "value", "key2": "value2"}
    return base64.b64encode(util.to_json(data).encode()).decode()


@pytest.fixture
def paginator_data(cursor):
    return {
        "limit": 5,
        "email_filter": "jbarwick@eits.com.sgn",
        "cursor": cursor,
        "sort": "descending",
    }


def test_paginator_initialization(paginator_data, cursor):

    paginator = Paginator(**paginator_data)

    assert paginator.email_filter == "jbarwick@eits.com.sgn"
    assert paginator.limit == 5

    assert paginator.sort == "descending"
    assert paginator.sort_forward is False

    paginator.sort = "ascending"

    assert paginator.sort == "ascending"
    assert paginator.sort_forward is True

    cursor2 = {"key2": "new_value", "key3": "new_value2"}
    cursor2_encoded = base64.b64encode(util.to_json(cursor2).encode()).decode()

    paginator.last_evaluated_key = cursor2
    assert paginator.cursor == cursor2_encoded
    assert paginator.last_evaluated_key["key2"] == "new_value"
    assert paginator.last_evaluated_key["key3"] == "new_value2"

    date = datetime.datetime(2023, 10, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    paginator.earliest_time = date
    assert paginator.earliest_time == date

    paginator.latest_time = date
    assert paginator.latest_time == date

    date1 = datetime.datetime(2023, 10, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)

    strdate = "2023-10-01T12:00:00Z"
    paginator.earliest_time = strdate
    assert paginator.earliest_time == date1

    paginator.latest_time = strdate
    assert paginator.latest_time == date1
