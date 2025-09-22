"""Zone registry actions for the core-automation-registry DynamoDB table.

This module provides comprehensive CRUD operations for zone management within the registry
system. Zones represent deployment regions or environments within client-portfolio structures
and provide configuration isolation for different deployment contexts.

Key Features:
    - **Zone Lifecycle Management**: Complete CRUD operations for zone entities
    - **Client-Zone Hierarchy**: Proper hierarchical organization within client namespaces
    - **Flexible Parameter Handling**: Supports various zone identifier formats
    - **Comprehensive Error Handling**: Detailed exception mapping for different failure scenarios
    - **Client Isolation**: Factory pattern ensures proper table isolation between clients

Zone Structure:
    Zones are stored with a composite key structure:
    - **Hash Key**: client (client identifier for data partitioning)
    - **Range Key**: zone (zone name within client namespace)
    - **Attributes**: Zone-specific metadata and configuration

Examples:
    >>> from core_db.registry.zone.actions import ZoneActions

    >>> # Create a new zone
    >>> result = ZoneActions.create(
    ...     client="acme",
    ...     zone="us-east-1-prod",
    ...     description="Production environment in US East",
    ...     region="us-east-1",
    ...     environment_type="production"
    ... )

    >>> # List all zones for a client
    >>> zones = ZoneActions.list(client="acme")
    >>> for zone in zones.data:
    ...     print(f"Zone: {zone['Zone']}")
    ...     print(f"Description: {zone.get('description')}")

    >>> # Get specific zone
    >>> zone = ZoneActions.get(client="acme", zone="us-east-1-prod")
    >>> print(f"Region: {zone.data.get('region')}")

    >>> # Update zone configuration
    >>> result = ZoneActions.patch(
    ...     client="acme",
    ...     zone="us-east-1-prod",
    ...     description="Updated: Production environment with enhanced monitoring",
    ...     monitoring_enabled=True
    ... )

Related Modules:
    - core_db.registry.zone.models: ZoneFactsModel and factory for table management
    - core_db.registry.actions: Base RegistryAction class with common functionality
    - core_db.registry: Registry system for deployment automation patterns

Note:
    All methods expect kwargs containing merged parameters from HTTP requests.
    Client and zone parameters are required for most operations and are extracted from kwargs.
"""

from typing import List, Tuple, Any

import core_logging as log

from core_framework.time_utils import make_default_time

from pydantic_core import ValidationError
from pynamodb.exceptions import (
    PutError,
    ScanError,
    DeleteError,
    UpdateError,
    DoesNotExist,
)
from pynamodb.expressions.update import Action

import core_framework as util

from ...models import Paginator
from ...exceptions import (
    ConflictException,
    UnknownException,
    BadRequestException,
    NotFoundException,
)

from ..actions import RegistryAction

from .models import ZoneFact


