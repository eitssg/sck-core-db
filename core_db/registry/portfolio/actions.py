"""Actions for the Registry.Portfolios database: list, get, create, update, delete"""

from pynamodb.expressions.update import Action
from pynamodb.exceptions import DeleteError, PutError, AttributeNullError

import core_logging as log

from ...constants import CLIENT_KEY, PORTFOLIO_KEY

from ...response import SuccessResponse, Response
from ...exceptions import (
    ConflictException,
    UnknownException,
    BadRequestException,
    NotFoundException,
)

from ..actions import RegistryAction

from .models import PortfolioFactsFactory, PortfolioFacts


class PortfolioActions(RegistryAction):
    """Class container for Portfolio Item specific validations and actions"""

    @classmethod
    def _get_client_portfolio(cls, kwargs: dict, default_portfolio: str | None = None) -> tuple[str, str]:
        """
        Extract client and portfolio from kwargs.

        :param kwargs: Dictionary containing client and portfolio information
        :type kwargs: dict
        :param default_portfolio: Default portfolio value if not found in kwargs
        :type default_portfolio: str, optional
        :returns: Client and portfolio names
        :rtype: tuple[str, str]
        :raises BadRequestException: If client or portfolio are missing
        """
        client = kwargs.pop("client", kwargs.pop(CLIENT_KEY, None))
        portfolio = kwargs.pop("portfolio", kwargs.pop(PORTFOLIO_KEY, default_portfolio))

        if not portfolio or not client:
            log.error("Missing required parameters: client=%s, portfolio=%s", client, portfolio)
            raise BadRequestException(
                'Client and Portfolio names are required in content: { "client": <name>, "portfolio": "<name>", ...}'
            )

        log.debug("Extracted client=%s, portfolio=%s", client, portfolio)
        return client, portfolio

    @classmethod
    def _get_model_class(cls, client: str) -> type[PortfolioFacts]:
        """
        Get the client-specific model class.

        :param client: The client name for table selection
        :type client: str
        :returns: Client-specific PortfolioFacts model class
        :rtype: type[PortfolioFacts]
        """
        log.debug("Getting model class for client: %s", client)
        return PortfolioFactsFactory.get_model(client)

    @classmethod
    def list(cls, **kwargs) -> Response:
        """
        Returns an array of portfolios or BizApps registered for the client.

        :param kwargs: Must contain 'client' parameter
        :returns: Success response containing list of portfolio names
        :rtype: Response
        :raises BadRequestException: If client name is missing
        :raises UnknownException: If database query fails
        """
        log.info("Listing portfolios for client")
        client, _ = cls._get_client_portfolio(kwargs, default_portfolio="-")

        if not client:
            log.error("Client name missing in list request")
            raise BadRequestException('Client name is required in content: { "client": "<name>", ...}')

        try:
            model_class = cls._get_model_class(client)
            log.debug("Querying portfolios for client: %s", client)
            facts = model_class.query(hash_key=client, attributes_to_get=[PORTFOLIO_KEY])
            result = [p.Portfolio for p in facts]
            log.info("Found %d portfolios for client: %s", len(result), client)

        except Exception as e:
            # Handle DoesNotExist through the factory model
            if "DoesNotExist" in str(type(e)):
                log.warning("No portfolios found for client: %s", client)
                result = []
            else:
                log.error("Failed to query portfolios for client %s: %s", client, str(e))
                raise UnknownException(f"Failed to query portfolios - {str(e)}")

        return SuccessResponse(result)

    @classmethod
    def get(cls, **kwargs) -> Response:
        """
        Handles the GET method. If the item does not exist, a 404 will be returned.

        :param kwargs: Must contain 'client' and 'portfolio' parameters
        :returns: Success response with PortfolioFacts data
        :rtype: Response
        :raises BadRequestException: If required parameters are missing
        :raises NotFoundException: If portfolio does not exist
        :raises UnknownException: If database operation fails
        """
        log.info("Getting portfolio")
        client, portfolio = cls._get_client_portfolio(kwargs)

        try:
            model_class = cls._get_model_class(client)
            log.debug("Retrieving portfolio: %s:%s", client, portfolio)
            item: PortfolioFacts = model_class.get(client, portfolio)
            log.info("Successfully retrieved portfolio: %s:%s", client, portfolio)
        except Exception as e:
            if "DoesNotExist" in str(type(e)):
                log.warning("Portfolio not found: %s:%s", client, portfolio)
                raise NotFoundException(f"Portfolio [{client}:{portfolio}] not found")
            else:
                log.error("Failed to get portfolio %s:%s: %s", client, portfolio, str(e))
                raise UnknownException(f"Failed to get portfolio: {str(e)}")

        return SuccessResponse(item.to_simple_dict())

    @classmethod
    def delete(cls, **kwargs) -> Response:
        """
        Handles the DELETE method. If the item does not exist, a 404 will be returned.

        :param kwargs: Must contain 'client' and 'portfolio' parameters
        :returns: Success response confirming deletion
        :rtype: Response
        :raises BadRequestException: If required parameters are missing
        :raises NotFoundException: If portfolio does not exist
        :raises UnknownException: If database operation fails
        """
        log.info("Deleting portfolio")
        client, portfolio = cls._get_client_portfolio(kwargs)

        try:
            model_class = cls._get_model_class(client)
            log.debug("Retrieving portfolio for deletion: %s:%s", client, portfolio)
            item: PortfolioFacts = model_class.get(client, portfolio)
        except Exception as e:
            if "DoesNotExist" in str(type(e)):
                log.warning("Portfolio not found for deletion: %s:%s", client, portfolio)
                raise NotFoundException(f"Portfolio {client}:{portfolio} does not exist")
            else:
                log.error("Failed to get portfolio for deletion %s:%s: %s", client, portfolio, str(e))
                raise UnknownException(f"Failed to get portfolio for deletion: {str(e)}")

        try:
            log.debug("Deleting portfolio: %s:%s", client, portfolio)
            item.delete()
            log.info("Successfully deleted portfolio: %s:%s", client, portfolio)
        except DeleteError as e:
            log.error("Failed to delete portfolio %s:%s: %s", client, portfolio, str(e))
            raise UnknownException(f"Failed to delete - {str(e)}")
        except Exception as e:
            log.error("Unexpected error deleting portfolio %s:%s: %s", client, portfolio, str(e))
            raise UnknownException(f"Failed to delete - {str(e)}")

        return SuccessResponse(f"Portfolio deleted: {client}:{portfolio}")

    @classmethod
    def create(cls, **kwargs) -> Response:
        """
        Handles the POST method. Creates a new portfolio, fails if it already exists.

        :param kwargs: Must contain 'client' and 'portfolio' parameters, plus portfolio attributes
        :returns: Success response with created PortfolioFacts data
        :rtype: Response
        :raises BadRequestException: If required parameters are missing or invalid
        :raises ConflictException: If portfolio already exists
        :raises UnknownException: If database operation fails
        """
        log.info("Creating portfolio")
        client, portfolio = cls._get_client_portfolio(kwargs)

        try:
            model_class = cls._get_model_class(client)
            log.debug("Creating portfolio: %s:%s with data: %s", client, portfolio, kwargs)
            fact: PortfolioFacts = model_class(client, portfolio, **kwargs)

            # Use the dynamic class's Portfolio attribute for the condition
            fact.save(model_class.Portfolio.does_not_exist())
            log.info("Successfully created portfolio: %s:%s", client, portfolio)
        except ValueError as e:
            log.error("Invalid portfolio data for %s:%s: %s", client, portfolio, str(e))
            raise BadRequestException(f"Invalid portfolio data: {kwargs}: {str(e)}")
        except PutError as e:
            log.warning("Portfolio already exists: %s:%s - %s", client, portfolio, str(e))
            raise ConflictException(f"Portfolio {client}:{portfolio} already exists")
        except Exception as e:
            log.error("Failed to create portfolio %s:%s: %s", client, portfolio, str(e))
            raise UnknownException(f"Failed to create portfolio: {str(e)}")

        return SuccessResponse(fact.to_simple_dict())

    @classmethod
    def update(cls, **kwargs) -> Response:
        """
        Handles the PUT method. Creates or replaces a portfolio completely.

        :param kwargs: Must contain 'client' and 'portfolio' parameters, plus portfolio attributes
        :returns: Success response with updated PortfolioFacts data
        :rtype: Response
        :raises BadRequestException: If required parameters are missing
        :raises UnknownException: If database operation fails
        """
        log.info("Updating portfolio")
        client, portfolio = cls._get_client_portfolio(kwargs)

        model_class = cls._get_model_class(client)

        try:
            # Check if item exists (for logging purposes)
            item: PortfolioFacts = model_class.get(client, portfolio)
            if item:
                log.info("Portfolio exists, will be replaced: %s:%s", client, portfolio)
        except Exception as e:
            if "DoesNotExist" in str(type(e)):
                log.info("Portfolio does not exist, will be created: %s:%s", client, portfolio)
            else:
                log.error("Failed to check existing portfolio %s:%s: %s", client, portfolio, str(e))
                raise UnknownException(f"Failed to check existing portfolio: {str(e)}")

        try:
            log.debug("Updating portfolio: %s:%s with data: %s", client, portfolio, kwargs)
            item: PortfolioFacts = model_class(client, portfolio, **kwargs)
            item.save()
            log.info("Successfully updated portfolio: %s:%s", client, portfolio)
        except PutError as e:
            log.error("Put error updating portfolio %s:%s: %s", client, portfolio, str(e))
            raise ConflictException(f"Portfolio {client}:{portfolio} already exists")
        except Exception as e:
            log.error("Failed to update portfolio %s:%s: %s", client, portfolio, str(e))
            raise UnknownException(f"Failed to update portfolio: {str(e)}")

        return SuccessResponse(item.to_simple_dict())

    @classmethod
    def patch(cls, **kwargs) -> Response:
        """
        Handles the PATCH method. Updates specific attributes of an existing portfolio.

        :param kwargs: Must contain 'client' and 'portfolio' parameters, plus attributes to update
        :returns: Success response with patched PortfolioFacts data
        :rtype: Response
        :raises BadRequestException: If required parameters are missing or invalid
        :raises NotFoundException: If portfolio does not exist
        :raises UnknownException: If database operation fails
        """
        log.info("Patching portfolio")
        client, portfolio = cls._get_client_portfolio(kwargs)

        try:
            model_class = cls._get_model_class(client)
            log.debug("Retrieving portfolio for patch: %s:%s", client, portfolio)
            # Get the existing record from the DB
            item: PortfolioFacts = model_class.get(client, portfolio)

            # Make sure fields are in PascalCase
            new_facts = item.convert_keys(**kwargs)
            log.debug("Patching portfolio %s:%s with: %s", client, portfolio, new_facts)

            attributes = item.get_attributes()

            actions: list[Action] = []
            for key, value in new_facts.items():
                if hasattr(item, key):
                    if value is None:
                        attr = attributes[key]
                        actions.append(attr.remove())
                        attr.set(None)
                        log.debug("Removing attribute %s from portfolio %s:%s", key, client, portfolio)
                    elif value != getattr(item, key):
                        actions.append(attributes[key].set(value))
                        log.debug("Updating attribute %s in portfolio %s:%s", key, client, portfolio)

            if len(actions) > 0:
                log.debug("Applying %d updates to portfolio %s:%s", len(actions), client, portfolio)
                item.update(actions=actions)
                item.refresh()
                log.info("Successfully patched portfolio: %s:%s", client, portfolio)
            else:
                log.info("No changes needed for portfolio: %s:%s", client, portfolio)

            return SuccessResponse(item.to_simple_dict())

        except AttributeNullError as e:
            log.error("Required attribute missing for portfolio %s:%s: %s", client, portfolio, str(e))
            raise BadRequestException(f"Required attribute missing: {str(e)}")

        except Exception as e:
            if "DoesNotExist" in str(type(e)):
                log.warning("Portfolio not found for patch: %s:%s", client, portfolio)
                raise NotFoundException(f"Portfolio {client}:{portfolio} does not exist")
            else:
                log.error("Failed to patch portfolio %s:%s: %s", client, portfolio, str(e))
                raise UnknownException(f"Failed to patch portfolio: {str(e)}")
