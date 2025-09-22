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

from typing import List, Tuple

from pynamodb.expressions.update import Action
from pynamodb.exceptions import (
    DeleteError,
    PutError,
    QueryError,
    ScanError,
    DoesNotExist,
    UpdateError,
)

import core_framework as util
from core_framework.time_utils import make_default_time

import core_logging as log

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

    @classmethod
    def list(cls, *, client: str, **kwargs) -> Tuple[List[PortfolioFact], Paginator]:
        log.info("Listing portfolios for client")

        if not client:
            raise BadRequestException('Client name is required in content: { "client": "<name>", ... }')

        try:
            paginator = Paginator(**kwargs)
        except ValueError as e:
            raise BadRequestException(f"Invalid pagination parameters: {str(e)}")

        model_class = PortfolioFact.model_class(client)

        try:
            log.debug("Querying portfolios for client: %s", client)

            scan_args = paginator.get_scan_args()

            result = model_class.scan(**scan_args)

            # Convert PynamoDB items to simple dictionaries
            data = [PortfolioFact.from_model(item) for item in result]

            paginator.last_evaluated_key = getattr(result, "last_evaluated_key", None)
            paginator.total_count = len(data)

            log.info("Successfully retrieved %d portfolios for client: %s", len(data), client)

            return data, paginator

        except ScanError as e:
            log.error("Failed to list portfolios for client %s: %s", client, str(e))
            raise UnknownException(f"Failed to list portfolios for client {client}: {str(e)}") from e

        except Exception as e:
            log.error("Failed to list portfolios for client %s: %s", client, str(e))
            raise UnknownException(f"Failed to list portfolios for client {client}: {str(e)}") from e

    @classmethod
    def get(cls, *, client: str, portfolio: str) -> PortfolioFact:
        log.info("Getting portfolio")

        if not client:
            raise BadRequestException("Client name is required")

        if not portfolio:
            raise BadRequestException("Portfolio name is required")

        model_class = PortfolioFact.model_class(client)

        try:
            log.debug("Retrieving portfolio: %s:%s", client, portfolio)

            item = model_class.get(portfolio)

            data = PortfolioFact.from_model(item)

            return data

        except DoesNotExist:
            log.warning("Portfolio not found: %s:%s", client, portfolio)
            raise NotFoundException(f"Portfolio {client}:{portfolio} does not exist")

        except Exception as e:
            log.error("Failed to get portfolio %s:%s: %s", client, portfolio, str(e))
            raise UnknownException(f"Failed to get portfolio: {str(e)}")

    @classmethod
    def delete(cls, *, client: str, portfolio: str) -> bool:
        log.info("Deleting portfolio")

        if not client or not portfolio:
            raise BadRequestException("Client and portfolio names are required for deletion}")

        model_class = PortfolioFact.model_class(client)

        try:

            log.debug("Retrieving portfolio for deletion: %s:%s", client, portfolio)

            item = model_class(portfolio)
            item.delete(condition=model_class.portfolio.exists())

            return True

        except DeleteError as e:
            if "ConditionalCheckFailedException" in str(e):
                log.info("Portfolio not found for deletion: %s:%s", client, portfolio)
                raise NotFoundException(f"Portfolio {client}:{portfolio} does not exist or was deleted by another process")

            log.error("Failed to delete portfolio %s:%s: %s", client, portfolio, str(e))
            raise UnknownException(f"Failed to delete portfolio {client}:{portfolio}: {str(e)}") from e

        except Exception as e:
            log.error(f"Unexpected error deleting portfolio {client}:{portfolio}: {str(e)}")
            raise UnknownException(f"Failed to delete portfolio {client}:{portfolio}: {str(e)}") from e

    @classmethod
    def create(cls, *, client: str, record: PortfolioFact | None = None, **kwargs) -> PortfolioFact:
        log.info("Creating portfolio")

        if not client:
            raise BadRequestException('Client name is required in content: { "client": "<name>", ... }')

        try:
            if not record:
                record = PortfolioFact(**kwargs)
        except ValueError as e:
            raise BadRequestException(f"Invalid portfolio data: {str(e)}")

        portfolio = record.portfolio
        if not portfolio:
            raise BadRequestException('Portfolio name is required in content: { "portfolio": "<name>", ... }')

        model_class = PortfolioFact.model_class(client)

        try:
            item = record.to_model(client)
            item.save(model_class.portfolio.does_not_exist())

            return PortfolioFact.from_model(item)

        except PutError as e:
            if "ConditionalCheckFailedException" in str(e):
                log.warning("Portfolio %s:%s already exists", client, portfolio)
                raise ConflictException(f"Portfolio {client}:{portfolio} already exists")

            log.error("Failed to create portfolio %s:%s: %s", client, portfolio, str(e))
            raise UnknownException(f"Failed to create portfolio {client}:{portfolio}: {str(e)}") from e
        except Exception as e:
            log.error("Failed to create portfolio %s:%s: %s", client, portfolio, str(e))
            raise UnknownException(f"Failed to create portfolio {client}:{portfolio}: {str(e)}") from e

    @classmethod
    def update(cls, *, client: str, record: PortfolioFact | None = None, **kwargs) -> PortfolioFact:
        log.info("Updating portfolio")

        return cls._update(remove_none=True, client=client, record=record, **kwargs)

    @classmethod
    def patch(cls, *, client: str, **kwargs) -> PortfolioFact:
        log.info("Patching portfolio")

        return cls._update(remove_none=False, client=client, **kwargs)

    @classmethod
    def _update(
        cls,
        *,
        remove_none: bool,
        client: str,
        record: PortfolioFact | None = None,
        **kwargs,
    ) -> PortfolioFact:
        log.info("Updating portfolio")

        if not client:
            raise BadRequestException('Client name is required in content: { "client": "<name>", ... }')

        excluded_fields = {"client", "portfolio", "created_at", "updated_at"}

        if record:
            values = record.model_dump(by_alias=False, exclude_none=False, exclude=excluded_fields)
        else:
            values = kwargs

        portfolio = values.get("portfolio")
        if not portfolio:
            raise BadRequestException('Portfolio name is required in content: { "portfolio": "<name>", ... }')

        model_class = PortfolioFact.model_class(client)

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

            return PortfolioFact.from_model(item)

        except UpdateError as e:
            if "ConditionalCheckFailedException" in str(e):
                log.warning("Portfolio %s:%s does not exist", client, portfolio)
                raise NotFoundException(f"Portfolio {client}:{portfolio} does not exist or condition check failed")

            log.error("Failed to update portfolio %s:%s: %s", client, portfolio, str(e))
            raise UnknownException(f"Failed to update portfolio {client}:{portfolio}: Permission denied or condition check failed")

        except Exception as e:
            log.error("Failed to update portfolio %s:%s: %s", client, portfolio, str(e))
            raise UnknownException(f"Failed to update portfolio: {str(e)}")
