"""Actions for the Registry.Clients database: list, get, create, update, delete"""

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

from .models import ClientFacts, ClientFactsFactory, ClientFactsType


class ClientActions(RegistryAction):
    """Actions for managing client FACTS records in the registry."""

    @classmethod
    def get_client_name(cls, kwargs: dict) -> str:
        """
        Get the client name from the input arguments dict.

        Mutates **kwargs by removing the client name and returning the client name.

        :param kwargs: Dictionary containing client identifier
        :type kwargs: dict
        :returns: The client name
        :rtype: str
        :raises BadRequestException: If client name is missing from kwargs
        """
        client = kwargs.pop("client", kwargs.pop(CLIENT_KEY, None))

        if not client:
            raise BadRequestException('Client name is required in content: { "client": "<name>", ...}')

        return client

    @classmethod
    def get_model(cls, client: str = None) -> ClientFactsType:
        """
        Get the PynamoDB model class for the specified client.

        :param client: The client name
        :type client: str
        :returns: The PynamoDB model class for the client
        :rtype: ClientFactsType
        """
        return ClientFactsFactory.get_model(client)

    @classmethod
    def list(cls, **kwargs) -> Response:
        """
        List all client FACTS records in a list of client names.

        :param kwargs: Dictionary containing no required parameters
        :type kwargs: dict
        :returns: SuccessResponse containing list of client names
        :rtype: Response
        :raises UnknownException: If database operations fail
        """
        try:
            model_class = cls.get_model()
            items = model_class.scan(attributes_to_get=[CLIENT_KEY])
        except TableError:
            # Table doesn't exist or is in a different state
            raise UnknownException("Failed to scan clients: Database table error")
        except ScanError:
            # Permissions or other AWS-specific scan operation failures
            raise UnknownException("Failed to scan clients: Permission denied or AWS error")
        except Exception as e:
            # Catch-all for unexpected errors
            raise UnknownException(f"Failed to scan clients: {str(e)}")

        result = [i.Client for i in items]  # return a simple list of client names

        return SuccessResponse(result)

    @classmethod
    def get(cls, **kwargs) -> Response:
        """
        Get a client FACTS record.

        :param kwargs: Dictionary containing client identifier
        :type kwargs: dict
        :returns: SuccessResponse containing client details or NoContentResponse if not found
        :rtype: Response
        :raises UnknownException: If database operations fail
        """
        client = cls.get_client_name(kwargs)

        try:
            model_class = cls.get_model(client)
            fact = model_class.get(client)
        except DoesNotExist:
            # Item doesn't exist in the database
            return NoContentResponse(f"Client {client} does not exist")
        except TableError:
            # Table doesn't exist or is in a different state
            raise UnknownException(f"Database table error for client {client}")
        except GetError:
            # Permissions or other AWS-specific get operation failures
            raise UnknownException(f"Failed to access client {client}: Permission denied or AWS error")
        except Exception as e:
            # Catch-all for unexpected errors
            raise UnknownException(f"Failed to get client {client}: {str(e)}")

        return SuccessResponse(fact.to_simple_dict())

    @classmethod
    def delete(cls, **kwargs) -> Response:
        """
        Delete a client FACTS record.

        :param kwargs: Dictionary containing client identifier
        :type kwargs: dict
        :returns: SuccessResponse if deleted or NoContentResponse if not found
        :rtype: Response
        :raises UnknownException: If database operations fail
        """
        client = cls.get_client_name(kwargs)

        try:
            # Get the record first to verify it exists
            model_class = cls.get_model(client)
            fact = model_class.get(client)
            fact.delete()
        except DoesNotExist:
            # Item doesn't exist in the database
            return NoContentResponse(f"Client {client} does not exist")
        except DeleteError:
            # Specific delete operation failure (permissions, conditions, etc.)
            raise UnknownException(f"Failed to delete client {client}: Permission denied or condition check failed")
        except Exception as e:
            # Catch-all for unexpected errors
            raise UnknownException(f"Failed to delete client {client}: {str(e)}")

        return SuccessResponse(f"Client {client} deleted")

    @classmethod
    def create(cls, **kwargs) -> Response:
        """
        Create a client FACTS record.

        :param kwargs: Dictionary containing client name and additional attributes
        :type kwargs: dict
        :returns: SuccessResponse containing the created client details
        :rtype: Response
        :raises ConflictException: If client name already exists
        :raises BadRequestException: If client name is missing or data format is invalid
        :raises UnknownException: If database operations fail
        """
        client = cls.get_client_name(kwargs)

        try:
            model_class = cls.get_model(client)
            fact = model_class(client, **kwargs)
            fact.save(model_class.Client.does_not_exist())
        except PutError:
            # Condition check failed (item already exists)
            raise ConflictException(f"Client {client} already exists")
        except TableError:
            # Table doesn't exist or is in a different state
            raise UnknownException(f"Failed to save client {client}: Database table error")
        except ValueError as e:
            # Invalid data format
            raise BadRequestException(f"Data error on create {client}: {str(e)}")
        except Exception as e:
            # Catch-all for unexpected errors
            raise UnknownException(f"Failed to save client {client}: {str(e)}")

        return SuccessResponse(fact.to_simple_dict())

    @classmethod
    def update(cls, **kwargs) -> Response:
        """
        Handle the PUT method. If the item does not exist, it will be created.

        :param kwargs: Dictionary containing client name and attributes to update
        :type kwargs: dict
        :returns: SuccessResponse containing the updated client details
        :rtype: Response
        :raises UnknownException: If database operations fail
        """
        client = cls.get_client_name(kwargs)

        try:
            # Create or update the client record
            model_class = cls.get_model(client)
            fact = model_class(client, **kwargs)
            fact.save()
        except (TableError, PutError) as e:
            raise UnknownException(f"Failed to update client {client}: {str(e)}")
        except Exception as e:
            raise UnknownException(f"Unexpected error updating client {client}: {str(e)}")

        return SuccessResponse(fact.to_simple_dict())

    @classmethod
    def patch(cls, **kwargs) -> Response:
        """
        Handle the PATCH method. Updates specific attributes of existing client record.

        :param kwargs: Dictionary containing client name and attributes to patch
        :type kwargs: dict
        :returns: SuccessResponse containing the updated client details
        :rtype: Response
        :raises UnknownException: If database operations fail
        """
        client = cls.get_client_name(kwargs)

        try:
            # Get the current record from the DB
            model_class = cls.get_model(client)
            fact = model_class.get(client)

            # Make sure fields are in PascalCase
            new_facts = fact.convert_keys(**kwargs)

            attributes = fact.get_attributes()
            actions: list[Action] = []
            for key, value in new_facts.items():
                if hasattr(fact, key):
                    attr = attributes[key]
                    if value is None:
                        actions.append(attr.remove())
                        # Don't set None on the object - remove action handles this
                    elif value != getattr(fact, key):
                        actions.append(attr.set(value))

            if len(actions) > 0:
                # Perform the update with all actions
                fact.update(actions=actions)
                fact.refresh()

            return SuccessResponse(fact.to_simple_dict())

        except DoesNotExist:
            # If client doesn't exist, create it
            return cls.create(client=client, **kwargs)
        except TableError:
            raise UnknownException(f"Database table error while saving client {client}")
        except PutError:
            raise UnknownException(f"Failed to save client {client}: Permission denied or condition check failed")
        except Exception as e:
            raise UnknownException(f"Unexpected error saving client {client}: {str(e)}")
