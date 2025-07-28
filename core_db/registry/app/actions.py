"""Actions for the Registry.Apps database: list, get, create, update, delete"""

from pynamodb.expressions.update import Action
from pynamodb.exceptions import DeleteError, PutError, AttributeNullError

import core_logging as log

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
from .models import AppFacts, AppFactsFactory, AppFactsType


class AppActions(RegistryAction):
    """Class container for App Item specific validations and actions"""

    @classmethod
    def _get_client_portfolio_app(cls, kwargs: dict, default_regex: str | None = None) -> tuple[str, str, str]:
        """
        Extract client, portfolio, and app regex from kwargs.

        :param kwargs: Dictionary containing client, portfolio and app information
        :type kwargs: dict
        :param default_regex: Default app regex value if not found in kwargs
        :type default_regex: str, optional
        :returns: Client name, portfolio name, and app regex
        :rtype: tuple[str, str, str]
        :raises BadRequestException: If required parameters are missing
        """
        # First try to get client-portfolio as a single value
        client_portfolio = kwargs.pop("client-portfolio", kwargs.pop(CLIENT_PORTFOLIO_KEY, None))

        if client_portfolio:
            # Split client-portfolio into client and portfolio
            if ":" in client_portfolio:
                client, portfolio = client_portfolio.split(":", 1)
            else:
                raise BadRequestException('Client-portfolio must be in format "client:portfolio"')
        else:
            # Try to get client and portfolio separately
            client = kwargs.pop("client", kwargs.pop(CLIENT_KEY, None))
            portfolio = kwargs.pop("portfolio", kwargs.pop(PORTFOLIO_KEY, None))

        app_regex = kwargs.pop("app-regex", kwargs.pop(APP_KEY, default_regex))

        if not client or not portfolio or not app_regex:
            log.error(
                "Missing required parameters: client=%s, portfolio=%s, app_regex=%s",
                client,
                portfolio,
                app_regex,
            )
            raise BadRequestException(
                'Client, Portfolio, and App Regex are required in content: { "client": "<name>", "portfolio": "<name>", "app-regex": "<regex>", ...}'
            )

        log.debug(
            "Extracted client=%s, portfolio=%s, app_regex=%s",
            client,
            portfolio,
            app_regex,
        )
        return client, portfolio, app_regex

    @classmethod
    def _get_model_class(cls, client: str) -> AppFactsType:
        """
        Get the client-specific model class.

        :param client: The client name for table selection
        :type client: str
        :returns: Client-specific AppFacts model class
        :rtype: AppFactsType
        """
        return AppFactsFactory.get_model(client)

    @classmethod
    def _format_client_portfolio(cls, client: str, portfolio: str) -> str:
        """
        Format client and portfolio into client-portfolio key.

        :param client: The client name
        :type client: str
        :param portfolio: The portfolio name
        :type portfolio: str
        :returns: Formatted client-portfolio string
        :rtype: str
        """
        return f"{client}:{portfolio}"

    @classmethod
    def list(cls, **kwargs) -> Response:
        """
        Returns an array of application deployments patterns for the client-portfolio.

        :param kwargs: Must contain 'client' and 'portfolio' parameters
        :returns: Success response containing list of app regex patterns
        :rtype: Response
        :raises BadRequestException: If required parameters are missing
        :raises UnknownException: If database query fails
        """
        log.info("Listing apps for client-portfolio")
        client, portfolio, _ = cls._get_client_portfolio_app(kwargs, default_regex="-")
        client_portfolio = cls._format_client_portfolio(client, portfolio)

        try:
            model_class = cls._get_model_class(client)
            log.debug("Querying apps for client-portfolio: %s", client_portfolio)
            items = model_class.query(hash_key=client_portfolio, attributes_to_get=[APP_KEY])
            result = [a.AppRegex for a in items]
            log.info("Found %d apps for client-portfolio: %s", len(result), client_portfolio)
        except Exception as e:
            # Handle DoesNotExist through the factory model
            if "DoesNotExist" in str(type(e)):
                log.warning("No apps found for client-portfolio: %s", client_portfolio)
                result = []
            else:
                log.error(
                    "Failed to query apps for client-portfolio %s: %s",
                    client_portfolio,
                    str(e),
                )
                raise UnknownException(f"Failed to query apps - {str(e)}")

        return SuccessResponse(result)

    @classmethod
    def get(cls, **kwargs) -> Response:
        """
        Handles the GET method. If the item does not exist, a 404 will be returned.

        :param kwargs: Must contain 'client', 'portfolio', and 'app-regex' parameters
        :returns: Success response with AppFacts data
        :rtype: Response
        :raises BadRequestException: If required parameters are missing
        :raises NotFoundException: If app does not exist
        :raises UnknownException: If database operation fails
        """
        log.info("Getting app")
        client, portfolio, app_regex = cls._get_client_portfolio_app(kwargs)
        client_portfolio = cls._format_client_portfolio(client, portfolio)

        try:
            model_class = cls._get_model_class(client)
            log.debug("Retrieving app: %s:%s", client_portfolio, app_regex)
            item: AppFacts = model_class.get(client_portfolio, app_regex)
            log.info("Successfully retrieved app: %s:%s", client_portfolio, app_regex)
        except Exception as e:
            if "DoesNotExist" in str(type(e)):
                log.warning("App not found: %s:%s", client_portfolio, app_regex)
                raise NotFoundException(f"App [{client_portfolio}:{app_regex}] not found")
            else:
                log.error("Failed to get app %s:%s: %s", client_portfolio, app_regex, str(e))
                raise UnknownException(f"Failed to get app: {str(e)}")

        return SuccessResponse(item.to_simple_dict())

    @classmethod
    def delete(cls, **kwargs) -> Response:
        """
        Handles the DELETE method. If the item does not exist, a 404 will be returned.

        :param kwargs: Must contain 'client', 'portfolio', and 'app-regex' parameters
        :returns: Success response confirming deletion
        :rtype: Response
        :raises BadRequestException: If required parameters are missing
        :raises NotFoundException: If app does not exist
        :raises UnknownException: If database operation fails
        """
        log.info("Deleting app")
        client, portfolio, app_regex = cls._get_client_portfolio_app(kwargs)
        client_portfolio = cls._format_client_portfolio(client, portfolio)

        try:
            model_class = cls._get_model_class(client)
            log.debug("Retrieving app for deletion: %s:%s", client_portfolio, app_regex)
            item: AppFacts = model_class.get(client_portfolio, app_regex)
        except Exception as e:
            if "DoesNotExist" in str(type(e)):
                log.warning("App not found for deletion: %s:%s", client_portfolio, app_regex)
                raise NotFoundException(f"App {client_portfolio}:{app_regex} does not exist")
            else:
                log.error(
                    "Failed to get app for deletion %s:%s: %s",
                    client_portfolio,
                    app_regex,
                    str(e),
                )
                raise UnknownException(f"Failed to get app for deletion: {str(e)}")

        try:
            log.debug("Deleting app: %s:%s", client_portfolio, app_regex)
            item.delete()
            log.info("Successfully deleted app: %s:%s", client_portfolio, app_regex)
        except DeleteError as e:
            log.error("Failed to delete app %s:%s: %s", client_portfolio, app_regex, str(e))
            raise UnknownException(f"Failed to delete - {str(e)}")
        except Exception as e:
            log.error(
                "Unexpected error deleting app %s:%s: %s",
                client_portfolio,
                app_regex,
                str(e),
            )
            raise UnknownException(f"Failed to delete - {str(e)}")

        return SuccessResponse(f"App [{client_portfolio}:{app_regex}] deleted")

    @classmethod
    def create(cls, **kwargs) -> Response:
        """
        Handles the POST method. Creates a new app, fails if it already exists.

        :param kwargs: Must contain 'client', 'portfolio', and 'app-regex' parameters, plus app attributes
        :returns: Success response with created AppFacts data
        :rtype: Response
        :raises BadRequestException: If required parameters are missing or invalid
        :raises ConflictException: If app already exists
        :raises UnknownException: If database operation fails
        """
        log.info("Creating app")
        client, portfolio, app_regex = cls._get_client_portfolio_app(kwargs)
        client_portfolio = cls._format_client_portfolio(client, portfolio)

        try:
            model_class = cls._get_model_class(client)
            log.debug("Creating app: %s:%s with data: %s", client_portfolio, app_regex, kwargs)
            item: AppFacts = model_class(client_portfolio, app_regex, **kwargs)

            # Use the dynamic class's AppRegex attribute for the condition
            item.save(model_class.AppRegex.does_not_exist())
            log.info("Successfully created app: %s:%s", client_portfolio, app_regex)
        except ValueError as e:
            log.error("Invalid app data for %s:%s: %s", client_portfolio, app_regex, str(e))
            raise BadRequestException(f"Invalid app data: {kwargs}: {str(e)}")
        except PutError as e:
            log.warning("App already exists: %s:%s - %s", client_portfolio, app_regex, str(e))
            raise ConflictException(f"App {client_portfolio}:{app_regex} already exists")
        except Exception as e:
            if "ConditionalCheckFailedException" in str(e):
                log.warning("App already exists: %s:%s", client_portfolio, app_regex)
                raise ConflictException(f"App {client_portfolio}:{app_regex} already exists")
            else:
                log.error(
                    "Failed to create app %s:%s: %s",
                    client_portfolio,
                    app_regex,
                    str(e),
                )
                raise UnknownException(f"Failed to create app: {str(e)}")

        return SuccessResponse(item.to_simple_dict())

    @classmethod
    def update(cls, **kwargs) -> Response:
        """
        Handles the PUT method. Creates or replaces an app completely.

        :param kwargs: Must contain 'client', 'portfolio', and 'app-regex' parameters, plus app attributes
        :returns: Success response with updated AppFacts data
        :rtype: Response
        :raises BadRequestException: If required parameters are missing
        :raises UnknownException: If database operation fails
        """
        log.info("Updating app")
        client, portfolio, app_regex = cls._get_client_portfolio_app(kwargs)
        client_portfolio = cls._format_client_portfolio(client, portfolio)

        model_class = cls._get_model_class(client)

        try:
            # Check if item exists (for logging purposes)
            item: AppFacts = model_class.get(client_portfolio, app_regex)
            if item:
                log.info("App exists, will be replaced: %s:%s", client_portfolio, app_regex)
        except Exception as e:
            if "DoesNotExist" in str(type(e)):
                log.info(
                    "App does not exist, will be created: %s:%s",
                    client_portfolio,
                    app_regex,
                )
            else:
                log.error(
                    "Failed to check existing app %s:%s: %s",
                    client_portfolio,
                    app_regex,
                    str(e),
                )
                raise UnknownException(f"Failed to check existing app: {str(e)}")

        try:
            log.debug("Updating app: %s:%s with data: %s", client_portfolio, app_regex, kwargs)
            item: AppFacts = model_class(client_portfolio, app_regex, **kwargs)
            item.save()
            log.info("Successfully updated app: %s:%s", client_portfolio, app_regex)
        except PutError as e:
            log.error("Put error updating app %s:%s: %s", client_portfolio, app_regex, str(e))
            raise ConflictException(f"App {client_portfolio}:{app_regex} update conflict")
        except Exception as e:
            log.error("Failed to update app %s:%s: %s", client_portfolio, app_regex, str(e))
            raise UnknownException(f"Failed to update app: {str(e)}")

        return SuccessResponse(item.to_simple_dict())

    @classmethod
    def patch(cls, **kwargs) -> Response:
        """
        Handles the PATCH method. Updates specific attributes of an existing app.

        :param kwargs: Must contain 'client', 'portfolio', and 'app-regex' parameters, plus attributes to update
        :returns: Success response with patched AppFacts data
        :rtype: Response
        :raises BadRequestException: If required parameters are missing or invalid
        :raises NotFoundException: If app does not exist
        :raises UnknownException: If database operation fails
        """
        log.info("Patching app")
        client, portfolio, app_regex = cls._get_client_portfolio_app(kwargs)
        client_portfolio = cls._format_client_portfolio(client, portfolio)

        try:
            model_class = cls._get_model_class(client)
            log.debug("Retrieving app for patch: %s:%s", client_portfolio, app_regex)
            # Get the existing record from the DB
            item: AppFacts = model_class.get(client_portfolio, app_regex)

            # Make sure fields are in PascalCase
            new_facts = item.convert_keys(**kwargs) if hasattr(item, "convert_keys") else kwargs
            log.debug("Patching app %s:%s with: %s", client_portfolio, app_regex, new_facts)

            attributes = item.get_attributes()

            actions: list[Action] = []
            for key, value in new_facts.items():
                if hasattr(item, key):
                    if value is None:
                        attr = attributes[key]
                        actions.append(attr.remove())
                        attr.set(None)
                        log.debug(
                            "Removing attribute %s from app %s:%s",
                            key,
                            client_portfolio,
                            app_regex,
                        )
                    elif value != getattr(item, key):
                        actions.append(attributes[key].set(value))
                        log.debug(
                            "Updating attribute %s in app %s:%s",
                            key,
                            client_portfolio,
                            app_regex,
                        )

            if len(actions) > 0:
                log.debug(
                    "Applying %d updates to app %s:%s",
                    len(actions),
                    client_portfolio,
                    app_regex,
                )
                item.update(actions=actions)
                item.refresh()
                log.info("Successfully patched app: %s:%s", client_portfolio, app_regex)
            else:
                log.info("No changes needed for app: %s:%s", client_portfolio, app_regex)

            return SuccessResponse(item.to_simple_dict())

        except AttributeNullError as e:
            log.error(
                "Required attribute missing for app %s:%s: %s",
                client_portfolio,
                app_regex,
                str(e),
            )
            raise BadRequestException(f"Required attribute missing: {str(e)}")

        except Exception as e:
            if "DoesNotExist" in str(type(e)):
                log.warning("App not found for patch: %s:%s", client_portfolio, app_regex)
                raise NotFoundException(f"App {client_portfolio}:{app_regex} does not exist")
            else:
                log.error("Failed to patch app %s:%s: %s", client_portfolio, app_regex, str(e))
                raise UnknownException(f"Failed to patch app: {str(e)}")
