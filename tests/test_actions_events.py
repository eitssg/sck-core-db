from typing import List
from datetime import datetime

import pytest

from core_framework.status import (
    INIT,
    DEPLOY_REQUESTED,
    DEPLOY_IN_PROGRESS,
    DEPLOY_COMPLETE,
    DEPLOY_FAILED,
    COMPILE_IN_PROGRESS,
    COMPILE_COMPLETE,
    COMPILE_FAILED,
    RELEASE_REQUESTED,
    RELEASE_IN_PROGRESS,
    RELEASE_COMPLETE,
    RELEASE_FAILED,
    TEARDOWN_REQUESTED,
    TEARDOWN_IN_PROGRESS,
    TEARDOWN_COMPLETE,
    TEARDOWN_FAILED,
    STATUS_LIST,
)
from pydantic.v1.json import isoformat

from core_db.event import EventActions, EventItem
from core_db.models import Paginator

from .bootstrap import *

client = util.get_client()

# Fixed: All PRNs are the same, only timestamps differ
data = [
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T14:30:45.123456Z",
        "status": "ok",
        "event_type": INIT,
        "message": "Initial deployment setup",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T14:35:45.123456Z",
        "status": "ok",
        "event_type": DEPLOY_REQUESTED,
        "message": "Deployment requested by user",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T14:40:45.123456Z",
        "status": "ok",
        "event_type": DEPLOY_IN_PROGRESS,
        "message": "Deployment in progress",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T14:45:45.123456Z",
        "status": "ok",
        "event_type": COMPILE_IN_PROGRESS,
        "message": "Code compilation started",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T14:50:45.123456Z",
        "status": "ok",
        "event_type": COMPILE_COMPLETE,
        "message": "Code compilation successful",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T14:55:45.123456Z",
        "status": "ok",
        "event_type": DEPLOY_COMPLETE,
        "message": "Deployment completed successfully",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T15:00:45.123456Z",
        "status": "ok",
        "event_type": RELEASE_REQUESTED,
        "message": "Release to production requested",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T15:05:45.123456Z",
        "status": "ok",
        "event_type": RELEASE_IN_PROGRESS,
        "message": "Release process initiated",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T15:10:45.123456Z",
        "status": "ok",
        "event_type": RELEASE_COMPLETE,
        "message": "Release completed successfully",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T15:15:45.123456Z",
        "event_type": DEPLOY_FAILED,
        "status": "error",
        "message": "Deployment failed due to configuration error",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T15:20:45.123456Z",
        "status": "error",
        "event_type": COMPILE_FAILED,
        "message": "Compilation failed - syntax errors detected",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T15:25:45.123456Z",
        "status": "error",
        "event_type": RELEASE_FAILED,
        "message": "Release failed - rollback initiated",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T15:30:45.123456Z",
        "status": "ok",
        "event_type": TEARDOWN_REQUESTED,
        "message": "Environment teardown requested",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T15:35:45.123456Z",
        "event_type": TEARDOWN_IN_PROGRESS,
        "message": "Tearing down deployment environment",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T15:40:45.123456Z",
        "status": "ok",
        "event_type": TEARDOWN_COMPLETE,
        "message": "Environment teardown completed",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T15:45:45.123456Z",
        "status": "error",
        "event_type": TEARDOWN_FAILED,
        "message": "Teardown failed - manual intervention required",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T15:50:45.123456Z",
        "status": "ok",
        "event_type": INIT,
        "message": "New deployment cycle initiated",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T15:55:45.123456Z",
        "status": "ok",
        "event_type": DEPLOY_REQUESTED,
        "message": "Second deployment attempt requested",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T16:00:45.123456Z",
        "status": "ok",
        "event_type": COMPILE_IN_PROGRESS,
        "message": "Recompiling with bug fixes",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T16:05:45.123456Z",
        "status": "ok",
        "event_type": COMPILE_COMPLETE,
        "message": "Compilation successful after fixes",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T16:10:45.123456Z",
        "status": "ok",
        "event_type": DEPLOY_IN_PROGRESS,
        "message": "Deploying fixed version",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T16:15:45.123456Z",
        "status": "ok",
        "event_type": DEPLOY_COMPLETE,
        "message": "Fixed version deployed successfully",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T16:20:45.123456Z",
        "status": "ok",
        "event_type": RELEASE_REQUESTED,
        "message": "Production release of fixed version",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T16:25:45.123456Z",
        "status": "ok",
        "event_type": RELEASE_IN_PROGRESS,
        "message": "Rolling out to production servers",
    },
    {
        "prn": "prn:portfolio:app:branch:build:1.2.0",
        "timestamp": "2024-01-15T16:30:45.123456Z",
        "status": "ok",
        "event_type": RELEASE_COMPLETE,
        "message": "Production release completed successfully",
    },
]


