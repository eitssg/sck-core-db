"""App registry actions for the core-automation-registry DynamoDB table.

This module provides comprehensive CRUD operations for application deployment patterns
within the registry system. Applications define regex patterns for deployment automation
and are organized within client-portfolio hierarchies with comprehensive validation and
error handling throughout all operations.

Key Features:
    - **Composite Key Management**: Handles client-portfolio + app-regex composite keys
    - **Pattern Validation**: Validates application regex patterns for deployment matching
    - **Client Isolation**: Factory pattern ensures proper table isolation between clients
    - **Flexible Parameter Handling**: Supports both composite and separate parameter formats
    - **Comprehensive Error Handling**: Detailed exception mapping for different failure scenarios

App Registry Structure:
    Applications are stored with a composite key structure:
    - Hash Key: portfolio (portfolio identifier)
    - Range Key: app_regex (regex pattern for application matching)
    - Attributes: Application-specific deployment configuration and metadata

Parameter Formats:
    The module supports flexible parameter formats for ease of use:
    - Composite format: client-portfolio="acme:web-services"
    - Separate format: client="acme", portfolio="web-services"
    - Both formats can be mixed with app-regex parameter

Related Modules:
    - core_db.registry.app.models: AppFactsModel and factory for table management
    - core_db.registry.actions: Base RegistryAction class with common functionality
    - core_db.registry: Registry system for deployment automation patterns

Note:
    All methods expect kwargs containing merged parameters from HTTP requests.
    The flexible parameter parsing supports both API gateway path parameters
    and request body formats for maximum compatibility.
"""

import re
from pydantic_core import ValidationError
from pynamodb.expressions.update import Action
from pynamodb.exceptions import (
    DeleteError,
    PutError,
    DoesNotExist,
    QueryError,
    ScanError,
    TableError,
    UpdateError,
)

import core_logging as log
import core_framework as util
from core_framework.time_utils import make_default_time

from ...response import (
    Response,
    SuccessResponse,  # http 200
    NoContentResponse,  # http 204
)
from ...exceptions import (
    BadRequestException,  # http 400
    ConflictException,  # http 409
    NotFoundException,  # http 404
    UnknownException,  # http 500
)

from ...models import Paginator
from ..actions import RegistryAction
from .models import AppFact


