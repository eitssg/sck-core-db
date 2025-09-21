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
    - Range Key: app (regex pattern for application matching)
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

from enum import auto
from typing import List, Tuple
import re
from pydantic_core import ValidationError
import hashlib
import slugify

from pynamodb.expressions.update import Action
from pynamodb.exceptions import (
    DeleteError,
    PutError,
    DoesNotExist,
    QueryError,
    ScanError,
    UpdateError,
)

import core_logging as log
import core_framework as util
from core_framework.time_utils import make_default_time

from ...exceptions import (
    BadRequestException,  # http 400
    ConflictException,  # http 409
    NotFoundException,  # http 404
    UnknownException,  # http 500
)

from ...models import Paginator
from ..actions import RegistryAction
from .models import AppFact


def _is_app_id_taken(client: str, portfolio: str, candidate: str) -> bool:
    try:
        Model = AppFact.model_class(client)
        Model.get(portfolio, candidate)  # hash=portfolio, range=app
        return True
    except DoesNotExist:
        return False
    except Exception:
        # Be conservative on unexpected errors
        return True


def generate_app_slug(
    name: str,
    *,
    client: str,
    portfolio: str,
    preferred: str | None = None,
    max_length: int = 63,
) -> str:
    source = (preferred or name or "").strip()
    base = slugify.slugify(source, lowercase=True, separator="-", max_length=max_length)
    if not base:
        base = "app"

    # avoid reserved route-y words
    if base in {"new", "create", "edit", "delete", "admin"}:
        base = f"{base}-app"

    def with_suffix(b: str, s: str) -> str:
        sfx = f"-{s}"
        if len(b) + len(sfx) > max_length:
            b = b[: max_length - len(sfx)]
        return b + sfx

    # no collision
    if not _is_app_id_taken(client, portfolio, base):
        return base

    # deterministic short hash first
    digest = hashlib.blake2b(
        f"{portfolio}:{source}".encode("utf-8"), digest_size=3
    ).hexdigest()
    cand = with_suffix(base, digest)
    if not _is_app_id_taken(client, portfolio, cand):
        return cand

    # fallback numeric counter
    for i in range(2, 50):
        cand = with_suffix(base, str(i))
        if not _is_app_id_taken(client, portfolio, cand):
            return cand

    # last resort: longer hash
    digest = hashlib.blake2b(
        f"{portfolio}:{source}".encode("utf-8"), digest_size=5
    ).hexdigest()
    return with_suffix(base, digest)


