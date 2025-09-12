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

import core_framework as util
import core_logging as log

from core_framework.time_utils import make_default_time

from pydantic_core import ValidationError
from pynamodb.exceptions import (
    PutError,
    ScanError,
    GetError,
    DeleteError,
    UpdateError,
    DoesNotExist,
)
from pynamodb.expressions.update import Action

from ...models import Paginator
from ...response import SuccessResponse, Response, NoContentResponse
from ...exceptions import (
    ConflictException,
    UnknownException,
    BadRequestException,
    NotFoundException,
)

from ..actions import RegistryAction

from .models import ZoneFact


class ZoneActions(RegistryAction):
    """Actions for managing zone registry entries.

    Provides comprehensive CRUD operations for zone management with proper error handling
    and validation. Zones represent deployment regions or environments within clients that
    provide configuration isolation for different deployment contexts.

    The class handles client-zone composite key management and supports flexible
    parameter parsing for maximum compatibility with different API patterns.

    Key Capabilities:
        - Create, read, update, delete zone registry entries
        - List zones by client with complete metadata
        - Partial updates with field-level change tracking
        - Comprehensive validation and error handling
        - Client-specific table isolation through factory pattern

    Examples:
        >>> # List zones for a client
        >>> zones = ZoneActions.list(client="acme")
        >>> print(f"Found {len(zones.data)} zones")

        >>> # Get specific zone
        >>> zone = ZoneActions.get(client="acme", zone="us-east-1-prod")
        >>> if zone.data:
        ...     print(f"Description: {zone.data.get('description')}")

        >>> # Create new zone
        >>> result = ZoneActions.create(
        ...     client="acme",
        ...     zone="eu-west-1-staging",
        ...     description="Staging environment in EU West"
        ... )

    Note:
        All methods expect kwargs containing merged parameters from HTTP requests,
        with client and zone parameters being extracted and validated for each operation.
    """

    @classmethod
    def list(cls, **kwargs) -> Response:
        """List all zones for a specific client.

        Retrieves all zone registry entries for the specified client with complete
        metadata and configuration. Results are sorted by zone name for consistent
        ordering and include full zone details.

        Args:
            **kwargs: Parameters containing client identification.

                     Required Fields:
                         client (str): Client name to list zones for.

        Returns:
            Response: SuccessResponse containing:
                - data (list): List of zone dictionaries with complete metadata
                - Sorted by Zone field for consistent ordering
                - Empty list if no zones found for the client

        Raises:
            BadRequestException: If client parameter is missing from kwargs.
            UnknownException: If database query fails due to connection issues or
                            other unexpected errors.

        """
        log.info("Listing zones for client")

        client = kwargs.get("client", kwargs.get("Client"))
        aws_account_id = kwargs.get("aws_account_id", kwargs.get("AwsAccountId"))

        if not client:
            log.error("Client name missing in list request")
            raise BadRequestException('Client name is required in content: { "client": "<name>", ... }')

        try:
            paginator = Paginator(**kwargs)
        except (ValueError, ValidationError) as e:
            log.error("Invalid pagination parameters: %s", str(e))
            raise BadRequestException(f"Invalid pagination parameters: {str(e)}") from e

        if aws_account_id:
            return cls._list_by_aws_account(client, aws_account_id)
        else:
            return cls._list_all(client, paginator)

    @classmethod
    def _list_all(cls, client, paginator: Paginator) -> Response:

        model_class = ZoneFact.model_class(client)

        try:
            log.debug("Querying zones for client: %s", client)

            query_args = {"consistent_read": True}

            if paginator.limit:
                query_args["limit"] = paginator.limit

            if paginator.cursor is not None:
                query_args["last_evaluated_key"] = paginator.cursor

            results = model_class.scan(**query_args)

            result = [ZoneFact.from_model(item).model_dump(mode="json") for item in results]

            paginator.cursor = getattr(results, "last_evaluated_key", None)
            paginator.total_count = getattr(results, "total_count", len(result))

            log.info("Found %d zones for client: %s", len(result), client)

            return SuccessResponse(data=result, metadata=paginator.get_metadata())

        except ScanError as e:
            log.error("Scan error for client %s: %s", client, str(e))
            raise UnknownException(f"Failed to scan zones for client {client}: {str(e)}") from e
        except Exception as e:
            log.error("Failed to query zones for client %s: %s", client, str(e))
            raise UnknownException(f"Failed to query zones - {str(e)}") from e

    @classmethod
    def _list_by_aws_account(cls, client, aws_account_id) -> Response:

        model_class = ZoneFact.model_class(client)

        try:
            log.debug("Querying zones for client: %s", client)

            query_args = {"consistent_read": True}

            # retrieve ALL zones, then we will see if it has the given AWS account ID
            results = model_class.scan(**query_args)

            data = []
            for item in results:
                if not isinstance(item, model_class) or item.account_facts.aws_account_id != aws_account_id:
                    continue
                data.append(ZoneFact.from_model(item).model_dump(mode="json"))

            log.info("Found %d zones for client: %s", len(data), client)

            return SuccessResponse(data=data, metadata={"total_count": len(data)})

        except ScanError as e:
            log.error("Scan error for client %s: %s", client, str(e))
            raise UnknownException(f"Failed to scan zones for client {client}: {str(e)}") from e
        except Exception as e:
            log.error("Failed to query zones for client %s: %s", client, str(e))
            raise UnknownException(f"Failed to query zones - {str(e)}") from e

    @classmethod
    def get(cls, **kwargs) -> Response:
        """Retrieve a specific zone registry entry.

        Fetches the complete configuration and metadata for a specific zone identified
        by client and zone name. Returns detailed zone information including
        deployment configuration and environment details.

        Args:
            **kwargs: Parameters identifying the specific zone.

                     Required Fields:
                         client (str): Client name.
                         zone (str): Zone name to retrieve.

        Returns:
            Response: SuccessResponse containing complete zone data dictionary,
                     or NoContentResponse if zone not found.

        Raises:
            BadRequestException: If required client or zone parameters are missing.
            UnknownException: If database operation fails due to connection issues,
                            table access problems, or permission issues.

        """
        log.info("Getting zone")

        client = kwargs.get("client", kwargs.get("Client"))
        if not client:
            log.error("Client name missing in get request")
            raise BadRequestException('Client name is required in content: { "client": "<name>", ... }')

        zone = kwargs.get("zone", kwargs.get("Zone"))
        if not zone:
            log.error("Zone name missing in get request")
            raise BadRequestException('Zone name is required in content: { "zone": "<name>", ... }')

        model_class = ZoneFact.model_class(client)

        try:
            log.debug("Retrieving zone: %s:%s", client, zone)

            item = model_class.get(zone)

            data = ZoneFact.from_model(item).model_dump(mode="json")

            log.info("Successfully retrieved zone: %s:%s", client, zone)

            return SuccessResponse(data=data)

        except DoesNotExist as e:
            log.warning("Zone not found: %s:%s", client, zone)
            return NoContentResponse(message=f"Zone {client}:{zone} does not exist")
        except Exception as e:
            log.error("Failed to get zone %s:%s: %s", client, zone, str(e))
            raise UnknownException(f"Failed to get zone: {str(e)}") from e

    @classmethod
    def delete(cls, **kwargs) -> Response:
        """Delete a zone registry entry.

        Removes the specified zone from the client's registry. Returns success
        confirmation or handles not found scenarios gracefully with NoContentResponse.

        Args:
            **kwargs: Parameters identifying the zone to delete.

                     Required Fields:
                         client (str): Client name.
                         zone (str): Zone name to delete.

        Returns:
            Response: SuccessResponse with deletion confirmation message,
                     or NoContentResponse if zone not found.

        Raises:
            BadRequestException: If required client or zone parameters are missing.
            UnknownException: If database operation fails during retrieval or deletion.

        """
        log.info("Deleting zone")

        client = kwargs.get("client", kwargs.get("Client"))
        if not client:
            log.error("Client name missing in get request")
            raise BadRequestException('Client name is required in content: { "client": "<name>", ... }')

        zone = kwargs.get("zone", kwargs.get("Zone"))
        if not zone:
            log.error("Zone name missing in get request")
            raise BadRequestException('Zone name is required in content: { "zone": "<name>", ... }')

        model_class = ZoneFact.model_class(client)

        try:
            log.debug("Deleting zone: %s:%s", client, zone)

            item = model_class(zone=zone)
            item.delete(condition=model_class.zone.exists())  # Use snake_case attribute for condition

            log.info("Successfully deleted zone: %s:%s", client, zone)
            return SuccessResponse(message=f"Zone deleted: {client}:{zone}")

        except DeleteError as e:
            if "ConditionalCheckFailedException" in str(e):
                log.warning("Zone not found for deletion: %s:%s", client, zone)
                return NoContentResponse(message=f"Zone not found: {client}:{zone}")
            log.error("Delete error for zone %s:%s: %s", client, zone, str(e))
            raise UnknownException(f"Failed to delete zone {client}:{zone}: {str(e)}") from e
        except Exception as e:
            log.error("Failed to delete zone %s:%s: %s", client, zone, str(e))
            raise UnknownException(f"Failed to delete - {str(e)}") from e

    @classmethod
    def create(cls, **kwargs) -> Response:
        """Create a new zone registry entry.

        Creates a new zone within the specified client with the provided configuration
        and metadata. Fails if a zone with the same client-zone combination already
        exists, ensuring unique zone names within each client namespace.

        Args:
            **kwargs: Parameters for zone creation.

                     Required Fields:
                         client (str): Client name.
                         zone (str): Unique zone name within client.

                     Optional Zone Attributes:
                         description (str): Human-readable zone description.
                         region (str): AWS region for the zone.
                         environment_type (str): Environment type (development, staging, production).
                         vpc_id (str): VPC identifier for the zone.
                         subnet_ids (list): List of subnet identifiers.
                         security_group_ids (list): List of security group identifiers.
                         availability_zones (list): List of availability zones.
                         monitoring_enabled (bool): Whether monitoring is enabled.
                         backup_retention_days (int): Backup retention period in days.
                         custom_fields: Any additional zone-specific attributes.

        Returns:
            Response: SuccessResponse containing the created zone data with all fields.

        Raises:
            BadRequestException: If required parameters are missing, have invalid format,
                               or zone data validation fails.
            ConflictException: If zone already exists with the same client-zone
                             combination.
            UnknownException: If database operation fails due to connection issues or
                            other unexpected errors.

        Examples:
            >>> # Create basic zone
            >>> result = ZoneActions.create(
            ...     client="acme",
            ...     zone="us-east-1-dev",
            ...     description="Development environment in US East",
            ...     region="us-east-1",
            ...     environment_type="development"
            ... )
            >>> zone_data = result.data
            >>> print(f"Created: {zone_data['Zone']}")

            >>> # Create zone with full network configuration
            >>> result = ZoneActions.create(
            ...     client="acme",
            ...     zone="eu-west-1-prod",
            ...     description="Production environment in EU West",
            ...     region="eu-west-1",
            ...     environment_type="production",
            ...     vpc_id="vpc-12345678",
            ...     subnet_ids=["subnet-abcd1234", "subnet-efgh5678"],
            ...     security_group_ids=["sg-web-prod", "sg-app-prod"],
            ...     availability_zones=["eu-west-1a", "eu-west-1b", "eu-west-1c"],
            ...     monitoring_enabled=True,
            ...     backup_retention_days=30
            ... )

            >>> # Handle conflict (duplicate creation)
            >>> try:
            ...     ZoneActions.create(
            ...         client="acme",
            ...         zone="us-east-1-dev"  # Already exists
            ...     )
            ... except ConflictException as e:
            ...     print(f"Zone already exists: {e}")

            >>> # Handle validation errors
            >>> try:
            ...     ZoneActions.create(client="acme")  # Missing zone name
            ... except BadRequestException as e:
            ...     print(f"Validation error: {e}")

        Zone Schema:
            Created zones include these standard fields:
            - Client: Hash key (client identifier)
            - Zone: Range key (zone name)
            - description: Optional zone description
            - region: Optional AWS region
            - environment_type: Optional environment classification
            - vpc_id: Optional VPC identifier
            - subnet_ids: Optional list of subnet identifiers
            - Custom fields: Any additional fields provided in kwargs

        Database Operations:
            - Uses DynamoDB PutItem with condition expression
            - Condition prevents overwriting existing zones
            - All provided fields stored as zone attributes
            - Atomic operation ensures data consistency

        Validation Notes:
            - Client-zone combination uniqueness enforced at database level
            - Zone name format validation can be added in model layer
            - Region validation recommended against AWS region list
        """
        log.info("Creating zone")

        client = kwargs.get("client", kwargs.get("Client"))
        if not client:
            log.error("Client name missing in get request")
            raise BadRequestException('Client name is required in content: { "client": "<name>", ... }')

        zone = kwargs.get("zone", kwargs.get("Zone"))
        if not zone:
            log.error("Zone name missing in get request")
            raise BadRequestException('Zone name is required in content: { "zone": "<name>", ... }')

        model_class = ZoneFact.model_class(client)

        try:
            data = ZoneFact(**kwargs)  # Validate and parse input data
        except (ValueError, ValidationError) as e:
            log.error("Invalid zone data for %s:%s: %s", client, zone, str(e))
            raise BadRequestException(f"Invalid zone data: {kwargs}: {str(e)}") from e

        try:

            item = data.to_model(client)
            item.save(model_class.zone.does_not_exist())

            log.info("Successfully created zone: %s:%s", client, zone)

            return SuccessResponse(data=data.model_dump(mode="json"))

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
    def update(cls, **kwargs) -> Response:
        """Create or completely replace a zone registry entry (PUT semantics).

        Performs a complete replacement of zone data, creating the zone if it
        doesn't exist or completely replacing it if it does. All provided fields become
        the new zone configuration, removing any previously set fields not included.

        Args:
            **kwargs: Complete zone configuration parameters.

                     Required Fields:
                         client (str): Client name.
                         zone (str): Zone name.

                     Zone Attributes:
                         All desired zone fields. Missing fields will not be
                         present in the updated zone (complete replacement).

        Returns:
            Response: SuccessResponse containing the complete updated zone data.

        Raises:
            BadRequestException: If required client or zone parameters are missing.
            UnknownException: If database operation fails due to connection issues or
                            other unexpected errors.

        Examples:
            >>> # Complete zone replacement
            >>> result = ZoneActions.update(
            ...     client="acme",
            ...     zone="us-east-1-staging",
            ...     description="Updated: Enhanced staging environment",
            ...     region="us-east-1",
            ...     environment_type="staging",
            ...     vpc_id="vpc-new12345",
            ...     monitoring_enabled=True
            ... )
            >>> # All previous fields replaced with above configuration

            >>> # Create new zone (doesn't exist)
            >>> result = ZoneActions.update(
            ...     client="acme",
            ...     zone="ap-southeast-1-test",
            ...     description="Test environment in Asia Pacific",
            ...     region="ap-southeast-1",
            ...     environment_type="testing"
            ... )
            >>> print("Zone created via update")

            >>> # Update existing zone (complete replacement)
            >>> result = ZoneActions.update(
            ...     client="testcorp",
            ...     zone="us-west-2-dev",
            ...     description="Development environment only"
            ...     # Note: This removes all other previously set fields
            ... )

            >>> # Error handling
            >>> try:
            ...     ZoneActions.update(client="acme")  # Missing zone parameter
            ... except BadRequestException as e:
            ...     print(f"Parameter error: {e}")

        Update Behavior:
            **Complete Replacement (PUT Semantics):**
            - Creates zone if it doesn't exist
            - Completely replaces existing zone data
            - Only fields provided in kwargs will exist in updated zone
            - Previously set fields not included in kwargs are removed
            - Atomic operation ensures data consistency

        Comparison with patch():
            - update(): Complete replacement (PUT semantics)
            - patch(): Partial update (PATCH semantics)
            - Use update() when providing complete new configuration
            - Use patch() when modifying specific fields only

        Database Operations:
            - Uses DynamoDB PutItem operation (create or replace)
            - No conditional checks (overwrites existing data)
            - All kwargs fields become the complete zone data
            - Existence check performed only for logging purposes
        """
        log.info("Updating zone")

        return cls._update(remove_none=True, **kwargs)

    @classmethod
    def patch(cls, **kwargs) -> Response:
        """Partially update a zone registry entry (PATCH semantics).

        Updates only the specified fields of a zone while preserving all other existing
        data. This is the ONLY model of the five that allow for DEEP replacement.  Meaning
        you can patch attributes below the top level database attributes.

        Args:
            **kwargs: Partial zone update parameters.

                     Required Fields:
                         client (str): Client name.
                         zone (str): Zone name.

                     Optional Update Fields:
                         Any zone attribute fields to update.
                         Set field to None to remove it from the zone.
                         Only modified fields will be updated in the database.

        Returns:
            Response: SuccessResponse containing the complete updated zone data
                     with all fields (modified and unchanged).

        Raises:
            BadRequestException: If required client or zone parameters are missing.
            UnknownException: If database operation fails due to connection issues,
                            table access problems, or permission issues.

        """
        log.info("Patching zone")

        remove_none = False

        client = kwargs.get("client", kwargs.get("Client"))
        if not client:
            log.error("Client name missing in get request")
            raise BadRequestException('Client name is required in content: { "client": "<name>", ... }')

        zone = kwargs.get("zone", kwargs.get("Zone"))
        if not zone:
            log.error("Zone name missing in get request")
            raise BadRequestException('Zone name is required in content: { "zone": "<name>", ... }')

        # if any of these are in the 'new' data, then we skip them because users cannot update them
        excluded_fields = {"client", "zone", "created_at", "updated_at"}
        try:
            model_class = ZoneFact.model_class(client)

            item = model_class.get(zone)
            current_data = ZoneFact.from_model(item).model_dump(by_alias=False, exclude_none=False)
            new_data = ZoneFact.model_construct(**kwargs).model_dump(by_alias=False, exclude_none=False, exclude=excluded_fields)

            def update_current_data(current: dict, new: dict) -> dict:
                """Update current field with new value or remove if None."""
                for key, value in new.items():
                    if value is None:
                        # If patch, then skip (remove_none=False).  If update, then remove it
                        if remove_none:
                            current[key] = None
                    elif isinstance(value, dict) and key in current:
                        current[key] = update_current_data(current[key], value)
                    else:
                        current[key] = value
                return current

            update_current_data(current_data, new_data)

            item = model_class(**current_data)
            item.updated_at = make_default_time()
            item.save()

            data = ZoneFact.from_model(item).model_dump(mode="json")

            log.info("Successfully patched zone: %s:%s", client, zone)

            return SuccessResponse(data=data)

        except DoesNotExist as e:
            raise NotFoundException(f"Zone not found: {client}:{zone}") from e
        except PutError as e:
            raise UnknownException(f"Failed to patch zone {client}:{zone}: {str(e)}") from e
        except Exception as e:
            log.error("Failed to patch zone %s:%s: %s", client, zone, str(e))
            raise UnknownException(f"Failed to patch zone: {str(e)}") from e

    @classmethod
    def _update(cls, remove_none: bool = True, **kwargs) -> Response:
        """Internal method for updating zone records with configurable semantics.

            Handles both PUT (complete replacement) and PATCH (partial update) semantics
            based on the remove_none parameter. Uses DynamoDB update operations with
            conditional existence checks.

            Args:
                remove_none (bool): Whether to remove fields with None values from the database.
                                  True for PUT semantics, False for PATCH semantics
                **kwargs: Partial zone update parameters.

                          Required Fields:
                              client (str): Client name.
                              zone (str): Zone name.

                          Optional Update Fields:
                              Any zone attribute fields to update.
                              Set field to None to remove it from the zone.
                              Only modified fields will be updated in the database.

            Returns:
                Response: SuccessResponse containing the complete updated zone data
                          with all fields (modified and unchanged).

            Raises:
                BadRequestException: If required client or zone parameters are missing.
        +            NotFoundException: If the zone does not exist for update.
                UnknownException: If database operation fails due to connection issues,
                                 table access problems, or permission issues.
        """
        log.info("Patching zone")

        client = kwargs.get("client", kwargs.get("Client"))
        if not client:
            log.error("Client name missing in get request")
            raise BadRequestException('Client name is required in content: { "client": "<name>", ... }')

        zone = kwargs.get("zone", kwargs.get("Zone"))
        if not zone:
            log.error("Zone name missing in get request")
            raise BadRequestException('Zone name is required in content: { "zone": "<name>", ... }')

        model_class = ZoneFact.model_class(client)

        try:
            if remove_none:
                data = ZoneFact(**kwargs)  # Validate and parse input data
            else:
                # If not removing None, we allow partial updates without validation
                data = ZoneFact.model_construct(**kwargs)
        except (ValueError, ValidationError) as e:
            log.error("Invalid zone data for patch %s:%s: %s", client, zone, str(e))
            raise BadRequestException(f"Invalid zone data: {kwargs}: {str(e)}") from e

        excluded_fields = {"zone", "created_at", "updated_at"}

        try:

            values = data.model_dump(by_alias=False, exclude_none=False, exclude=excluded_fields)

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

            data = ZoneFact.from_model(item).model_dump(mode="json")

            return SuccessResponse(data=data)

        except UpdateError as e:
            if "ConditionalCheckFailedException" in str(e):
                log.warning("Zone not found for patching: %s:%s", client, zone)
                raise NotFoundException(f"Zone not found: {client}:{zone}") from e
            log.error("Update error patching zone %s:%s: %s", client, zone, str(e))
            raise UnknownException(f"Failed to patch zone {client}:{zone}: Permission denied or condition check failed") from e
        except Exception as e:
            log.error("Failed to patch zone %s:%s: %s", client, zone, str(e))
            raise UnknownException(f"Unexpected error patching zone: {str(e)}") from e