class AppActions(RegistryAction):
    """Actions for managing application deployment patterns in the registry.

    Provides comprehensive CRUD operations for application registry entries with proper
    error handling, validation, and flexible parameter parsing. Applications define
    regex patterns used for automated deployment matching within client-portfolio hierarchies.

    The class handles composite key management (portfolio + app-regex) and supports
    multiple parameter formats for maximum compatibility with different API patterns.

    Key Capabilities:
        - Create, read, update, delete application registry entries
        - List applications by client-portfolio
        - Flexible parameter parsing (composite vs separate parameters)
        - Comprehensive validation and error handling
        - Client-specific table isolation through factory pattern

    Note:
        All methods expect kwargs containing merged parameters from HTTP requests,
        supporting both path parameters and request body data.
    """

    @classmethod
    def list(cls, **kwargs) -> Response:
        """List all application deployment patterns for a client-portfolio.

        Retrieves all application regex patterns registered for the specified client-portfolio
        combination. Results are sorted by app regex for consistent ordering and include
        complete application configuration data.

        Args:
            **kwargs: Parameters containing client-portfolio identification.
                     Supports both composite and separate parameter formats:
                     - client (str): Client name (required)
                     - portfolio (str): Portfolio identifier

        Returns:
            Response: SuccessResponse containing list of application dictionaries with complete configuration.
                     Sorted by AppRegex field for consistent ordering. Empty list if no applications found.

        Raises:
            BadRequestException: If required client-portfolio parameters are missing or have invalid format
            UnknownException: If database query fails due to connection issues or other unexpected errors
        """
        log.info("Listing apps for client")

        client = kwargs.get("client", kwargs.get("Client")) or util.get_client()
        portfolio = kwargs.get("portfolio", kwargs.get("Portfolio"))
        app_name = kwargs.get("app_name", kwargs.get("AppName"))

        if not client:
            raise BadRequestException("Missing required parameter: client")

        try:
            paginator = Paginator(**kwargs)
        except (ValueError, ValidationError) as e:
            raise BadRequestException(f"Invalid pagination parameters: {str(e)}") from e

        if portfolio and app_name:
            return cls._get_apps_by_portfolio_app_name(
                client, portfolio, app_name, paginator
            )
        elif portfolio:
            return cls._get_apps_by_portfolio(client, portfolio, paginator)
        else:
            return cls._get_all_apps_paginated(client, paginator)

    @classmethod
    def get(cls, **kwargs) -> Response:
        """Retrieve specific application deployment pattern by client-portfolio and app name.

        Args:
            **kwargs: Parameters containing client-portfolio identification and app name.
                     Supports both composite and separate parameter formats:
                     - client (str): Client name (required)
                     - portfolio (str): Portfolio identifier
                     - app_name (str): Application name

        Returns:
            Response: SuccessResponse containing the specific application data or empty list if not found.

        Raises:
            BadRequestException: If required parameters are missing or have invalid format
            NotFoundException: If the specific application is not found
            UnknownException: If database query fails due to connection issues or other unexpected errors
        """
        log.info("Getting specific app for client")

        client = kwargs.get("client", kwargs.get("Client")) or util.get_client()
        portfolio = kwargs.get("portfolio", kwargs.get("Portfolio"))
        app_regex = kwargs.get("app_regex", kwargs.get("AppRegex"))

        if not client:
            raise BadRequestException("Missing required parameter: client")
        if not portfolio:
            raise BadRequestException("Missing required parameter: portfolio")
        if not app_regex:
            raise BadRequestException("Missing required parameter: app_regex")

        return cls._get_apps_by_portfolio_regex(client, portfolio, app_regex)

    @classmethod
    def _get_apps_by_portfolio_regex(
        cls, client: str, portfolio: str, app_regex: str
    ) -> Response:
        """Retrieve specific application by portfolio and regex pattern.

        Args:
            client (str): Client identifier for table access
            portfolio (str): Portfolio name (hash key)
            app_regex (str): Application regex pattern (range key)

        Returns:
            Response: SuccessResponse containing the specific application data or empty list if not found

        Raises:
            DoesNotExist: If the specific application is not found
        """
        log.debug("Getting specific app: %s:%s", portfolio, app_regex)

        model_class = AppFact.model_class(client)

        try:
            item = model_class.get(portfolio, app_regex)

            data = AppFact.from_model(item).model_dump(mode="json")

            log.info("Successfully retrieved specific app: %s:%s", portfolio, app_regex)

            return SuccessResponse(data=data)
        except DoesNotExist as e:
            log.warning("Specific app not found: %s:%s", portfolio, app_regex)
            return NoContentResponse(
                message=f"App {portfolio}:{app_regex} does not exist"
            )
        except Exception as e:
            log.error(
                "Failed to retrieve specific app %s:%s - %s",
                portfolio,
                app_regex,
                str(e),
            )
            raise UnknownException(
                f"Failed to retrieve app {portfolio}:{app_regex}"
            ) from e

    @classmethod
    def _get_apps_by_portfolio(
        cls, client: str, portfolio: str, paginator: Paginator
    ) -> Response:
        """Retrieve all applications for a specific portfolio with pagination.

        Args:
            client (str): Client identifier for table access
            portfolio (str): Portfolio name (hash key)
            paginator (Paginator): Pagination configuration and state management

        Returns:
            Response: SuccessResponse containing list of applications in the portfolio with pagination metadata
        """
        log.debug("Getting all apps for portfolio: %s", portfolio)

        model_class = AppFact.model_class(client)

        try:
            query_kwargs = {"consistent_read": True}

            if paginator.limit:
                query_kwargs["limit"] = paginator.limit

            if paginator.cursor is not None:
                query_kwargs["last_evaluated_key"] = paginator.cursor

            result = model_class.query(portfolio, **query_kwargs)

            data = [AppFact.from_model(item).model_dump(mode="json") for item in result]

            paginator.cursor = getattr(result, "last_evaluated_key", None)
            paginator.total_count = getattr(result, "total_count", len(data))

            # Sort by app_regex for consistent ordering
            log.info(
                "Successfully queried %d apps for portfolio: %s", len(data), portfolio
            )

            return SuccessResponse(data=data, metadata=paginator.get_metadata())
        except QueryError as e:
            log.error("Failed to query apps for portfolio %s - %s", portfolio, str(e))
            raise UnknownException(
                f"Failed to query apps for portfolio {portfolio}"
            ) from e
        except Exception as e:
            log.error(
                "Unexpected error while querying apps for portfolio %s - %s",
                portfolio,
                str(e),
            )
            raise UnknownException(
                f"Unexpected error while querying apps for {portfolio}"
            ) from e

    @classmethod
    def _get_apps_by_portfolio_app_name(
        cls, client: str, portfolio: str, app_name: str, paginator: Paginator
    ) -> Response:
        """Retrieve applications by portfolio filtered by app name regex matching.

        Queries all applications in the portfolio and filters them by checking if the provided
        app_name matches any of the stored regex patterns.

        Args:
            client (str): Client identifier for table access
            portfolio (str): Portfolio name (hash key)
            app_name (str): Application name to match against stored regex patterns

        Returns:
            Response: SuccessResponse containing list of applications where regex patterns match the app_name
        """
        log.debug(
            "Filtering apps by name: %s matching patterns in portfolio: %s",
            app_name,
            portfolio,
        )

        model_class = AppFact.model_class(client)

        try:

            query_kwargs = {"consistent_read": True}

            if paginator.limit:
                query_kwargs["limit"] = paginator.limit

            if paginator.cursor is not None:
                query_kwargs["last_evaluated_key"] = paginator.cursor

            result = model_class.query(portfolio, **query_kwargs)

            data = []
            for item in result:
                app_fact = AppFact.from_model(item)
                try:
                    # Check if the app_name matches the regex pattern stored in app_regex field
                    if re.match(app_fact.app_regex, app_name):
                        data.append(app_fact.model_dump(mode="json"))
                        log.debug(
                            "App name '%s' matches pattern '%s'",
                            app_name,
                            app_fact.app_regex,
                        )
                except re.error:
                    # Skip invalid regex patterns
                    log.warning("Invalid regex pattern in app: %s", app_fact.app_regex)
                    continue

            paginator.cursor = getattr(result, "last_evaluated_key", None)
            paginator.total_count = getattr(result, "total_count", len(data))

            log.info(
                "Successfully filtered %d apps matching name: %s", len(data), app_name
            )

            # Returns a list of applications that match the app_name regex
            return SuccessResponse(data=data, metadata=paginator.get_metadata())

        except QueryError as e:
            log.error("Failed to query apps for portfolio %s - %s", portfolio, str(e))
            raise UnknownException(
                f"Failed to query apps for portfolio {portfolio}"
            ) from e
        except Exception as e:
            log.error(
                "Unexpected error while filtering apps by name %s in portfolio %s - %s",
                app_name,
                portfolio,
                str(e),
            )
            raise UnknownException(
                f"Unexpected error while filtering apps for {portfolio}:{app_name}"
            ) from e

    @classmethod
    def _get_all_apps_paginated(cls, client: str, paginator: Paginator) -> Response:
        """Retrieve all applications for a client with pagination support.

        Performs a table scan to retrieve all applications across all portfolios for the client.
        Supports pagination for efficient handling of large datasets.

        Args:
            client (str): Client identifier for table access
            paginator (Paginator): Pagination configuration and state management

        Returns:
            Response: SuccessResponse containing list of all applications with pagination metadata
        """
        log.debug("Scanning all apps for client: %s", client)

        model_class = AppFact.model_class(client)

        try:
            scan_kwargs = {}
            if paginator.limit:
                scan_kwargs["limit"] = paginator.limit

            if paginator.cursor:
                scan_kwargs["last_evaluated_key"] = paginator.cursor

            result = model_class.scan(**scan_kwargs)

            data = [AppFact.from_model(item).model_dump(mode="json") for item in result]

            paginator.cursor = getattr(result, "last_evaluated_key", None)
            paginator.total_count = getattr(result, "total_count", len(data))

            log.info("Successfully scanned %d apps for client: %s", len(data), client)

            return SuccessResponse(data=data, metadata=paginator.get_metadata())

        except ScanError as e:
            log.error("Failed to scan apps for client %s - %s", client, str(e))
            raise UnknownException(f"Failed to scan apps for client {client}") from e
        except Exception as e:
            log.error(
                "Unexpected error while scanning apps for client %s - %s",
                client,
                str(e),
            )
            raise UnknownException(
                f"Unexpected error while scanning apps for {client}"
            ) from e

    @classmethod
    def delete(cls, **kwargs) -> Response:
        """Delete an application deployment pattern.

        Removes the specified application registry entry from the database. Returns
        success confirmation or handles not found scenarios gracefully.

        Args:
            **kwargs: Parameters identifying the application to delete:
                     - client (str): Client name (required)
                     - portfolio (str): Portfolio name (required)
                     - app_regex (str): Application regex pattern to delete (required)

        Returns:
            Response: SuccessResponse with deletion confirmation message,
                     or NoContentResponse if application not found

        Raises:
            BadRequestException: If required parameters are missing or have invalid format
            UnknownException: If database operation fails during retrieval or deletion
        """
        log.info("Deleting app")

        client = kwargs.get("client", kwargs.get("Client")) or util.get_client()
        portfolio = kwargs.get("portfolio", kwargs.get("Portfolio"))
        app_regex = kwargs.get("app_regex", kwargs.get("AppRegex"))

        if not client:
            raise BadRequestException("Missing required parameter: client")
        if not portfolio:
            raise BadRequestException("Missing required parameter: portfolio")
        if not app_regex:
            raise BadRequestException("Missing required parameter: app_regex")

        model_class = AppFact.model_class(client)

        try:
            log.debug("Deleting app: %s:%s", portfolio, app_regex)

            item = model_class.get(portfolio, app_regex)

            item.delete(
                condition=model_class.portfolio.exists()
                & model_class.app_regex.exists()
            )

            log.info("Successfully deleted app: %s:%s", portfolio, app_regex)

            return SuccessResponse(message=f"App [{portfolio}:{app_regex}] deleted")

        except DoesNotExist as e:
            log.info("App not found for deletion: %s:%s", portfolio, app_regex)
            return NoContentResponse(
                message=f"App [{portfolio}:{app_regex}] does not exist"
            )
        except DeleteError as e:
            if "ConditionalCheckFailedException" in str(e):
                log.info("App not found for deletion: %s:%s", portfolio, app_regex)
                return NoContentResponse(
                    message=f"App [{portfolio}:{app_regex}] was deleted by another process"
                )
            log.error("Failed to delete app: %s:%s - %s", portfolio, app_regex, str(e))
            raise UnknownException(
                f"Failed to delete app {portfolio}:{app_regex}"
            ) from e
        except Exception as e:
            log.error(
                "Unexpected error deleting app %s:%s - %s", portfolio, app_regex, str(e)
            )
            raise UnknownException(
                f"Unexpected error deleting app {portfolio}:{app_regex}"
            ) from e

    @classmethod
    def create(cls, **kwargs) -> Response:
        """Create a new application deployment pattern.

        Creates a new application registry entry with the specified configuration.
        Fails if an application with the same portfolio and app-regex already exists,
        ensuring unique application regex patterns within each portfolio.

        Args:
            **kwargs: Parameters for application creation:
                     - client (str): Client name (required)
                     - portfolio (str): Portfolio name (required)
                     - app_regex (str): Unique application regex pattern (required)
                     - name (str): Human-readable application name (required)
                     - All AppFact fields supported for application configuration

        Returns:
            Response: SuccessResponse containing the created application data with all fields

        Raises:
            BadRequestException: If required parameters are missing, have invalid format,
                               or application data validation fails
            ConflictException: If application already exists with the same portfolio and app-regex combination
            UnknownException: If database operation fails due to connection issues or other unexpected errors
        """
        log.info("Creating app")

        client = kwargs.get("client", kwargs.get("Client", None)) or util.get_client()
        if not client:
            raise BadRequestException("Missing required parameter: client")

        try:
            data = AppFact(**kwargs)
        except (ValueError, ValidationError) as e:
            log.error("Invalid app data: %s", str(e))
            raise BadRequestException(f"Invalid app data: {str(e)}")

        model_class = AppFact.model_class(client)

        try:
            item = data.to_model(client)
            # Use condition to prevent overwriting existing apps
            item.save(
                model_class.portfolio.does_not_exist()
                & model_class.app_regex.does_not_exist()
            )

            log.info("Successfully created app: %s:%s", data.portfolio, data.app_regex)

            return SuccessResponse(data=data.model_dump(mode="json"))

        except PutError as e:
            if "ConditionalCheckFailedException" in str(e):
                log.warning("App already exists: %s:%s", data.portfolio, data.app_regex)
                raise ConflictException(
                    f"App already exists: {data.portfolio}:{data.app_regex}"
                ) from e
            log.error(
                "Failed to create app %s:%s: %s", data.portfolio, data.app_regex, str(e)
            )
            raise UnknownException(
                f"Failed to create app {data.portfolio}:{data.app_regex}"
            ) from e
        except TableError as e:
            log.error(
                "Database table error while creating app %s:%s: %s",
                data.portfolio,
                data.app_regex,
                str(e),
            )
            raise UnknownException(f"Database error creating app: {str(e)}") from e
        except Exception as e:
            log.error(
                "Unexpected error creating app %s:%s: %s",
                data.portfolio,
                data.app_regex,
                str(e),
            )
            raise UnknownException(f"Unexpected error creating app: {str(e)}") from e

    @classmethod
    def update(cls, **kwargs) -> Response:
        """Update an application deployment pattern with complete replacement semantics.

        Performs a complete replacement of application data, creating the application if it
        doesn't exist or completely replacing it if it does (PUT semantics).

        Args:
            **kwargs: Complete application configuration parameters:
                     - client (str): Client name (optional if set in framework)
                     - portfolio (str): Portfolio name (required)
                     - app_regex (str): Application regex pattern (required)
                     - All desired application fields for complete replacement

        Returns:
            Response: SuccessResponse containing the updated application data

        Raises:
            BadRequestException: If required parameters are missing or invalid
            NotFoundException: If the application does not exist for update operations
            UnknownException: If database operation fails
        """
        log.info("Updating app")
        return cls._update(remove_none=True, **kwargs)

    @classmethod
    def patch(cls, **kwargs) -> Response:
        """Partially update an application deployment pattern.

        Updates only the specified fields while preserving all other existing application
        data. Only modifies existing applications - does not create new ones (PATCH semantics).

        Args:
            **kwargs: Partial application update parameters:
                     - client (str): Client name (optional if set in framework)
                     - portfolio (str): Portfolio name (required)
                     - app_regex (str): Application regex pattern (required)
                     - Any application attribute fields to update

        Returns:
            Response: SuccessResponse containing the updated application data

        Raises:
            BadRequestException: If required parameters are missing or invalid
            NotFoundException: If the application does not exist
            UnknownException: If database operation fails
        """
        log.info("Patching app")
        return cls._update(remove_none=False, **kwargs)

    @classmethod
    def _update(cls, remove_none: bool = False, **kwargs) -> Response:
        """Internal method for updating application records with configurable semantics.

        Handles both PUT (complete replacement) and PATCH (partial update) semantics
        based on the remove_none parameter. Uses DynamoDB update operations with
        conditional existence checks.

        Args:
            remove_none (bool): Whether to remove fields with None values from the database.
                              True for PUT semantics, False for PATCH semantics
            **kwargs: Application update parameters

        Returns:
            Response: SuccessResponse containing the updated application data

        Raises:
            BadRequestException: If required parameters are missing or validation fails
            NotFoundException: If the application does not exist for update
            UnknownException: If database operation fails
        """
        client = kwargs.get("client") or util.get_client()

        if not client:
            raise BadRequestException("Missing required parameter: client")

        portfolio = kwargs.get("portfolio", kwargs.get("Portfolio"))
        app_regex = kwargs.get("app_regex", kwargs.get("AppRegex"))

        if not portfolio:
            raise BadRequestException("Missing required parameter: portfolio")
        if not app_regex:
            raise BadRequestException("Missing required parameter: app_regex")

        try:
            if remove_none:
                data = AppFact(**kwargs)
            else:
                data = AppFact.model_construct(**kwargs)
        except (ValueError, ValidationError) as e:
            log.error("Invalid app data for update: %s", str(e))
            raise BadRequestException(f"Invalid app data: {str(e)}") from e

        model_class = AppFact.model_class(client)

        excluded_fields = ["portfolio", "app_regex", "created_at", "updated_at"]

        try:
            attributes = model_class.get_attributes()

            values = data.model_dump(
                by_alias=False, exclude_none=False, exclude=excluded_fields
            )

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

            # Perform the update with proper key order
            item = model_class(portfolio=data.portfolio, app_regex=data.app_regex)
            item.update(
                actions=actions,
                condition=model_class.portfolio.exists()
                & model_class.app_regex.exists(),
            )
            item.refresh()

            updated_data = AppFact.from_model(item).model_dump(mode="json")

            return SuccessResponse(
                data=updated_data,
                message=f"App {data.portfolio}:{data.app_regex} updated successfully",
            )

        except UpdateError as e:
            if "ConditionalCheckFailedException" in str(e):
                log.warning(
                    "App not found for update: %s:%s", data.portfolio, data.app_regex
                )
                raise NotFoundException(
                    f"App {data.portfolio}:{data.app_regex} does not exist"
                ) from e
            log.error(
                "Failed to update app %s:%s: %s", data.portfolio, data.app_regex, str(e)
            )
            raise UnknownException(
                f"Failed to update app {data.portfolio}:{data.app_regex}"
            ) from e
        except Exception as e:
            log.error(
                "Unexpected error updating app %s:%s: %s",
                data.portfolio,
                data.app_regex,
                str(e),
            )
            raise UnknownException(f"Unexpected error updating app: {str(e)}") from e