def test_create_all_events_and_test_pagination(bootstrap_dynamo):
    """Test creating all 25 events and then testing pagination with EventActions.list().

    This test:
    1. Creates all 25 event records in the database with the same PRN
    2. Uses EventActions.list() with PRN filter and pagination
    3. Verifies pagination cursor functionality
    4. Validates that the 6th record is returned as first item on second page

    Args:
        client: Client identifier from test fixture
    """
    created_events: List[EventItem] = []
    failed_events: List[EventItem] = []

    print(f"🚀 Starting test: Creating all {len(data)} events...")

    # Step 1: Create all 25 events with same PRN
    for i, event_data in enumerate(data):
        try:

            # Call EventActions.create()
            response: EventItem = EventActions.create(client=client, **event_data)

            # Verify the created event data matches input
            assert response.prn == event_data["prn"], f"Record {i}: PRN mismatch"
            assert response.event_type == event_data["event_type"], f"Record {i}: Status mismatch"
            assert response.message == event_data["message"], f"Record {i}: Message mismatch"

            created_events.append(response)
            print(f"✅ Created event {i+1}/25: {event_data['prn']} - {event_data['event_type']}")

        except Exception as e:
            failed_events.append({"index": i, "event_data": event_data, "error": str(e)})
            print(f"❌ Failed to create event {i+1}/25: {event_data['prn']} - Error: {str(e)}")

    # Assert all events were created successfully
    assert len(failed_events) == 0, f"Failed to create {len(failed_events)} events: {failed_events}"
    assert len(created_events) == 25, f"Expected 25 events created, got {len(created_events)}"

    print(f"\n🎉 Successfully created all {len(created_events)} events!")

    # Step 2: Test pagination with EventActions.list()
    print(f"\n📄 Testing pagination with EventActions.list()...")

    # First page: Get first 5 events for the PRN
    print(f"🔍 First page: Getting first 5 events with PRN filter...")

    prn = "prn:portfolio:app:branch:build:1.2.0"

    paginator: Paginator = None

    # Fixed: Use correct parameter signature for EventActions.list()
    first_page_events, paginator = EventActions.list(client=client, prn=prn, limit=5)

    # Verify first page response
    assert isinstance(first_page_events, list), "First page: Response data should be a list"

    print(f"📊 First page returned {len(first_page_events)} events")

    # Should have 5 events since we created 25 with same PRN
    assert len(first_page_events) == 5, f"Expected 5 events on first page, got {len(first_page_events)}"

    # Verify metadata structure
    print(f"📈 First page metadata: {paginator.cursor}")

    # Check if cursor is populated (should be since we have 25 records and limit is 5)
    cursor_value = paginator.cursor

    # Should have more pages since we have 25 records
    assert cursor_value is not None, "Cursor should be populated since we have more than 5 records"

    print(f"🔗 Cursor found: {cursor_value[:50]}... (truncated)")
    print(f"📄 Testing second page with cursor...")

    second_page_events, paginator = EventActions.list(client=client, prn=prn, cursor=cursor_value, limit=5)
    assert isinstance(second_page_events, list), "Second page: Response data should be a list"
    assert paginator.cursor is not None, "Second page: Cursor should be populated"

    # Verify second page response
    assert second_page_events is not None, "Second page: Response data should not be None"
    assert isinstance(second_page_events, list), "Second page: Response data should be a list"

    print(f"📊 Second page returned {len(second_page_events)} events")

    # Should have 5 more events
    assert len(second_page_events) == 5, f"Expected 5 events on second page, got {len(second_page_events)}"

    # Verify we got different events (no duplicates from first page)
    first_page_timestamps = {event.timestamp for event in first_page_events}
    second_page_timestamps = {event.timestamp for event in second_page_events}

    # Check for duplicates (there shouldn't be any)
    overlapping_timestamps = first_page_timestamps.intersection(second_page_timestamps)
    assert len(overlapping_timestamps) == 0, f"Found duplicate timestamps between pages: {overlapping_timestamps}"

    print(f"✅ No duplicate events between first and second page")

    # Step 4: Validate that the first event on second page is the 6th record (index 5)
    # Since events are ordered by timestamp, the 6th event should be data[5]
    expected_sixth_event = created_events[5]  # Index 5 = 6th record
    actual_sixth_event = second_page_events[0]  # First event on second page

    print(f"🕒 Expected 6th event (data[5]):")
    print(f"   Timestamp: {expected_sixth_event.timestamp}")
    print(f"   Status: {expected_sixth_event.event_type}")
    print(f"   Message: {expected_sixth_event.message}")

    print(f"🕒 Actual first event on second page:")
    print(f"   Timestamp: {actual_sixth_event.timestamp}")
    print(f"   Status: {actual_sixth_event.event_type}")
    print(f"   Message: {actual_sixth_event.message}")

    assert actual_sixth_event.timestamp == expected_sixth_event.timestamp, "Timestamp should match 6th record"
    assert actual_sixth_event.event_type == expected_sixth_event.event_type, "Status should match 6th record"
    assert actual_sixth_event.message == expected_sixth_event.message, "Message should match 6th record"

    print(f"✅ Verified: First event on second page is the 6th record from test data!")

    print(f"📈 Second page metadata: {paginator.get_metadata()}")

    print(f"✅ Pagination test completed successfully!")


