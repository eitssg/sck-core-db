""" Actions for the Registry.Zones database: list, get, create, update, delete """

from pynamodb.exceptions import DeleteError, PutError

import core_framework as util

from ...constants import CLIENT_PORTFOLIO_KEY, ZONE_KEY, CLIENT_KEY, PORTFOLIO_KEY

from ...response import (
    Response,
    SuccessResponse,
    NoContentResponse,
)
from ...exceptions import (
    ConflictException,
    UnknownException,
    BadRequestException,
    NotFoundException,
)

from ..actions import RegistryAction

from .models import ZoneFacts


class ZoneActions(RegistryAction):

    @classmethod
    def get_clent_portfolio_zone(cls, kwargs: dict) -> tuple[str | None, str | None]:
        """
        Get the client portfolio and zone from the input arguments.

        Mutates \\*\\*kwargs by removing the client portfolio and zone and returning the client portfolio and zone.
        Do not \\*\\* the kwaargs or else it wont mutate

        Args:
            kwargs (dict): The paramters with client, portfolio, and zone

        Raises:
            BadRequestException: If client portfolio name is missing from kwargs

        Returns:
            tuple[str | None, str | None]: client:portfolio, zone
        """
        client_portfolio = kwargs.pop(
            CLIENT_PORTFOLIO_KEY, kwargs.pop("client-portfolio", None)
        )
        if not client_portfolio:
            client = kwargs.pop(CLIENT_KEY, kwargs.pop("Client", None))
            portfolio = kwargs.pop(PORTFOLIO_KEY, kwargs.pop("Portfolio", None))
            if client and portfolio:
                client_portfolio = f"{client}:{portfolio}"
            else:
                raise BadRequestException(
                    'Client portfolio name is required in content: { "client_portfolio": "<name>", ...}'
                )
        zone = kwargs.pop(ZONE_KEY, kwargs.pop("zone", None))
        return client_portfolio, zone

    @classmethod
    def list(cls, **kwargs) -> Response:
        """
        Returns an array of zones registered for the client and portfolio.

        The client_portfolio is a combination of the client and portfolio name.

        Ex:  client_portfolio = "client:portfolio"

        Args:
            client_portfolio (str): The client portfolio name
        """
        client_portfolio, _ = cls.get_clent_portfolio_zone(kwargs)

        try:
            items = ZoneFacts.query(
                hash_key=client_portfolio, attributes_to_get=["Zone"]
            )
            results = [z.Zone for z in items]
        except ZoneFacts.DoesNotExist:
            results = []
        except Exception as e:
            raise UnknownException(f"Failed to list zones: {str(e)}")

        return SuccessResponse(results)

    @classmethod
    def get(cls, **kwargs) -> Response:
        """
        Handles the GET method.  If the item does not exist, a 404 will be returned.

        Args:
            client_portfolio (str): The client portfolio name
            zone (str): the zone name
        """
        client_portfolio, zone = cls.get_clent_portfolio_zone(kwargs)

        if not zone:
            raise BadRequestException(
                'Zone name is required in content { "zone": "<name>", ...}'
            )

        try:
            item = ZoneFacts.get(client_portfolio, zone)
        except ZoneFacts.DoesNotExist:
            raise NotFoundException(f"Zone [{client_portfolio}:{zone}] not found")
        except Exception as e:
            raise UnknownException(f"Failed to get zone: {str(e)}")

        return SuccessResponse(item.to_simple_dict())

    @classmethod
    def delete(cls, **kwargs) -> Response:
        """
        Handles the DELETE method.  If the item does not exist, it will be ignored and 204 result

        Args:
            client_portfolio (str): The client portfolio name
            zone (str): the zone name
        """
        client_portfolio, zone = cls.get_clent_portfolio_zone(kwargs)

        if not zone:
            raise BadRequestException(
                'Zone name is required in content { "zone": "<name>", ...}'
            )

        try:
            item = ZoneFacts(client_portfolio, zone)
            item.delete(condition=ZoneFacts.Zone.exists())
        except ZoneFacts.DoesNotExist:
            return NoContentResponse(f"Zone {client_portfolio}:{zone} does not exist")
        except DeleteError as e:
            raise UnknownException(f"Failed to delete zone: {str(e)}")
        except Exception as e:
            raise UnknownException(f"Failed to delete zone: {str(e)}")

        return SuccessResponse(f"Zone deleted: {zone}")

    @classmethod
    def create(cls, **kwargs) -> Response:
        """
        Handles the POST method.  If the item already exists, it will be replaced.

        Args:
            client_portfolio (str): The client portfolio name
            zone (str): the zone name
            kwargs: The attributes to create
        """
        client_portfolio, zone = cls.get_clent_portfolio_zone(kwargs)

        if not zone:
            raise BadRequestException(
                'Zone name is required in content { "zone": "<name>", ...}'
            )

        try:
            item = ZoneFacts(client_portfolio, zone, **kwargs)
            item.save(ZoneFacts.Zone.does_not_exist())
        except PutError as e:
            raise ConflictException(f"Failed to create zone: {str(e)}")
        except ValueError as e:
            raise BadRequestException(f"Invalid zone data: {kwargs}: {str(e)}")
        except Exception as e:
            raise UnknownException(f"Failed to create zone: {str(e)}")

        return SuccessResponse(item.to_simple_dict())

    @classmethod
    def update(cls, **kwargs) -> Response:
        """
        Handles the PUT method.  If the item does not exist, it will be created.  The specified attributes will updated.

        Args:
            client_portfolio (str): The client portfolio name
            zone (str): the zone name
            kwargs: The attributes to update
        """
        client_portfolio, zone = cls.get_clent_portfolio_zone(kwargs)

        if not zone:
            raise BadRequestException(
                'Zone name is required in content { "zone": "<name>", ...}'
            )

        try:
            item = ZoneFacts(client_portfolio, zone, **kwargs)
            item.save(condition=ZoneFacts.Zone.exists())
        except ZoneFacts.DoesNotExist:
            raise NotFoundException(f"Zone [{client_portfolio}:{zone}] not found")
        except Exception as e:
            raise UnknownException(f"Failed to update zone: {str(e)}")

        return SuccessResponse(item.to_simple_dict())

    @classmethod
    def patch(cls, **kwargs) -> Response:
        """
        Handles the PATCH method.  If the item does not exist, it will be created or updated.

        Args:
            client_portfolio (str): The client portfolio name
            zone (str): the zone name
            kwargs: The attributes to update
        """
        client_portfolio, zone = cls.get_clent_portfolio_zone(kwargs)

        if not zone:
            raise BadRequestException(
                'Zone name is required in content { "zone": "<name>", ...}'
            )

        try:
            item: dict = ZoneFacts.get(client_portfolio, zone).to_simple_dict()

            # Merge the patch data into the item
            util.deep_merge_in_place(item, kwargs, merge_lists=True)

            new_item = ZoneFacts(client_portfolio, zone, **item)
            new_item.save()

        except ZoneFacts.DoesNotExist:
            raise NotFoundException(f"Zone [{client_portfolio}:{zone}] not found")
        except Exception as e:
            raise UnknownException(f"Failed to patch zone: {str(e)}")

        return SuccessResponse(new_item.to_simple_dict())
