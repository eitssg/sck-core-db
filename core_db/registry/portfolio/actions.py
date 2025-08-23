"""Portfolio registry actions for the core-automation-registry DynamoDB table.

This module provides comprehensive CRUD operations for portfolio management within the registry
system. Portfolios represent organizational units within clients that group related applications
and deployment patterns.

Key Features:
    - **Portfolio Lifecycle Management**: Complete CRUD operations for portfolio entities
    - **Client Isolation**: Factory pattern ensures proper table isolation between clients
    - **Flexible Parameter Handling**: Supports various portfolio identifier formats
    - **Comprehensive Error Handling**: Detailed exception mapping for different failure scenarios
    - **Atomic Operations**: Uses DynamoDB UpdateItem and conditional checks

Examples:
    >>> from core_db.registry.portfolio.actions import PortfolioActions

    >>> # Create a new portfolio
    >>> result = PortfolioActions.create(
    ...     client="acme",
    ...     portfolio="web-services",
    ...     description="Web-based applications and APIs",
    ...     contact_email="webteam@acme.com",
    ...     environment_strategy="blue-green"
    ... )

    >>> # List all portfolios for a client
    >>> portfolios = PortfolioActions.list()
    >>> for portfolio in portfolios.data:
    ...     print(f"Portfolio: {portfolio['Portfolio']}")
    ...     print(f"Description: {portfolio.get('description')}")

    >>> # Get specific portfolio
    >>> portfolio = PortfolioActions.get(client="acme", portfolio="web-services")
    >>> print(f"Contact: {portfolio.data.get('contact_email')}")

    >>> # Update portfolio configuration
    >>> result = PortfolioActions.patch(
    ...     client="acme",
    ...     portfolio="web-services",
    ...     description="Updated: Web services and microservices",
    ...     deployment_regions=["us-east-1", "us-west-2"]
    ... )

Related Modules:
    - core_db.registry.portfolio.models: PortfolioFactsModel and factory for table management
    - core_db.registry.actions: Base RegistryAction class with common functionality
    - core_db.registry: Registry system for deployment automation patterns

Note:
    All methods expect kwargs containing merged parameters from HTTP requests.
    Client and portfolio parameters are required for most operations and are extracted from kwargs.
"""

from pydantic import ValidationError
from pynamodb.expressions.update import Action
from pynamodb.exceptions import (
    DeleteError,
    PutError,
    QueryError,
    DoesNotExist,
    TableError,
    UpdateError,
    ScanError,
)

import core_framework as util
from core_framework.time_utils import make_default_time

import core_logging as log

from ...response import (
    SuccessResponse,  # http 200
    Response,
    NoContentResponse,  # http 204
)
from ...exceptions import (
    ConflictException,  # http 409
    UnknownException,  # http 500
    BadRequestException,  # http 400
    NotFoundException,  # http 404
)

from ...models import Paginator
from ..actions import RegistryAction
from .models import PortfolioFact


