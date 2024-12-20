""" Actions for the Registry.Clients database: list, get, create, update, delete """

from pynamodb.exceptions import (
    DoesNotExist,
    PutError,
    TableError,
    ScanError,
    GetError,
    DeleteError,
)
from pynamodb.expressions.update import Action

from ...constants import CLIENT_KEY

from ...exceptions import (
    ConflictException,
    BadRequestException,
    UnknownException,
)
from ...response import Response, SuccessResponse, NoContentResponse

from ..actions import RegistryAction

from .models import ClientFacts


def _get_client_name(**kwargs) -> str:
    """
    Get the client name from the input arguments.dict

    Mutates **kwargs by removing the client name and returning the client name.

    Args:
        **kwargs (dict): Dictionary containing:
            client (str): The client name (required)

    Returns:
        str: The client name

    Raises:
        BadRequestException: If client name is missing from **kwargs
    """
    client = kwargs.pop("client", kwargs.pop("Client", None))
    if not client:
        raise BadRequestException(
            'Client name is required in content: { "client": "<name>", ...}'
        )
    return client


class ClientActions(RegistryAction):

    @classmethod
    def list(cls, **kwargs) -> Response:
        """
        list all client FACTS records in a list of client names

        Args:
            **kwargs (dict): Dictionary containing:
                Nothing

        Returns:
            Response:
                SuccessResponse: containing the updated client details

        Raises:
            UnknownException: If database operations fail
        """
        try:
            items = ClientFacts.scan(attributes_to_get=[CLIENT_KEY])
        except TableError:
            # Table doesn't exist or is in a different state
            raise UnknownException("Failed to scan clients: Database table error")
        except ScanError:
            # Permissions or other AWS-specific scan operation failures
            raise UnknownException(
                "Failed to scan clients: Permission denied or AWS error"
            )
        except Exception as e:
            # Catch-all for unexpected errors
            raise UnknownException(f"Failed to scan clients: {str(e)}")

        result = [i.client for i in items]  # return a simple list of client names

        return SuccessResponse(result)

    @classmethod
    def get(cls, **kwargs) -> Response:
        """
        Get a client FACTS record

        Args:
            **kwargs (dict): Dictionary containing:
                client (str): The client name (required)

        Returns:
            Response:
                SuccessResponse: containing the updated client details
                NoContentResponse: if the client does not exist

        Raises:
            UnknownException: If database operations fail
        """
        client = _get_client_name(**kwargs)

        try:
            fact = ClientFacts.get(client)
        except DoesNotExist:
            # Item doesn't exist in the database
            return NoContentResponse(f"Client {client} does not exist")
        except TableError:
            # Table doesn't exist or is in a different state
            raise UnknownException(f"Database table error for client {client}")
        except GetError:
            # Permissions or other AWS-specific get operation failures
            raise UnknownException(
                f"Failed to access client {client}: Permission denied or AWS error"
            )
        except Exception as e:
            # Catch-all for unexpected errors
            raise UnknownException(f"Failed to get client {client}: {str(e)}")

        return SuccessResponse(fact.to_simple_dict())

    @classmethod
    def delete(cls, **kwargs) -> Response:
        """
        Delete a client FACTS record

        Args:
            **kwargs (dict): Dictionary containing:
                client (str): The client name (required)
                [attribute_name] (Any): Any additional attributes to update for the client

        Returns:
            Response:
                SuccessResponse: containing the updated client details
                NoContentResponse: if the client does not exist

        Raises:
            UnknownException: If database operations fails
        """
        client = _get_client_name(**kwargs)

        try:
            fact = ClientFacts(client)
            fact.delete()
        except DoesNotExist:
            # Item was deleted between get and delete (race condition)
            return NoContentResponse(f"Client {client} does not exist")
        except DeleteError:
            # Specific delete operation failure (permissions, conditions, etc.)
            raise UnknownException(
                f"Failed to delete client {client}: Permission denied or condition check failed"
            )
        except Exception as e:
            # Catch-all for unexpected errors
            raise UnknownException(f"Failed to delete client {client}: {str(e)}")

        return SuccessResponse(f"Client {client} deleted")

    @classmethod
    def create(cls, **kwargs) -> Response:
        """
        Create a client FACTS record

        Args:
            **kwargs (dict): Dictionary containing:
                client (str): The client name (required)
                [attribute_name] (Any): Any additional attributes to update for the client

        Returns:
            Response: SuccessResponse containing the updated client details

        Raises:
            ConflictException: If client name already exists
            BadRequestException: If client name is missing or data format is invalid
            UnknownException: If database operations fails
        """
        client = _get_client_name(**kwargs)

        try:
            fact = ClientFacts(client, **kwargs)
            fact.save(ClientFacts.client.does_not_exist())
        except PutError:
            # Condition check failed (item already exists)
            raise ConflictException(f"Client {client} already exists")
        except TableError:
            # Table doesn't exist or is in a different state
            raise UnknownException(
                f"Failed to save client {client}: Database table error"
            )
        except Exception as e:
            # Catch-all for unexpected errors
            raise UnknownException(f"Failed to save client {client}: {str(e)}")

        return SuccessResponse(fact.to_simple_dict())

    @classmethod
    def update(cls, **kwargs) -> Response:
        """
        Handles the PUT method.  If the item does not exist, it will be created.

        Args:
            kwargs (dict): The client name
        """
        client = _get_client_name(**kwargs)

        try:
            # Get the existing client record or create a new one if it doesn't exist
            fact = ClientFacts(client, **kwargs)
            fact.save()
        except (TableError, PutError) as e:
            raise UnknownException(f"Failed to update client {client}: {str(e)}")
        except Exception as e:
            raise UnknownException(
                f"Unexpected error updating client {client}: {str(e)}"
            )

        return SuccessResponse(fact.to_simple_dict())

    @classmethod
    def patch(cls, **kwargs) -> Response:
        """
        Handles the PATCH method.  If the item does not exist, it will be created or updated.

        Args:
            kwargs (dict): Input arguments
        """
        client = _get_client_name(**kwargs)

        try:
            # Create actions to remove attributes not in new kwargs
            fact = ClientFacts.get(client)
            attributes = fact.get_attributes()

            actions: list[Action] = []
            for key, value in kwargs.items():
                if hasattr(fact, key):
                    attr = attributes[key]
                    if value is None:
                        actions.append(attr.remove())
                        attr.set(None)
                    elif value != getattr(fact, key):
                        actions.append(attr.set(value))

            if len(actions) > 0:
                # Perform the update with all actions
                fact.update(actions=actions)
                fact.refresh()

            return SuccessResponse(fact.to_simple_dict())

        except TableError:
            raise UnknownException(f"Database table error while saving client {client}")
        except PutError:
            raise UnknownException(
                f"Failed to save client {client}: Permission denied or condition check failed"
            )
        except Exception as e:
            raise UnknownException(f"Unexpected error saving client {client}: {str(e)}")