class ZoneActions(RegistryAction):

    @classmethod
    def list(cls, *, client: str, **kwargs) -> Tuple[List[ZoneFact], Paginator]:
        log.info("Listing zones for client")

        if not client:
            log.error("Client name missing in list request")
            raise BadRequestException('Client name is required in content: { "client": "<name>", ... }')

        aws_account_id = kwargs.get("aws_account_id")

        try:
            paginator = Paginator(**kwargs)
        except (ValueError, ValidationError) as e:
            log.error("Invalid pagination parameters: %s", str(e))
            raise BadRequestException(f"Invalid pagination parameters: {str(e)}") from e

        if aws_account_id:
            return cls._list_by_aws_account(client, aws_account_id, paginator)
        else:
            return cls._list_all(client, paginator)

    @classmethod
    def _list_all(cls, client, paginator: Paginator) -> Tuple[List[ZoneFact], Paginator]:
        model_class = ZoneFact.model_class(client)

        try:
            log.debug("Querying zones for client: %s", client)

            scan_args = paginator.get_scan_args()

            results = model_class.scan(**scan_args)

            result = [ZoneFact.from_model(item) for item in results]

            paginator.last_evaluated_key = getattr(results, "last_evaluated_key", None)
            paginator.total_count = len(result)

            log.info("Found %d zones for client: %s", len(result), client)

            return result, paginator

        except ScanError as e:
            log.error("Scan error for client %s: %s", client, str(e))
            raise UnknownException(f"Failed to scan zones for client {client}: {str(e)}") from e
        except Exception as e:
            log.error("Failed to query zones for client %s: %s", client, str(e))
            raise UnknownException(f"Failed to query zones - {str(e)}") from e

    @classmethod
    def _list_by_aws_account(cls, client, aws_account_id, paginator: Paginator) -> Tuple[List[ZoneFact], Paginator]:
        model_class = ZoneFact.model_class(client)

        try:
            log.debug("Querying zones for client: %s", client)

            query_args = paginator.get_scan_args()

            # retrieve ALL zones, then we will see if it has the given AWS account ID
            results = model_class.scan(**query_args)

            data = []
            for item in results:
                if not isinstance(item, model_class) or item.account_facts.aws_account_id != aws_account_id:
                    continue
                data.append(ZoneFact.from_model(item))

            paginator.last_evaluated_key = getattr(results, "last_evaluated_key", None)
            paginator.total_count = len(data)

            log.info("Found %d zones for client: %s", len(data), client)

            return data, paginator

        except ScanError as e:
            log.error("Scan error for client %s: %s", client, str(e))
            raise UnknownException(f"Failed to scan zones for client {client}: {str(e)}") from e
        except Exception as e:
            log.error("Failed to query zones for client %s: %s", client, str(e))
            raise UnknownException(f"Failed to query zones - {str(e)}") from e

    @classmethod
    def get(cls, *, client: str, zone: str | None = None) -> ZoneFact:
        log.info("Getting zone")

        if not client:
            log.error("Client name missing in get request")
            raise BadRequestException('Client name is required in content: { "client": "<name>", ... }')

        if not zone:
            log.error("Zone name missing in get request")
            raise BadRequestException('Zone name is required in content: { "zone": "<name>", ... }')

        model_class = ZoneFact.model_class(client)

        try:
            log.debug("Retrieving zone: %s:%s", client, zone)

            item = model_class.get(zone)

            data = ZoneFact.from_model(item)

            log.info("Successfully retrieved zone: %s:%s", client, zone)

            return data

        except DoesNotExist as e:
            log.warning("Zone not found: %s:%s", client, zone)
            raise NotFoundException(f"Zone {client}:{zone} does not exist") from e

        except Exception as e:
            log.error("Failed to get zone %s:%s: %s", client, zone, str(e))
            raise UnknownException(f"Failed to get zone: {str(e)}") from e

    @classmethod
    def delete(cls, *, client: str, zone: str) -> bool:
        log.info("Deleting zone")

        if not client:
            log.error("Client name missing in get request")
            raise BadRequestException('Client name is required in content: { "client": "<name>", ... }')

        if not zone:
            log.error("Zone name missing in get request")
            raise BadRequestException('Zone name is required in content: { "zone": "<name>", ... }')

        model_class = ZoneFact.model_class(client)

        try:
            log.debug("Deleting zone: %s:%s", client, zone)

            item = model_class(zone=zone)
            item.delete(condition=model_class.zone.exists())  # Use snake_case attribute for condition

            log.info("Successfully deleted zone: %s:%s", client, zone)
            return True

        except DeleteError as e:
            if "ConditionalCheckFailedException" in str(e):
                log.warning("Zone not found for deletion: %s:%s", client, zone)
                raise NotFoundException(f"Zone {client}:{zone} does not exist or was deleted by another process") from e

            log.error("Delete error for zone %s:%s: %s", client, zone, str(e))
            raise UnknownException(f"Failed to delete zone {client}:{zone}: {str(e)}") from e

        except Exception as e:
            log.error("Failed to delete zone %s:%s: %s", client, zone, str(e))
            raise UnknownException(f"Failed to delete - {str(e)}") from e

    @classmethod
    def create(cls, *, client: str, record: ZoneFact | None = None, **kwargs) -> ZoneFact:
        log.info("Creating zone")

        if not client:
            log.error("Client name missing in get request")
            raise BadRequestException("Client name is required.")

        try:
            if not record:
                record = ZoneFact(**kwargs)
        except (ValueError, ValidationError) as e:
            log.error("Invalid zone data for %s:%s: %s", client, kwargs.get("zone"), str(e))
            raise BadRequestException(f"Invalid zone data: {kwargs}: {str(e)}") from e

        zone = record.zone

        model_class = ZoneFact.model_class(client)

        try:

            item = record.to_model(client)
            item.save(model_class.zone.does_not_exist())

            log.info("Successfully created zone: %s:%s", client, zone)

            return record

        except PutError as e:
            if "ConditionalCheckFailedException" in str(e):
                log.error("Zone already exists: %s:%s", client, zone)
                raise ConflictException(f"Zone already exists: {client}:{zone}") from e

            log.error("Save error for zone %s:%s: %s", client, zone, str(e))
            raise UnknownException(f"Failed to create zone {client}:{zone}: {str(e)}") from e

        except Exception as e:
            log.error("Failed to create zone %s:%s: %s", client, zone, str(e))
            raise UnknownException(f"Failed to create zone: {str(e)}") from e

    @classmethod
    def update(cls, *, client: str, record: ZoneFact | None = None, **kwargs) -> ZoneFact:
        log.info("Updating zone")

        return cls._update(remove_none=True, client=client, record=record, **kwargs)

    @classmethod
    def patch(cls, *, client: str, **kwargs) -> ZoneFact:
        log.info("Patching zone")

        if not client:
            log.error("Client name missing in get request")
            raise BadRequestException('Client name is required in content: { "client": "<name>", ... }')

        excluded_fields = {"client", "zone", "created_at", "updated_at"}

        zone = kwargs.get("zone")
        if not zone:
            log.error("Zone name missing in get request")
            raise BadRequestException('Zone name is required in content: { "zone": "<name>", ... }')

        remove_none = kwargs.get("remove_none", True)

        # if any of these are in the 'new' data, then we skip them because users cannot update them
        try:
            model_class = ZoneFact.model_class(client)

            current_item = ZoneFact.from_model(model_class.get(zone)).model_dump(by_alias=False, exclude_none=False)

            def should_merge(key: str, dest: Any | None, source: Any | None) -> bool:
                if key in excluded_fields:
                    return False
                if source is None and not remove_none:
                    return False
                return True

            util.deep_merge_in_place(current_item, kwargs, should_merge=should_merge)

            # Valiate our merged data
            new_item = ZoneFact(**current_item)

            item = new_item.to_model(client)
            item.updated_at = make_default_time()
            item.save()

            log.info("Successfully patched zone: %s:%s", client, zone)

            return new_item

        except DoesNotExist as e:
            raise NotFoundException(f"Zone not found: {client}:{zone}") from e

        except PutError as e:
            raise UnknownException(f"Failed to patch zone {client}:{zone}: {str(e)}") from e

        except Exception as e:
            log.error("Failed to patch zone %s:%s: %s", client, zone, str(e))
            raise UnknownException(f"Failed to patch zone: {str(e)}") from e

    @classmethod
    def _update(cls, remove_none: bool, client: str, record: ZoneFact | None = None, **kwargs) -> ZoneFact:
        log.info("Patching zone")

        if not client:
            log.error("Client name missing in get request")
            raise BadRequestException('Client name is required in content: { "client": "<name>", ... }')

        excluded_fields = {"zone", "created_at", "updated_at"}

        if record:
            values = record.model_dump(by_alias=False, exclude_none=remove_none)
        else:
            values = {k: v for k, v in kwargs.items() if k not in excluded_fields and (not remove_none or v is not None)}

        zone = kwargs.get("zone")
        if not zone:
            log.error("Zone name missing in get request")
            raise BadRequestException('Zone name is required in content: { "zone": "<name>", ... }')

        model_class = ZoneFact.model_class(client)

        try:

            attributes = model_class.get_attributes()

            actions: list[Action] = []
            for key, value in values.items():
                if key in excluded_fields:
                    continue

                if key in attributes:
                    attr = attributes[key]
                    if value is None:
                        if remove_none:
                            actions.append(attr.remove())
                    else:
                        actions.append(attr.set(value))

            actions.append(model_class.updated_at.set(make_default_time()))

            item = model_class(zone=zone)
            item.update(actions=actions, condition=model_class.zone.exists())
            item.refresh()

            return ZoneFact.from_model(item)

        except UpdateError as e:
            if "ConditionalCheckFailedException" in str(e):
                log.warning("Zone not found for patching: %s:%s", client, zone)
                raise NotFoundException(f"Zone not found: {client}:{zone}") from e

            log.error("Update error patching zone %s:%s: %s", client, zone, str(e))
            raise UnknownException(f"Failed to patch zone {client}:{zone}: Permission denied or condition check failed") from e

        except Exception as e:
            log.error("Failed to patch zone %s:%s: %s", client, zone, str(e))
            raise UnknownException(f"Unexpected error patching zone: {str(e)}") from e
