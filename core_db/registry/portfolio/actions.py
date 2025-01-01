""" Actions for the Registry.Portfolios database: list, get, create, update, delete """

from pynamodb.expressions.update import Action
from pynamodb.exceptions import DeleteError, PutError, AttributeNullError

from ...constants import CLIENT_KEY, PORTFOLIO_KEY

from ...response import SuccessResponse, Response
from ...exceptions import (
    ConflictException,
    UnknownException,
    BadRequestException,
    NotFoundException,
)

from ..actions import RegistryAction

from .models import PortfolioFacts


class PortfolioActions(RegistryAction):
    """Class container for Portfolio Item specific validations and actions"""

    @classmethod
    def _get_client_portfolio(
        cls, kwargs: dict, default_portfolio: str | None = None
    ) -> tuple[str, str]:

        client = kwargs.pop("client", kwargs.pop(CLIENT_KEY, None))
        portfolio = kwargs.pop(
            "portfolio", kwargs.pop(PORTFOLIO_KEY, default_portfolio)
        )

        if not portfolio or not client:
            raise BadRequestException(
                'Client and Portfolio names ar required in content: { "client": <name>, "portfolio": "<name>", ...}'
            )

        return client, portfolio

    @classmethod
    def list(cls, **kwargs) -> Response:
        """
        Returns an array of portflios or BizApps registered for the client.

        Args:
            client (str): The clinet name
        """
        client, _ = cls._get_client_portfolio(kwargs, default_portfolio="-")

        if not client:
            raise BadRequestException(
                'Client name is required in content: { "client": "<name>", ...}'
            )

        try:

            facts = PortfolioFacts.query(
                hash_key=client, attributes_to_get=[PORTFOLIO_KEY]
            )
            result = [p.Portfolio for p in facts]

        except PortfolioFacts.DoesNotExist:
            result = []
        except Exception as e:
            raise UnknownException(f"Failed to query portfolios - {str(e)}")

        return SuccessResponse(result)

    @classmethod
    def get(cls, **kwargs) -> Response:
        """
        Handles the GET method.  If the item does not exist, a 404 will be returned.

        Args:
            client (str): The client name
            portfolio (str): the portfolio name
        """
        client, portfolio = cls._get_client_portfolio(kwargs)

        try:
            item = PortfolioFacts.get(client, portfolio)
        except PortfolioFacts.DoesNotExist:
            raise NotFoundException(f"Portfolio [{client}:{portfolio}] not found")
        except Exception as e:
            raise UnknownException(f"Failed to get portfolio: {str(e)}")

        return SuccessResponse(item.to_simple_dict())

    @classmethod
    def delete(cls, **kwargs) -> Response:
        """
        Handles the DELETE method.  If the item does not exist, it will be ignored.  No 404 will ever be returned

        Args:
            client (str): The client name
            portfolio (str): the portfolio name
        """
        client, portfolio = cls._get_client_portfolio(kwargs)

        try:
            item = PortfolioFacts.get(client, portfolio)
        except PortfolioFacts.DoesNotExist:
            raise NotFoundException(f"Portfolio {client}:{portfolio} does not exist")

        try:
            item.delete()
        except DeleteError as e:
            raise UnknownException(f"Failed to delete - {str(e)}")
        except Exception as e:
            raise UnknownException(f"Failed to delete - {str(e)}")

        return SuccessResponse(f"Portfolio deleted: {client}:{portfolio}")

    @classmethod
    def create(cls, **kwargs) -> Response:
        """
        Handles the POST method.  If the item already exists, it will be replaced.

        Args:
            client (str): The client name
            portfolio (str): the portfolio name
            kwargs: The attributes to create
        """
        client, portfolio = cls._get_client_portfolio(kwargs)

        try:
            fact = PortfolioFacts(client, portfolio, **kwargs)
            fact.save(PortfolioFacts.Portfolio.does_not_exist())
        except ValueError as e:
            raise BadRequestException(f"Invalid portfolio data: {kwargs}: {str(e)}")
        except PutError as e:
            print(str(e))
            raise ConflictException(f"Portfolio {client}:{portfolio} already exists")
        except Exception as e:
            raise UnknownException(f"Failed to create portfolio: {str(e)}")

        return SuccessResponse(fact.to_simple_dict())

    @classmethod
    def update(cls, **kwargs) -> Response:
        """
        Handles the PUT method.  If the item does not exist, it will be created.  The specified attributes will updated.

        Args:
            client (str): The client name
            portfolio (str): the portfolio name
            kwargs: The attributes to update
        """
        client, portfolio = cls._get_client_portfolio(kwargs)

        item = PortfolioFacts.get(client, portfolio)
        if item:
            # log a warning saying the item already exists
            pass

        try:
            item = PortfolioFacts(client, portfolio, **kwargs)
            item.save()
        except PutError:
            raise ConflictException(f"Portfolio {client}:{portfolio} already exists")

        return SuccessResponse(item.to_simple_dict())

    @classmethod
    def patch(cls, **kwargs) -> Response:
        """
        Handles the PATCH method.  If the item does not exist, it will be created.  The specified attributes will updated.

        Args:
            client (str): The client name
            portfolio (str): the portfolio name
            kwargs: The attributes to update
        """
        client, portfolio = cls._get_client_portfolio(kwargs)

        try:
            # Get the existing record from the dB
            item = PortfolioFacts.get(client, portfolio)

            # Make sure fields are in PascalCase
            new_facts = item.convert_keys(**kwargs)

            attributes = item.get_attributes()

            actions: list[Action] = []
            for key, value in new_facts.items():
                if hasattr(item, key):
                    if value is None:
                        attr = attributes[key]
                        actions.append(attr.remove())
                        attr.set(None)
                    elif value != getattr(item, key):
                        actions.append(attributes[key].set(value))

            if len(actions) > 0:
                item.update(actions=actions)
                item.refresh()

            return SuccessResponse(item.to_simple_dict())

        except AttributeNullError as e:
            raise BadRequestException(f"Required attribute missing: {str(e)}")

        except PortfolioFacts.DoesNotExist:
            raise NotFoundException(f"Portfolio {client}:{portfolio} does not exist")

        except Exception as e:
            raise UnknownException(f"Failed to patch portfolio: {str(e)}")
