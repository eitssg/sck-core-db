"""Event tracking and audit trail management.

Provides event logging for deployment activities, status changes, and audit trails
using the core-automation-events DynamoDB table.

Key Classes:
    - **EventActions**: CRUD operations with filtering and querying
    - **EventModel**: PynamoDB model for event records
    - **EventModelFactory**: Client-specific event model creation

Event Types:
    - Status changes (build success/failure, deployments)
    - CRUD operations (item creation, updates, deletions)
    - System events (configuration changes, maintenance)
    - Error events (exceptions, validation failures)

Example:
    >>> from core_db.event import EventActions
    >>> event = EventActions.create(
    ...     prn="portfolio:acme:web",
    ...     event_type="create",
    ...     status="success",
    ...     message="Portfolio created successfully"
    ... )
    - **timestamp**: Precise event occurrence time (sortable)
    - **status**: Event status (success, failure, in_progress, etc.)
    - **message**: Human-readable event description
    - **event_type**: Classification of the event (status_change, crud_operation, etc.)
    - **metadata**: Additional event context and details

Examples:
    >>> from core_db.event import EventActions, EventModel, EventModelFactory

    >>> # Create a status change event
    >>> result = EventActions.create(
    ...     prn="build:acme:web-services:api:main:123",
    ...     status="success",
    ...     message="Build completed successfully",
    ...     event_type="status_change",
    ...     metadata={"duration": "2m30s", "artifacts": ["lambda.zip"]}
    ... )

    >>> # Query events for a specific PRN
    >>> events = EventActions.list_by_prn(
    ...     prn="build:acme:web-services:api:main:123"
    ... )

    >>> # Get recent events for a client
    >>> recent_events = EventActions.list_recent(
    ...     client="acme",
    ...     limit=50
    ... )

    >>> # Filter events by status and time range
    >>> from datetime import datetime, timedelta
    >>> yesterday = datetime.now() - timedelta(days=1)
    >>> failed_events = EventActions.list_by_status(
    ...     client="acme",
    ...     status="failure",
    ...     since=yesterday
    ... )

    >>> # Create client-specific event model
    >>> acme_events = EventModelFactory.get_model("acme")
    >>> event_count = acme_events.count()

    >>> # Create deployment operation event
    >>> EventActions.create(
    ...     prn="component:acme:web-services:api:main:123:lambda",
    ...     status="deployed",
    ...     message="Lambda function deployed to production",
    ...     event_type="deployment",
    ...     metadata={
    ...         "environment": "production",
    ...         "version": "1.2.3",
    ...         "region": "us-west-2"
    ...     }
    ... )

Usage Patterns:
    **Status Tracking**: Use EventActions.create() for all status changes across entities

    **Audit Queries**: Use EventActions.list_by_prn() to get complete audit trail for items

    **Monitoring**: Use EventActions.list_recent() and filtering methods for operational monitoring

    **Error Tracking**: Filter by status="failure" to identify and analyze failures

    **Performance Analysis**: Use timestamp and metadata for deployment performance metrics

Table Information:
    - **Table Name**: {client}-core-automation-events (client-specific)
    - **Hash Key**: event_id (UUID for global uniqueness)
    - **Range Key**: timestamp (for chronological sorting)
    - **GSI**: prn-timestamp-index (for PRN-based queries)
    - **GSI**: status-timestamp-index (for status-based filtering)
    - **Billing Mode**: PAY_PER_REQUEST
    - **Client Isolation**: Each client has separate event table

Common Query Patterns::

        # Get all events for a build
        build_events = EventActions.list_by_prn("build:acme:api:main:123")

        # Get recent failures across all portfolios
        failures = EventActions.list_by_status("acme", "failure", limit=100)

        # Get events for entire portfolio hierarchy
        portfolio_events = EventActions.list_by_prn_prefix("portfolio:acme:web")

        # Get deployment events in time range
        from datetime import datetime
        start = datetime(2025, 1, 1)
        end = datetime(2025, 1, 31)
        deployments = EventActions.list_by_timerange("acme", start, end)

Integration with Other Modules:
    Events are automatically created by:
    - **dbhelper.update_status()**: Creates events for all status updates
    - **Item Actions**: CRUD operations on portfolios, apps, branches, builds, components
    - **Registry Actions**: Configuration changes and client management
    - **Deployment Operations**: Build processes, component deployments, status changes

Event Metadata Examples:
    Different event types include specific metadata::

        # Build events
        metadata = {
            "commit_sha": "abc123",
            "branch": "main",
            "duration": "2m30s",
            "tests_passed": 45,
            "coverage": "92%"
        }

        # Deployment events
        metadata = {
            "environment": "production",
            "region": "us-west-2",
            "version": "1.2.3",
            "rollback_version": "1.2.2"
        }

        # Error events
        metadata = {
            "error_type": "ValidationError",
            "error_code": "INVALID_PRN",
            "stack_trace": "Full exception trace..."
        }

Validation Rules:
    - Event ID must be valid UUID format
    - PRN must follow valid PRN format patterns
    - Timestamp must be valid ISO datetime
    - Status must be from allowed status constants
    - Message must be non-empty string
    - Metadata must be valid JSON-serializable dict

Error Handling:
    All operations may raise:
    - NotFoundException: Event not found for retrieval operations
    - BadRequestException: Invalid event data, PRN format, or query parameters
    - ConflictException: Duplicate event ID (rare with UUID generation)
    - UnauthorizedException: Missing or invalid authentication
    - ForbiddenException: Insufficient permissions for client event access

Performance Considerations:
    - **Indexing**: Use appropriate GSIs for efficient querying
    - **Time Ranges**: Limit query time ranges to avoid expensive scans
    - **Pagination**: Use limit parameters for large result sets
    - **Client Isolation**: Event tables are client-specific for performance and security
    - **Retention**: Consider implementing TTL for long-term event cleanup

Note:
    Events provide the primary audit trail for the entire Simple Cloud Kit system.
    They should be created for all significant operations and status changes to
    ensure complete traceability and debugging capability.
"""

from .models import EventItem, EventModel, EventModelFactory
from .actions import EventActions

__all__ = ["EventItem", "EventModel", "EventActions", "EventModelFactory"]