def test_create_single_event_basic():
    """Test creating a single event record for basic functionality."""

    event_data = {
        "prn": "prn:test:single:event:build:1.0.0",
        "timestamp": "2024-01-15T12:00:00.000000Z",
        "event_type": INIT,
        "message": "Single event test",
    }

    response: EventItem = EventActions.create(client=client, **event_data)

    # Verify response
    assert response.prn == event_data["prn"]
    assert response.event_type == event_data["event_type"]
    assert response.message == event_data["message"]

    print(f"✅ Single event creation test passed")


def test_list_events_basic():
    """Test basic EventActions.list() functionality."""

    # Create a test event first
    event_data = {
        "prn": "prn:test:list:basic:build:1.0.0",
        "timestamp": "2024-01-15T12:00:00Z",
        "event_type": INIT,
        "message": "List test event",
    }

    create_response: EventItem = EventActions.create(client=client, **event_data)
    assert isinstance(create_response, EventItem)

    # Test EventActions.list() with correct parameters
    list_response, paginator = EventActions.list(
        client=client,
        prn="prn:test:list:basic:build:1.0.0",
        limit=10,
        # cursor not provided for first page
    )

    # Verify response
    assert isinstance(list_response, list)
    assert len(list_response) >= 1, "Should have at least the event we just created"

    # Verify the event we created is in the results
    found_event = None
    for event in list_response:
        if event.timestamp == datetime.fromisoformat(event_data["timestamp"]):
            found_event = event
            break

    assert found_event is not None, "Should find the event we created"
    assert found_event.prn == event_data["prn"]
    assert found_event.event_type == event_data["event_type"]
    assert found_event.message == event_data["message"]

    print(f"✅ Basic list test passed")


def test_list_events_with_date_range():
    earliest_date = "2024-01-15T15:35:45.123456Z"
    latest_date = "2024-01-15T15:45:45.123456Z"

    # Test EventActions.list() with date range
    list_response, paginator = EventActions.list(
        client=client,
        prn="prn:portfolio:app:branch:build:1.2.0",
        limit=10,
        earliest_time=earliest_date,
        latest_time=latest_date,
    )

    # Verify response
    assert isinstance(list_response, list)
    assert len(list_response) == 3, "Should have only the three events in the date range"

    print(f"✅ Date range list test passed")
