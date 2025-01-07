""" Actions for the Registry.Apps database: list, get, create, update, delete """

from pynamodb.expressions.update import Action
from pynamodb.exceptions import DeleteError, PutError

from ...response import (
    Response,
    SuccessResponse,
    NoContentResponse,
)
from ...exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    UnknownException,
)

from ...constants import (
    APP_KEY,
    CLIENT_PORTFOLIO_KEY,
    CLIENT_KEY,
    PORTFOLIO_KEY,
)

from ..actions import RegistryAction
from .models import AppFacts


class AppActions(RegistryAction):

    @classmethod
    def get_client_portfolio_app(
        cls, kwargs: dict, default_regex: str | None = None
    ) -> tuple[str, str]:
        """
        Get the client portfolio name from the input arguments.

        Mutates \\*\\*kwargs by removing the client-portfolio name and returning the client-portfolio name.
        Do not \\*\\* kwargs else it wont mutate.

        Args:
            kwargs (Dict): Dictionary containing:
                client-portfolio (str): The client portfolio name (optional)

                or

                client (str): The client name (optional)
                portfolio (str): The portfolio name (optional)

        Returns:
            str: The client portfolio name in the format "<client name>:<portfolio name>"

        Raises:
            BadRequestException: If client-portfolio name is missing or cant be created from client and portfolio
        """
        client_portfolio = kwargs.pop(
            "client-portfolio", kwargs.pop(CLIENT_PORTFOLIO_KEY, None)
        )

        if not client_portfolio:
            client = kwargs.pop("client", kwargs.pop(CLIENT_KEY, None))
            portfolio = kwargs.pop("portfolio", kwargs.pop(PORTFOLIO_KEY, None))
            client_portfolio = f"{client}:{portfolio}" if client and portfolio else None

        app_regex = kwargs.pop("app-regex", kwargs.pop(APP_KEY, default_regex))

        if not client_portfolio or not app_regex:
            raise BadRequestException(
                'Client portfolio name is required in content: { "client-portfolio": "<name>", ...}'
            )

        return client_portfolio, app_regex

    @classmethod
    def list(cls, **kwargs) -> Response:
        """
        Returns an array of application deployments patterns for the client-portfolio.
        The array is a list of application regex patterns.

        ```python
        values: list[str] = ['a','b','c']
        ```
        To get the list, supply a single paramter with the cilent and portfolio concatenated with a colon (:).

        Why this list?  Think about the "UI" and the REST api you will want to use and create a type-ahead list.
        So, you only need to query this list of regex patterns to get the list of applications.

        Select Client:      [ client name        v ]
        Select Portfolio:   [ portfolio name     v ]
        Select Application: [ application regex  v ]

        Think about your UI.  use this API to get the list of applications.

        Args:
            **kwargs (Dict): The dictionary of input arguments.
                [attribute_name] (str): See get_client_portfolio() for details

        Returns:
            List[str]: A list of application regex patterns
        """
        client_portfolio, _ = cls.get_client_portfolio_app(kwargs, default_regex="-")

        try:
            items = AppFacts.query(
                hash_key=client_portfolio, attributes_to_get=["AppRegex"]
            )
        except Exception as e:
            raise UnknownException(f"Failed to get apps: {str(e)}")

        try:
            result = [a.AppRegex for a in items]
        except Exception as e:
            raise UnknownException(f"Failed to get apps: {str(e)}")

        return SuccessResponse(result)

    @classmethod
    def get(cls, **kwargs) -> Response:
        """
        Handles the GET method.  If the item does not exist, a 404 will be returned.

        Args:
            client_portfolio (str): The client_portfolio name
            app_regex (str): the deployment key regular expression
        """
        client_portfolio, app_regex = cls.get_client_portfolio_app(kwargs)

        if not app_regex:
            raise BadRequestException(
                'App regex is required in content: { "app_regex": "<name>", ...}'
            )

        try:
            item = AppFacts.get(hash_key=client_portfolio, range_key=app_regex)
        except AppFacts.DoesNotExist:
            raise NotFoundException(f"App [{client_portfolio}:{app_regex}] not found")

        return SuccessResponse(item.to_simple_dict())

    @classmethod
    def delete(cls, **kwargs) -> Response:
        """
        Handles the DELETE method.  If the item does not exist, it will be ignored.  No 404 will ever be returned

        Args:
            client_portfolio (str): The client_portfolio name
            app_regex (str): the deployment key regular expression
        """
        client_portfolio, app_regex = cls.get_client_portfolio_app(kwargs)

        if not app_regex:
            raise BadRequestException(
                'App regex is required in content: { "app_regex": "<name>", ...}'
            )

        try:
            item = AppFacts(client_portfolio, app_regex)
            item.delete()
        except AppFacts.DoesNotExist:
            return NoContentResponse(f"App [{client_portfolio}:{app_regex}] not found")
        except DeleteError as e:
            raise UnknownException(f"Failed to delete - {str(e)}")

        return SuccessResponse(f"App [{client_portfolio}:{app_regex}] deleted")

    @classmethod
    def create(cls, **kwargs) -> Response:
        """
        Handles the POST method.  If the item already exists, an exception will be thrown.

        Args:
            client_portfolio (str): The client_portfolio name
            app_regex (str): the deployment key regular expression
        """
        client_portfolio, app_regex = cls.get_client_portfolio_app(kwargs)

        if not app_regex:
            raise BadRequestException(
                'App regex is required in content: { "AppRegex": "<name>", ...}'
            )

        try:
            item = AppFacts(client_portfolio, app_regex, **kwargs)
            item.save(AppFacts.AppRegex.does_not_exist())
        except ValueError as e:
            raise BadRequestException(
                f"Invalid item data for [{client_portfolio}:{app_regex}] {kwargs}: {str(e)}"
            )
        except AppFacts.DoesNotExist:
            raise ConflictException(
                f"App [{client_portfolio}:{app_regex}] already exists"
            )
        except PutError as e:
            raise ConflictException(f"Failed to create app: {str(e)}")
        except Exception as e:
            raise UnknownException(f"Creation failed - {str(e)}")

        return SuccessResponse(item.to_simple_dict())

    @classmethod
    def update(cls, **kwargs) -> Response:
        """
        Handles the PUT method.  If the item does not exist, it will be created.  The specified attributes will updated.

        Args:
            client_portfolio (str): The client_portfolio name
            app_regex (str): the deployment key regular expression
        """
        client_portfolio, app_regex = cls.get_client_portfolio_app(kwargs)

        if not app_regex:
            raise BadRequestException(
                'App regex is required in content: { "app_regex": "<name>", ...}'
            )

        try:

            item = AppFacts.get(client_portfolio, app_regex)

            attributes = item.get_attributes()

            actions: list[Action] = []
            for key, value in kwargs.items():
                if hasattr(item, key):
                    attr = attributes[key]
                    if value is None:
                        actions.append(attr.remove())
                        attr.set(None)
                    elif value != getattr(item, key):
                        actions.append(attr.set(value))

            if len(actions) > 0:
                item.update(actions=actions, condition=AppFacts.AppRegex.exists())
                item.refresh()

            return SuccessResponse(item.to_simple_dict())

        except AppFacts.DoesNotExist:
            raise NotFoundException(
                f"App [{client_portfolio}:{app_regex}] does not exist"
            )
        except PutError as e:
            raise ConflictException(f"Failed to update app: {str(e)}")

    @classmethod
    def patch(cls, **kwargs) -> Response:
        """
        Handles the PATCH method.  If the item does not exist, an error will occur

        Args:
            client_portfolio (str): The client_portfolio name
            app_regex (str): the deployment key regular expression
        """
        client_portfolio, app_regex = cls.get_client_portfolio_app(kwargs)

        try:
            item = AppFacts.get(client_portfolio, app_regex)

            attributes = item.get_attributes()

            actions: list[Action] = []
            for key, value in kwargs.items():
                if hasattr(item, key):
                    attr = attributes[key]
                    if value is None:
                        actions.append(attr.remove())
                        attr.set(None)
                    elif value != getattr(item, key):
                        actions.append(attr.set(value))

            if len(actions) > 0:
                item.update(actions=actions)
                item.refresh()

            return SuccessResponse(item.to_simple_dict())

        except AppFacts.DoesNotExist:
            raise NotFoundException(
                f"App [{client_portfolio}:{app_regex}] does not exist"
            )