class PortfolioActions(RegistryAction):
    """Actions for managing portfolio registry entries.

    Provides comprehensive CRUD operations for portfolio management with proper error handling
    and validation. Portfolios represent organizational units within clients that group
    related applications and deployment patterns.

    The class handles portfolio management within client-scoped tables and supports flexible
    parameter parsing for maximum compatibility with different API patterns.

    """

    @classmethod
    def list(cls, **kwargs) -> Response:
        """List all portfolios for a specific client.

        Retrieves all portfolio registry entries for the specified client with complete
        metadata and configuration. Results are sorted by portfolio name for consistent
        ordering and include full portfolio details.

        Args:
            **kwargs: Parameters containing client identification and optional pagination.

                      Required Fields:
                         client (str): Client name to list portfolios for (optional if set in framework).

                     Optional Fields:
                         limit (int): Maximum number of results per page
                         cursor (str): Pagination cursor for next page

        Returns:
            Response: SuccessResponse containing list of portfolio dictionaries with complete metadata
                 - Sorted by Portfolio field for consistent ordering
                 - Empty list if no portfolios found for the client

        Raises:
            BadRequestException: If client parameter is missing from kwargs.
            UnknownException: If database query fails due to connection issues or
                            other unexpected errors.

        """
        log.info("Listing portfolios for client")

        client = kwargs.get("client", kwargs.get("Client")) or util.get_client()
        if not client:
            raise BadRequestException(
                'Client name is required in content: { "client": "<name>", ... }'
            )

        try:
            paginator = Paginator(**kwargs)
        except ValueError as e:
            raise BadRequestException(f"Invalid pagination parameters: {str(e)}")

        model_class = PortfolioFact.model_class(client)

        try:
            log.debug("Querying portfolios for client: %s", client)

            result = model_class.query(
                client, consistent_read=True, last_evaluated_key=paginator.cursor
            )

            # Convert PynamoDB items to simple dictionaries
            data = [
                PortfolioFact.from_model(item).model_dump(mode="json")
                for item in result
            ]

            paginator.cursor = getattr(result, "last_evaluated_key", None)
            paginator.total_count = getattr(result, "total_count", len(data))

            log.info(
                "Successfully retrieved %d portfolios for client: %s", len(data), client
            )

            return SuccessResponse(data=data, metadata=paginator.get_metadata())
        except QueryError as e:
            log.error("Failed to list portfolios for client %s: %s", client, str(e))
            raise UnknownException(
                f"Failed to list portfolios for client {client}: {str(e)}"
            ) from e
        except Exception as e:
            log.error("Failed to list portfolios for client %s: %s", client, str(e))
            raise UnknownException(
                f"Failed to list portfolios for client {client}: {str(e)}"
            ) from e

    @classmethod
    def get(cls, **kwargs) -> Response:
        """Retrieve a specific portfolio registry entry.

        Fetches the complete configuration and metadata for a specific portfolio identified
        by client and portfolio name. Returns detailed portfolio information including
        organizational details and deployment configuration.

        Args:
            **kwargs: Parameters identifying the specific portfolio.

                      Required Fields:
                         client (str): Client name (optional if set in framework).
                         portfolio (str): Portfolio name to retrieve (required).

        Returns:
            Response: SuccessResponse containing complete portfolio data dictionary,
                     or NoContentResponse if portfolio not found.

        Raises:
            BadRequestException: If required client or portfolio parameters are missing.
            UnknownException: If database operation fails due to connection issues,
                            table access problems, or permission issues.

        """
        log.info("Getting portfolio")

        client = kwargs.get("client", kwargs.get("Client")) or util.get_client()
        portfolio = kwargs.get("portfolio", kwargs.get("Portfolio"))

        if not client or not portfolio:
            raise BadRequestException(
                'Client and portfolio names are required in content: { "client": "<name>", "portfolio": "<name>", ... }'
            )

        model_class = PortfolioFact.model_class(client)

        try:
            log.debug("Retrieving portfolio: %s:%s", client, portfolio)

            item = model_class.get(portfolio)

            data = PortfolioFact.from_model(item).model_dump(mode="json")

            log.info("Successfully retrieved portfolio: %s:%s", client, portfolio)

            return SuccessResponse(data=data)

        except DoesNotExist:
            log.warning("Portfolio not found: %s:%s", client, portfolio)
            return NoContentResponse(
                data={"message": f"Portfolio {client}:{portfolio} does not exist"}
            )
        except Exception as e:
            log.error("Failed to get portfolio %s:%s: %s", client, portfolio, str(e))
            raise UnknownException(f"Failed to get portfolio: {str(e)}")

    @classmethod
    def delete(cls, **kwargs) -> Response:
        """Delete a portfolio registry entry.

        Removes the specified portfolio from the client's registry. Returns success
        confirmation or handles not found scenarios gracefully with NoContentResponse.

        Args:
            **kwargs: Parameters identifying the portfolio to delete.

                      Required Fields:
                         client (str): Client name (optional if set in framework).
                         portfolio (str): Portfolio name to delete (required).

        Returns:
            Response: SuccessResponse with deletion confirmation message,
                     or NoContentResponse if portfolio not found.

        Raises:
            BadRequestException: If required client or portfolio parameters are missing.
            UnknownException: If database operation fails during retrieval or deletion.

        """
        log.info("Deleting portfolio")

        client = kwargs.get("client", kwargs.get("Client")) or util.get_client()
        portfolio = kwargs.get("portfolio", kwargs.get("Portfolio"))

        if not client or not portfolio:
            raise BadRequestException(
                'Client and portfolio names are required in content: { "client": "<name>", "portfolio": "<name>", ... }'
            )

        model_class = PortfolioFact.model_class(client)

        try:
            log.debug("Retrieving portfolio for deletion: %s:%s", client, portfolio)
            item = model_class.get(portfolio)
            item.delete()

            return SuccessResponse(message=f"Portfolio deleted: {client}:{portfolio}")

        except DoesNotExist:
            log.warning("Portfolio not found for deletion: %s:%s", client, portfolio)
            return NoContentResponse(
                data={"message": f"Portfolio {client}:{portfolio} does not exist"}
            )
        except DeleteError as e:
            log.error("Failed to delete portfolio %s:%s: %s", client, portfolio, str(e))
            raise UnknownException(
                f"Failed to delete portfolio {client}:{portfolio}: {str(e)}"
            ) from e
        except Exception as e:
            log.error(
                "Unexpected error deleting portfolio %s:%s: %s",
                client,
                portfolio,
                str(e),
            )
            raise UnknownException(
                f"Failed to delete portfolio {client}:{portfolio}: {str(e)}"
            ) from e

    @classmethod
    def create(cls, **kwargs) -> Response:
        """Create a new portfolio registry entry.

        Creates a new portfolio within the specified client with the provided configuration
        and metadata. Fails if a portfolio with the same client-portfolio combination already
        exists, ensuring unique portfolio names per client.

        Args:
            **kwargs: Parameters for portfolio creation.

                      Required Fields:
                         client (str): Client name (optional if set in framework).
                         portfolio (str): Unique portfolio name within client (required).

                      Optional Portfolio Attributes:
                         All PortfolioFact fields are supported for portfolio configuration.

        Returns:
            Response: SuccessResponse containing the created portfolio data with all fields.

        Raises:
            BadRequestException: If required parameters are missing, have invalid format,
                                or portfolio data validation fails.
            ConflictException: If portfolio already exists with the same portfolio name
                             within the client.
            UnknownException: If database operation fails due to connection issues or
                             other unexpected errors.

        """
        log.info("Creating portfolio")

        client = kwargs.get("client", kwargs.get("Client")) or util.get_client()
        portfolio = kwargs.get("portfolio", kwargs.get("Portfolio"))

        try:
            data = PortfolioFact(**kwargs)

        except (ValueError, ValidationError) as e:
            log.error("Invalid portfolio data for %s:%s: %s", client, portfolio, str(e))
            raise BadRequestException(f"Invalid portfolio data: {kwargs}: {str(e)}")

        try:
            item = data.to_model(client)
            item.save(type(item).portfolio.does_not_exist())

            data = PortfolioFact.from_model(item).model_dump(mode="json")

            return SuccessResponse(
                data=data,
                message=f"Portfolio {client}:{portfolio} created successfully",
            )

        except PutError as e:
            if "ConditionalCheckFailedException" in str(e):
                log.warning("Portfolio %s:%s already exists", client, portfolio)
                raise ConflictException(
                    f"Portfolio {client}:{portfolio} already exists"
                )
            log.error("Failed to create portfolio %s:%s: %s", client, portfolio, str(e))
            raise UnknownException(
                f"Failed to create portfolio {client}:{portfolio}: {str(e)}"
            ) from e
        except Exception as e:
            log.error("Failed to create portfolio %s:%s: %s", client, portfolio, str(e))
            raise UnknownException(
                f"Failed to create portfolio {client}:{portfolio}: {str(e)}"
            ) from e

    @classmethod
    def update(cls, **kwargs) -> Response:
        """Create or completely replace a portfolio registry entry (PUT semantics).

                Performs a complete replacement of portfolio data, creating the portfolio if it
                doesn't exist or completely replacing it if it does. All provided fields become
                the new portfolio configuration, removing any previously set fields not included.

                Args:
                    **kwargs: Complete portfolio configuration parameters.

                              Required Fields:
                                 client (str): Client name (optional if set in framework).
                                 portfolio (str): Portfolio name (required).

                              Portfolio Attributes:
                                  All desired portfolio fields. Missing fields will not be
                                  present in the updated portfolio (complete replacement).

                Returns:
                    Response: SuccessResponse containing the complete updated portfolio data.

                Raises:
                    BadRequestException: If required client or portfolio parameters are missing.
        +            NotFoundException: If the portfolio does not exist for update operations.
                    UnknownException: If database operation fails due to connection issues or
                                     other unexpected errors.
        """
        log.info("Updating portfolio")

        return cls._update(remove_none=True, **kwargs)

    @classmethod
    def patch(cls, **kwargs) -> Response:
        """Partially update specific fields of a portfolio (PATCH semantics).

        Updates only the specified fields while preserving all other existing portfolio
        data. Only modifies existing portfolios - does not create new ones. Supports
        field removal by setting values to None.

        Args:
            **kwargs: Partial portfolio update parameters.

                      Required Fields:
                         client (str): Client name (optional if set in framework).
                         portfolio (str): Portfolio name (required).

                      Optional Update Fields:
                          Any portfolio attribute fields to update.
                          Set field to None to remove it from the portfolio.
                          Only modified fields will be updated in the database.

        Returns:
            Response: SuccessResponse containing the complete updated portfolio data
                     with all fields (modified and unchanged).

        Raises:
            BadRequestException: If required client or portfolio parameters are missing,
                               or if portfolio data validation fails.
            NotFoundException: If the portfolio does not exist.
            UnknownException: If database operation fails due to connection issues,
                            table access problems, or permission issues.
        """
        log.info("Patching portfolio")

        return cls._update(remove_none=False, **kwargs)

    @classmethod
    def _update(cls, remove_none: bool = True, **kwargs) -> Response:
        """Internal method for portfolio updates with configurable None handling.

        Handles both PUT (complete replacement) and PATCH (partial update) semantics
        based on the remove_none parameter. Uses DynamoDB update operations with
        conditional existence checks.

        Args:
            remove_none (bool): Whether to remove fields with None values from the database.
                              True for PUT semantics, False for PATCH semantics.
            **kwargs: Portfolio update parameters.

                      Required Fields:
                         client (str): Client name (optional if set in framework).
                         portfolio (str): Portfolio name (required).

                     Portfolio Attributes:
                         Fields to update. Behavior depends on remove_none parameter.

        Returns:
            Response: SuccessResponse containing the complete updated portfolio data.

        Raises:
            BadRequestException: If required parameters are missing or validation fails.
            NotFoundException: If the portfolio does not exist for update.
            UnknownException: If database operation fails due to connection issues or
                             other unexpected errors.

        Implementation Details:
            - Uses DynamoDB UpdateItem with conditional existence check
            - Builds atomic update actions for each modified field
            - Automatically updates the updated_at timestamp
            - Validates input data based on remove_none parameter
            - Refreshes item after update to return current state
        """
        log.info("Updating portfolio")

        client = kwargs.get("client", kwargs.get("Client")) or util.get_client()
        portfolio = kwargs.get("portfolio", kwargs.get("Portfolio"))

        if not client or not portfolio:
            raise BadRequestException(
                'Client and portfolio names are required in content: { "client": "<name>", "portfolio": "<name>", ... }'
            )

        try:
            if remove_none:
                data = PortfolioFact(**kwargs)
            else:
                data = PortfolioFact.model_construct(**kwargs)
        except (ValueError, ValidationError) as e:
            log.error(
                "Invalid portfolio data for %s:%s: %s",
                kwargs.get("client"),
                kwargs.get("portfolio"),
                str(e),
            )
            raise BadRequestException(f"Invalid portfolio data: {kwargs}: {str(e)}")

        model_class = PortfolioFact.model_class(client)

        excluded_fields = {"client", "portfolio", "created_at", "updated_at"}

        values = data.model_dump(
            by_alias=False, exclude_none=False, exclude=excluded_fields
        )

        try:
            # Build update actions for changed fields
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

            item = model_class(portfolio)
            item.update(actions=actions, condition=model_class.portfolio.exists())
            item.refresh()

            data = PortfolioFact.from_model(item).model_dump(mode="json")

            log.info("Successfully updated portfolio: %s:%s", client, portfolio)

            return SuccessResponse(data=data)

        except UpdateError as e:
            if "ConditionalCheckFailedException" in str(e):
                log.warning("Portfolio %s:%s does not exist", client, portfolio)
                raise NotFoundException(
                    f"Portfolio {client}:{portfolio} does not exist or condition check failed"
                )
            raise UnknownException(
                f"Failed to update portfolio {client}:{portfolio}: Permission denied or condition check failed"
            )
        except Exception as e:
            log.error("Failed to update portfolio %s:%s: %s", client, portfolio, str(e))
            raise UnknownException(f"Failed to update portfolio: {str(e)}")
