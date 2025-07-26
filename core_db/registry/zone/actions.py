"""Zone Registry Actions for client-specific zone facts management."""

from typing import List, Optional, Dict, Any

import core_logging as log

from ...response import SuccessResponse, Response
from ...exceptions import (
    ConflictException,
    UnknownException,
    BadRequestException,
    NotFoundException,
)
from ...constants import CLIENT_KEY, ZONE_KEY

from ..actions import RegistryAction
from .models import ZoneFactsFactory, ZoneFacts


class ZoneActions(RegistryAction):
    """
    Zone Registry Actions for managing zone facts across multiple clients.

    This class handles CRUD operations for zone facts using client-specific
    table models via the ZoneFactsFactory.
    """

    @classmethod
    def _get_client_zone(cls, kwargs: dict, default_zone: str | None = None) -> tuple[str, str]:
        """
        Extract client and zone from kwargs.

        :param kwargs: Dictionary containing client and zone information
        :type kwargs: dict
        :param default_zone: Default zone value if not found in kwargs
        :type default_zone: str, optional
        :returns: Client and zone names
        :rtype: tuple[str, str]
        :raises BadRequestException: If client or zone are missing
        """
        client = kwargs.pop("client", kwargs.pop(CLIENT_KEY, None))
        zone = kwargs.pop("zone", kwargs.pop(ZONE_KEY, default_zone))

        if not zone or not client:
            log.error("Missing required parameters: client=%s, zone=%s", client, zone)
            raise BadRequestException('Client and Zone names are required in content: { "client": <name>, "zone": "<name>", ...}')

        log.debug("Extracted client=%s, zone=%s", client, zone)
        return client, zone

    @classmethod
    def _get_model_class(cls, client: str) -> type[ZoneFacts]:
        """
        Get the client-specific model class.

        :param client: The client name for table selection
        :type client: str
        :returns: Client-specific ZoneFacts model class
        :rtype: type[ZoneFacts]
        """
        log.debug("Getting model class for client: %s", client)
        return ZoneFactsFactory.get_model(client)

    @classmethod
    def list(cls, **kwargs) -> Response:
        """
        Returns an array of zones registered for the client.

        :param kwargs: Must contain 'client' parameter
        :returns: Success response containing list of zone names
        :rtype: Response
        :raises BadRequestException: If client name is missing
        :raises UnknownException: If database query fails
        """
        log.info("Listing zones for client")
        client, _ = cls._get_client_zone(kwargs, default_zone="-")

        if not client:
            log.error("Client name missing in list request")
            raise BadRequestException('Client name is required in content: { "client": "<name>", ...}')

        try:
            model_class = cls._get_model_class(client)
            log.debug("Querying zones for client: %s", client)
            facts = model_class.query(hash_key=client, attributes_to_get=[ZONE_KEY])
            result = [z.Zone for z in facts]
            log.info("Found %d zones for client: %s", len(result), client)

        except Exception as e:
            # Handle DoesNotExist through the factory model
            if "DoesNotExist" in str(type(e)):
                log.warning("No zones found for client: %s", client)
                result = []
            else:
                log.error("Failed to query zones for client %s: %s", client, str(e))
                raise UnknownException(f"Failed to query zones - {str(e)}")

        return SuccessResponse(result)

    @classmethod
    def get(cls, **kwargs) -> Response:
        """
        Handles the GET method. If the item does not exist, a 404 will be returned.

        :param kwargs: Must contain 'client' and 'zone' parameters
        :returns: Success response with ZoneFacts data
        :rtype: Response
        :raises BadRequestException: If required parameters are missing
        :raises NotFoundException: If zone does not exist
        :raises UnknownException: If database operation fails
        """
        log.info("Getting zone")
        client, zone = cls._get_client_zone(kwargs)

        try:
            model_class = cls._get_model_class(client)
            log.debug("Retrieving zone: %s:%s", client, zone)
            item: ZoneFacts = model_class.get(client, zone)
            log.info("Successfully retrieved zone: %s:%s", client, zone)
        except Exception as e:
            if "DoesNotExist" in str(type(e)):
                log.warning("Zone not found: %s:%s", client, zone)
                raise NotFoundException(f"Zone [{client}:{zone}] not found")
            else:
                log.error("Failed to get zone %s:%s: %s", client, zone, str(e))
                raise UnknownException(f"Failed to get zone: {str(e)}")

        return SuccessResponse(item.to_simple_dict())

    @classmethod
    def delete(cls, **kwargs) -> Response:
        """
        Handles the DELETE method. If the item does not exist, a 404 will be returned.

        :param kwargs: Must contain 'client' and 'zone' parameters
        :returns: Success response confirming deletion
        :rtype: Response
        :raises BadRequestException: If required parameters are missing
        :raises NotFoundException: If zone does not exist
        :raises UnknownException: If database operation fails
        """
        log.info("Deleting zone")
        client, zone = cls._get_client_zone(kwargs)

        try:
            model_class = cls._get_model_class(client)
            log.debug("Retrieving zone for deletion: %s:%s", client, zone)
            item: ZoneFacts = model_class.get(client, zone)
        except Exception as e:
            if "DoesNotExist" in str(type(e)):
                log.warning("Zone not found for deletion: %s:%s", client, zone)
                raise NotFoundException(f"Zone {client}:{zone} does not exist")
            else:
                log.error("Failed to get zone for deletion %s:%s: %s", client, zone, str(e))
                raise UnknownException(f"Failed to get zone for deletion: {str(e)}")

        try:
            log.debug("Deleting zone: %s:%s", client, zone)
            item.delete()
            log.info("Successfully deleted zone: %s:%s", client, zone)
        except Exception as e:
            log.error("Failed to delete zone %s:%s: %s", client, zone, str(e))
            raise UnknownException(f"Failed to delete - {str(e)}")

        return SuccessResponse(f"Zone deleted: {client}:{zone}")

    @classmethod
    def create(cls, **kwargs) -> Response:
        """
        Handles the POST method. Creates a new zone, fails if it already exists.

        :param kwargs: Must contain 'client' and 'zone' parameters, plus zone attributes
        :returns: Success response with created ZoneFacts data
        :rtype: Response
        :raises BadRequestException: If required parameters are missing or invalid
        :raises ConflictException: If zone already exists
        :raises UnknownException: If database operation fails
        """
        log.info("Creating zone")
        client, zone = cls._get_client_zone(kwargs)

        try:
            model_class = cls._get_model_class(client)
            log.debug("Creating zone: %s:%s with data: %s", client, zone, kwargs)
            fact: ZoneFacts = model_class(client, zone, **kwargs)

            # Use the dynamic class's Zone attribute for the condition
            fact.save(model_class.Zone.does_not_exist())
            log.info("Successfully created zone: %s:%s", client, zone)
        except ValueError as e:
            log.error("Invalid zone data for %s:%s: %s", client, zone, str(e))
            raise BadRequestException(f"Invalid zone data: {kwargs}: {str(e)}")
        except Exception as e:
            if "ConditionalCheckFailedException" in str(e):
                log.warning("Zone already exists: %s:%s", client, zone)
                raise ConflictException(f"Zone {client}:{zone} already exists")
            else:
                log.error("Failed to create zone %s:%s: %s", client, zone, str(e))
                raise UnknownException(f"Failed to create zone: {str(e)}")

        return SuccessResponse(fact.to_simple_dict())

    @classmethod
    def update(cls, **kwargs) -> Response:
        """
        Handles the PUT method. Creates or replaces a zone completely.

        :param kwargs: Must contain 'client' and 'zone' parameters, plus zone attributes
        :returns: Success response with updated ZoneFacts data
        :rtype: Response
        :raises BadRequestException: If required parameters are missing
        :raises UnknownException: If database operation fails
        """
        log.info("Updating zone")
        client, zone = cls._get_client_zone(kwargs)

        model_class = cls._get_model_class(client)

        try:
            # Check if item exists (for logging purposes)
            item: ZoneFacts = model_class.get(client, zone)
            if item:
                log.info("Zone exists, will be replaced: %s:%s", client, zone)
        except Exception as e:
            if "DoesNotExist" in str(type(e)):
                log.info("Zone does not exist, will be created: %s:%s", client, zone)
            else:
                log.error("Failed to check existing zone %s:%s: %s", client, zone, str(e))
                raise UnknownException(f"Failed to check existing zone: {str(e)}")

        try:
            log.debug("Updating zone: %s:%s with data: %s", client, zone, kwargs)
            item: ZoneFacts = model_class(client, zone, **kwargs)
            item.save()
            log.info("Successfully updated zone: %s:%s", client, zone)
        except Exception as e:
            log.error("Failed to update zone %s:%s: %s", client, zone, str(e))
            raise UnknownException(f"Failed to update zone: {str(e)}")

        return SuccessResponse(item.to_simple_dict())

    @classmethod
    def patch(cls, **kwargs) -> Response:
        """
        Handles the PATCH method. Updates specific attributes of an existing zone.

        :param kwargs: Must contain 'client' and 'zone' parameters, plus attributes to update
        :returns: Success response with patched ZoneFacts data
        :rtype: Response
        :raises BadRequestException: If required parameters are missing or invalid
        :raises NotFoundException: If zone does not exist
        :raises UnknownException: If database operation fails
        """
        log.info("Patching zone")
        client, zone = cls._get_client_zone(kwargs)

        try:
            model_class = cls._get_model_class(client)
            log.debug("Retrieving zone for patch: %s:%s", client, zone)
            # Get the existing record from the DB
            item: ZoneFacts = model_class.get(client, zone)

            # Make sure fields are in PascalCase
            new_facts = item.convert_keys(**kwargs)
            log.debug("Patching zone %s:%s with: %s", client, zone, new_facts)

            attributes = item.get_attributes()

            actions: list = []
            for key, value in new_facts.items():
                if hasattr(item, key):
                    if value is None:
                        attr = attributes[key]
                        actions.append(attr.remove())
                        attr.set(None)
                        log.debug("Removing attribute %s from zone %s:%s", key, client, zone)
                    elif value != getattr(item, key):
                        actions.append(attributes[key].set(value))
                        log.debug("Updating attribute %s in zone %s:%s", key, client, zone)

            if len(actions) > 0:
                log.debug("Applying %d updates to zone %s:%s", len(actions), client, zone)
                item.update(actions=actions)
                item.refresh()
                log.info("Successfully patched zone: %s:%s", client, zone)
            else:
                log.info("No changes needed for zone: %s:%s", client, zone)

            return SuccessResponse(item.to_simple_dict())

        except Exception as e:
            if "DoesNotExist" in str(type(e)):
                log.warning("Zone not found for patch: %s:%s", client, zone)
                raise NotFoundException(f"Zone {client}:{zone} does not exist")
            else:
                log.error("Failed to patch zone %s:%s: %s", client, zone, str(e))
                raise UnknownException(f"Failed to patch zone: {str(e)}")
