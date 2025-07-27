"""Defines the get method for the Facts table view."""

import os
import core_framework as util

from core_framework.constants import (
    SCOPE_CLIENT,
    SCOPE_PORTFOLIO,
    SCOPE_APP,
    SCOPE_BRANCH,
    SCOPE_BUILD,
    SCOPE_COMPONENT,
    SCOPE_ZONE,
)

from core_framework.models import DeploymentDetails

from ..constants import PRN
from ..actions import TableActions

from ..response import Response, SuccessResponse
from ..exceptions import BadRequestException

from .facter import get_facts


class FactsActions(TableActions):
    """
    This is a VIEW model on the registry combining the following 4 tables into a "context" for Jinja2 rendering.

    1. Load Registry Client Facts
    2. Load Registry Portfolio Facts
    3. Load Registry App Facts
    4. Load Registry Zone Facts

    Combine them with a deep merge and present as the Jinja2 Context (a.k.a. Facts)

    """

    @classmethod
    def validate_prn_scope(
        cls, prn: str | None
    ) -> tuple[str | None, str | None, str | None, str | None, str | None]:
        """
        Validate PRN format and extract scope components.

        Validates the provided PRN against the expected format for its scope
        and extracts the hierarchical components (portfolio, app, branch, build, component).

        :param prn: Pipeline Reference Number to validate and parse
        :type prn: str | None
        :returns: Tuple of (portfolio, app, branch, build, component) extracted from PRN
        :rtype: tuple[str | None, str | None, str | None, str | None, str | None]
        :raises BadRequestException: If PRN is None, has invalid scope, or fails validation

        Examples
        --------
        >>> # Portfolio PRN
        >>> portfolio, app, branch, build, component = cls.validate_prn_scope("prn:core")
        >>> # Returns: ("core", None, None, None, None)

        >>> # App PRN
        >>> portfolio, app, branch, build, component = cls.validate_prn_scope("prn:core:api")
        >>> # Returns: ("core", "api", None, None, None)

        >>> # Build PRN
        >>> portfolio, app, branch, build, component = cls.validate_prn_scope("prn:core:api:master:1234")
        >>> # Returns: ("core", "api", "master", "1234", None)
        """
        # Validation mapping: scope -> (validator_function, expected_parts_count)
        validators = {
            SCOPE_PORTFOLIO: (util.validate_portfolio_prn, 2),  # prn:portfolio
            SCOPE_APP: (util.validate_app_prn, 3),  # prn:portfolio:app
            SCOPE_BRANCH: (util.validate_branch_prn, 4),  # prn:portfolio:app:branch
            SCOPE_BUILD: (util.validate_build_prn, 5),  # prn:portfolio:app:branch:build
            SCOPE_COMPONENT: (
                util.validate_component_prn,
                6,
            ),  # prn:portfolio:app:branch:build:component
        }

        if prn is None:
            raise BadRequestException("PRN must be provided to the facts API")

        scope = util.prn_utils.get_prn_scope(prn)
        parts = prn.split(":")

        # Default values
        portfolio = app = branch = build = component = None

        if scope == SCOPE_CLIENT:
            # Client PRN has no portfolio/app/branch/build/component info
            return portfolio, app, branch, build, component

        if scope not in validators:
            raise BadRequestException(f"Invalid scope: {scope}")

        validator_func, num_parts = validators[scope]

        if not validator_func(prn):
            raise BadRequestException(f"Invalid PRN: {prn}. Not a valid {scope} PRN.")

        # Extract components from PRN format: prn:portfolio:app:branch:build:component
        # Skip "prn" part and extract the hierarchy components
        if len(parts) >= 2:  # At least portfolio
            portfolio = parts[1]
        if len(parts) >= 3:  # At least app
            app = parts[2]
        if len(parts) >= 4:  # At least branch
            branch = parts[3]
        if len(parts) >= 5:  # At least build
            build = parts[4]
        if len(parts) >= 6:  # Component
            component = parts[5]

        return portfolio, app, branch, build, component

    @classmethod
    def get(cls, **kwargs: dict) -> Response:
        """
        Retrieve Facts for a specific deployment context.

        Combines registry data from multiple sources (Client, Portfolio, App, Zone)
        to create a complete Jinja2 context for template rendering.

        :param kwargs: Request parameters including client and PRN information
        :type kwargs: dict
        :returns: Response containing the merged facts data
        :rtype: Response
        :raises BadRequestException: If required parameters are missing or invalid

        Examples
        --------
        >>> # Get facts for an app deployment
        >>> response = FactsActions.get(
        ...     client="acme",
        ...     prn="prn:core:api"
        ... )

        >>> # Get facts for a specific build
        >>> response = FactsActions.get(
        ...     client="acme",
        ...     prn="prn:core:api:master:1234"
        ... )
        """
        # The client information can come from the query string or the environment variables
        # client must come from pathParameters
        client = str(kwargs.pop(SCOPE_CLIENT, util.get_client()))

        # based on the scope, is the PRN valid? The PRN must be specified in the query parameters
        prn = str(kwargs.pop(PRN, kwargs.pop(SCOPE_ZONE, None)))

        if not prn or prn == "None":
            raise BadRequestException("PRN must be provided to retrieve Facts")

        portfolio, app, branch, build, component = cls.validate_prn_scope(prn)

        if not client:
            raise BadRequestException("Client is required to retrieve Facts")

        if not portfolio or not app:
            raise BadRequestException(
                "Client, portfolio, and app are required in the PRN to retrieve Facts"
            )

        deployment_details = DeploymentDetails(
            Client=client,
            Portfolio=portfolio,
            App=app,
            Branch=branch,
            Build=build,
            Component=component,
        )

        the_facts = get_facts(deployment_details)

        return SuccessResponse(the_facts)