class AppActions(RegistryAction):

    @classmethod
    def list(
        cls,
        *,
        client: str,
        portfolio: str | None = None,
        app_regex: str | None = None,
        **kwargs,
    ) -> Tuple[List[AppFact], Paginator]:
        if not client:
            raise BadRequestException("Missing required parameter: client")

        try:
            paginator = Paginator(**kwargs)
        except (ValueError, ValidationError) as e:
            raise BadRequestException(f"Invalid pagination parameters: {str(e)}") from e

        if portfolio and app_regex:
            return cls._get_apps_by_portfolio_app_regex(
                client, portfolio, app_regex, paginator
            )
        elif portfolio:
            return cls._get_apps_by_portfolio(client, portfolio, paginator)
        else:
            return cls._get_all_apps_paginated(client, paginator)

    @classmethod
    def get(
        cls,
        *,
        client: str,
        portfolio: str | None = None,
        app: str | None = None,
        **kwargs,
    ) -> AppFact:
        log.info("Getting specific app for client")

        if not client:
            raise BadRequestException("Missing required parameter: client")
        if not portfolio:
            raise BadRequestException("Missing required parameter: portfolio")
        if not app:
            raise BadRequestException("Missing required parameter: app")

        return cls._get_apps_by_portfolio_app(client, portfolio, app)

    @classmethod
    def _get_apps_by_portfolio_app(
        cls, client: str, portfolio: str, app: str
    ) -> AppFact:
        log.debug("Getting specific app: %s:%s", portfolio, app)

        model_class = AppFact.model_class(client)

        try:

            item = model_class.get(portfolio, app)

            data = AppFact.from_model(item)

            return data

        except DoesNotExist as e:
            log.warning(f"Specific app not found: {portfolio}:{app}")
            raise NotFoundException(f"App {portfolio}:{app} does not exist") from e

        except Exception as e:
            log.error(f"Failed to retrieve specific app {portfolio}:{app} - {str(e)}")
            raise UnknownException(f"Failed to retrieve app {portfolio}:{app}") from e

    @classmethod
    def _get_apps_by_portfolio(
        cls, client: str, portfolio: str, paginator: Paginator
    ) -> Tuple[List[AppFact], Paginator]:
        log.debug("Getting all apps for portfolio: %s", portfolio)

        model_class = AppFact.model_class(client)

        try:
            query_kwargs = paginator.get_query_args()

            result = model_class.query(portfolio, **query_kwargs)

            data = [AppFact.from_model(item) for item in result]

            paginator.cursor = getattr(result, "last_evaluated_key", None)
            paginator.total_count = len(data)

            # Sort by app for consistent ordering
            log.info(
                "Successfully queried %d apps for portfolio: %s", len(data), portfolio
            )

            return data, paginator

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
    def _get_apps_by_portfolio_app_regex(
        cls, client: str, portfolio: str, app_regex: str, paginator: Paginator
    ) -> Tuple[List[AppFact], Paginator]:
        log.debug(
            "Filtering apps by name: %s matching patterns in portfolio: %s",
            app_regex,
            portfolio,
        )

        model_class = AppFact.model_class(client)

        try:

            query_kwargs = paginator.get_query_args()

            result = model_class.query(portfolio, **query_kwargs)

            data = []
            for item in result:
                app_fact = AppFact.from_model(item)
                try:
                    # Check if the provided value matches the stored regex pattern
                    if app_fact.app_regex and re.match(app_fact.app_regex, app_regex):
                        data.append(app_fact)
                        log.debug(
                            "Value '%s' matches pattern '%s'",
                            app_regex,
                            app_fact.app_regex,
                        )
                except re.error:
                    # Skip invalid regex patterns
                    log.warning(
                        "Invalid regex pattern in app_regex: %s", app_fact.app_regex
                    )
                    continue

            paginator.cursor = getattr(result, "last_evaluated_key", None)
            paginator.total_count = len(data)

            log.info(
                "Successfully filtered %d apps matching name: %s", len(data), app_regex
            )

            # Returns a list of applications that match the app regex
            return data, paginator

        except QueryError as e:
            log.error("Failed to query apps for portfolio %s - %s", portfolio, str(e))
            raise UnknownException(
                f"Failed to query apps for portfolio {portfolio}"
            ) from e

        except Exception as e:
            log.error(
                "Unexpected error while filtering apps by name %s in portfolio %s - %s",
                app_regex,
                portfolio,
                str(e),
            )
            raise UnknownException(
                f"Unexpected error while filtering apps for {portfolio}:{app_regex}"
            ) from e

    @classmethod
    def _get_all_apps_paginated(
        cls, client: str, paginator: Paginator
    ) -> Tuple[List[AppFact], Paginator]:
        log.debug("Scanning all apps for client: %s", client)

        model_class = AppFact.model_class(client)

        try:

            scan_kwargs = paginator.get_scan_args()

            result = model_class.scan(**scan_kwargs)

            data = [AppFact.from_model(item) for item in result]

            paginator.cursor = getattr(result, "last_evaluated_key", None)
            paginator.total_count = len(data)

            return data, paginator

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
    def delete(
        cls,
        *,
        client: str,
        portfolio: str | None = None,
        app: str | None = None,
        **kwargs,
    ) -> bool:
        log.info("Deleting app")

        if not client:
            raise BadRequestException("Missing required parameter: client")
        if not portfolio:
            raise BadRequestException("Missing required parameter: portfolio")
        if not app:
            raise BadRequestException("Missing required parameter: app")

        model_class = AppFact.model_class(client)

        try:
            log.debug("Deleting app: %s:%s", portfolio, app)

            item = model_class(portfolio, app)

            item.delete(
                condition=model_class.portfolio.exists() & model_class.app.exists()
            )

            log.info("Successfully deleted app: %s:%s", portfolio, app)

            return True

        except DeleteError as e:
            if "ConditionalCheckFailedException" in str(e):
                log.info("App not found for deletion: %s:%s", portfolio, app)
                raise NotFoundException(
                    f"App [{portfolio}:{app}] was deleted by another process"
                )

            log.error("Failed to delete app: %s:%s - %s", portfolio, app, str(e))
            raise UnknownException(f"Failed to delete app {portfolio}:{app}") from e

        except Exception as e:
            log.error(
                "Unexpected error deleting app %s:%s - %s", portfolio, app, str(e)
            )
            raise UnknownException(
                f"Unexpected error deleting app {portfolio}:{app}"
            ) from e

    @classmethod
    def create(cls, *, client: str, record: AppFact | None = None, **kwargs) -> AppFact:
        log.info("Creating app")

        if not client:
            raise BadRequestException("Missing required parameter: client")

        try:
            if not record:
                portfolio = kwargs.get("portfolio")
                if not portfolio:
                    raise BadRequestException("Missing required parameter: portfolio")

                name = kwargs.get("name")
                app = kwargs.get("app")

                if not name:
                    name = app or "app"
                    kwargs["name"] = name

                if not app:
                    auto_gen = True
                    app = generate_app_slug(
                        name=name,
                        client=client or util.get_client(),
                        portfolio=portfolio,
                    )
                    kwargs["app"] = app
                else:
                    auto_gen = False

                app_regex = kwargs.get("app_regex")
                if not app_regex:
                    app_regex = rf"^prn:{portfolio}:{re.escape(name)}:*:*$"
                    kwargs["app_regex"] = app_regex

                # Validate and construct the AppFact record
                record = AppFact(**kwargs)

        except Exception as e:
            log.error("Invalid app data: %s", str(e))
            raise BadRequestException(f"Invalid app data: {str(e)}")

        model_class = AppFact.model_class(client)
        item = record.to_model(client)

        for _ in range(3):
            try:

                # Uniqueness on the range key `app` (within the given portfolio)
                item.save(model_class.app.does_not_exist())

                log.info(
                    "Successfully created app: %s:%s", record.portfolio, record.app
                )

                return record

            except PutError as e:
                if "ConditionalCheckFailedException" in str(e):

                    if auto_gen:
                        # Rare race: regenerate and retry a couple of times, then fail.
                        log.warning(
                            "App creation conflict, retrying with new slug: %s:%s",
                            portfolio,
                            app,
                        )

                        item.app = generate_app_slug(
                            name=name,
                            client=client,
                            portfolio=portfolio,
                            preferred=item.app,  # keep base, add next suffix
                        )
                        continue

                    raise ConflictException(
                        f"App {item.portfolio}:{item.app} already exists"
                    ) from e

                # Non-conditional failure
                log.error(
                    "Failed to create app %s:%s: %s", item.portfolio, item.app, str(e)
                )
                raise UnknownException(
                    f"Failed to create app {item.portfolio}:{item.app}"
                ) from e

            except Exception as e:
                log.error(
                    "Unexpected error creating app %s:%s: %s",
                    item.portfolio,
                    item.app,
                    str(e),
                )
                raise UnknownException(
                    f"Unexpected error creating app: {str(e)}"
                ) from e

        raise ConflictException(
            f"Cannot create app due to app conflict: {str(e)}"
        ) from e

    @classmethod
    def update(cls, *, client: str, record: AppFact | None = None, **kwargs) -> AppFact:
        log.info("Updating app")
        return cls._update(remove_none=True, client=client, record=record, **kwargs)

    @classmethod
    def patch(cls, *, client: str, **kwargs) -> AppFact:
        log.info("Patching app")
        return cls._update(remove_none=False, client=client, **kwargs)

    @classmethod
    def _update(
        cls, remove_none: bool, client: str, record: AppFact | None = None, **kwargs
    ) -> AppFact:
        if not client:
            raise BadRequestException("Missing required parameter: client")

        excluded_fields = ["portfolio", "app", "created_at", "updated_at"]

        if record:
            values = record.model_dump(
                by_alias=False, exclude_none=False, exclude=excluded_fields
            )
        else:
            values = kwargs

        portfolio = values.get("portfolio")
        app = values.get("app")

        if not portfolio:
            raise BadRequestException("Missing required parameter: portfolio")
        if not app:
            raise BadRequestException("Missing required parameter: app")

        model_class = AppFact.model_class(client)

        try:
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

            # Perform the update with proper key order
            item = model_class(portfolio, app)
            item.update(
                actions=actions,
                condition=model_class.portfolio.exists() & model_class.app.exists(),
            )
            item.refresh()

            return AppFact.from_model(item)

        except UpdateError as e:
            if "ConditionalCheckFailedException" in str(e):
                log.warning("App not found for update: %s:%s", portfolio, app)
                raise NotFoundException(f"App {portfolio}:{app} does not exist") from e

            log.error("Failed to update app %s:%s: %s", portfolio, app, str(e))
            raise UnknownException(f"Failed to update app {portfolio}:{app}") from e

        except Exception as e:
            log.error("Unexpected error updating app %s:%s: %s", portfolio, app, str(e))
            raise UnknownException(f"Unexpected error updating app: {str(e)}") from e
