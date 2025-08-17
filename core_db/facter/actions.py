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
    """Facts actions for registry data aggregation and Jinja2 context generation.

    This is a VIEW model on the registry that combines multiple tables into a unified
    context for Jinja2 template rendering. The FactsActions class provides methods
    to validate PRNs and retrieve aggregated facts for deployment operations.

    Data Sources:
        1. **Registry Client Facts**: Global client configuration and settings
        2. **Registry Portfolio Facts**: Portfolio-specific metadata and contacts
        3. **Registry App Facts**: Application deployment parameters and repository info
        4. **Registry Zone Facts**: AWS account, region, and environment configuration

    Features:
        - **PRN Validation**: Validates and parses Pipeline Reference Numbers by scope
        - **Data Aggregation**: Deep merges registry data from multiple sources
        - **Jinja2 Context**: Provides complete template rendering context
        - **Scope-aware Processing**: Handles different PRN scopes (portfolio, app, build, etc.)

    Examples:
        >>> # Get facts for app deployment
        >>> response = FactsActions.get(
        ...     client="acme",
        ...     prn="prn:web-services:api"
        ... )
        >>> facts = response.data
        >>> print(facts["Client"])        # "acme"
        >>> print(facts["AwsAccountId"])  # "738499099231"

        >>> # Get facts for specific build
        >>> response = FactsActions.get(
        ...     client="acme",
        ...     prn="prn:web-services:api:main:1234"
        ... )
        >>> build_facts = response.data
        >>> print(build_facts["Build"])   # "1234"
        >>> print(build_facts["Branch"])  # "main"
    """

    @classmethod
    def validate_prn_scope(cls, prn: str | None) -> tuple[str | None, str | None, str | None, str | None, str | None]:
        """Validate PRN format and extract scope components.

        Validates the provided PRN against the expected format for its scope
        and extracts the hierarchical components (portfolio, app, branch, build, component).
        Each scope has specific validation rules and expected component counts.

        Args:
            prn (str | None): Pipeline Reference Number to validate and parse.
                Must follow format: "prn:portfolio:app:branch:build:component"
                depending on the scope level.

        Returns:
            tuple[str | None, str | None, str | None, str | None, str | None]:
                Tuple of (portfolio, app, branch, build, component) extracted from PRN.
                Components not present in the PRN scope will be None.

        Raises:
            BadRequestException: If PRN is None, has invalid scope, or fails validation.
                Common causes include:
                - PRN is None or empty
                - Invalid scope not in allowed scopes
                - PRN format doesn't match expected pattern for scope
                - Insufficient components for the detected scope

        Examples:
            >>> # Portfolio PRN
            >>> portfolio, app, branch, build, component = cls.validate_prn_scope("prn:web-services")
            >>> print((portfolio, app, branch, build, component))
            >>> # ("web-services", None, None, None, None)

            >>> # App PRN
            >>> portfolio, app, branch, build, component = cls.validate_prn_scope("prn:web-services:api")
            >>> print((portfolio, app, branch, build, component))
            >>> # ("web-services", "api", None, None, None)

            >>> # Build PRN
            >>> portfolio, app, branch, build, component = cls.validate_prn_scope("prn:web-services:api:main:1234")
            >>> print((portfolio, app, branch, build, component))
            >>> # ("web-services", "api", "main", "1234", None)

            >>> # Component PRN
            >>> portfolio, app, branch, build, component = cls.validate_prn_scope("prn:web-services:api:main:1234:lambda")
            >>> print((portfolio, app, branch, build, component))
            >>> # ("web-services", "api", "main", "1234", "lambda")

            >>> # Client PRN (no hierarchy components)
            >>> portfolio, app, branch, build, component = cls.validate_prn_scope("client:acme")
            >>> print((portfolio, app, branch, build, component))
            >>> # (None, None, None, None, None)

            >>> # Invalid PRN raises exception
            >>> try:
            ...     cls.validate_prn_scope("invalid:format")
            ... except BadRequestException as e:
            ...     print(f"Validation failed: {e}")

        Note:
            The validation uses scope-specific validator functions from core_framework.
            Each scope has different requirements:
            - PORTFOLIO: 2 parts (prn:portfolio)
            - APP: 3 parts (prn:portfolio:app)
            - BRANCH: 4 parts (prn:portfolio:app:branch)
            - BUILD: 5 parts (prn:portfolio:app:branch:build)
            - COMPONENT: 6 parts (prn:portfolio:app:branch:build:component)
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
        """Retrieve Facts for a specific deployment context.

        Combines registry data from multiple sources (Client, Portfolio, App, Zone)
        to create a complete Jinja2 context for template rendering. This method
        validates the provided PRN, extracts deployment details, and aggregates
        configuration data from all relevant registry tables.

        Args:
            **kwargs (dict): Request parameters including client and PRN information.
                Expected parameters:
                - client (str, optional): Client identifier. If not provided, will use
                  environment variable or fail with BadRequestException.
                - prn (str): Pipeline Reference Number specifying the deployment scope.
                  Must be valid for portfolio, app, branch, build, or component scope.
                - zone (str, optional): Alternative parameter name for PRN.

        Returns:
            Response: SuccessResponse containing the merged facts data.
                The response.data contains the complete aggregated facts dictionary
                with all configuration data needed for template rendering.
                The response.metadata includes client and prn for reference.

        Raises:
            BadRequestException: If required parameters are missing or invalid.
                Common causes include:
                - PRN is None, empty, or "None" string
                - Client is missing and cannot be determined from environment
                - PRN doesn't contain required portfolio and app components
                - PRN validation fails for the detected scope

        Examples:
            >>> # Get facts for app deployment
            >>> response = FactsActions.get(
            ...     client="acme",
            ...     prn="prn:web-services:api"
            ... )
            >>> facts = response.data
            >>> print(facts["Client"])        # "acme"
            >>> print(facts["Portfolio"])     # "web-services"
            >>> print(facts["App"])          # "api"
            >>> print(facts["AwsAccountId"]) # "738499099231"
            >>> print(facts["Region"])      # "us-west-2"

            >>> # Get facts for specific build
            >>> response = FactsActions.get(
            ...     client="acme",
            ...     prn="prn:web-services:api:main:1234"
            ... )
            >>> build_facts = response.data
            >>> print(build_facts["Build"])   # "1234"
            >>> print(build_facts["Branch"])  # "main"
            >>> print(build_facts["Tags"]["Environment"])  # "production"

            >>> # Get facts for component deployment
            >>> response = FactsActions.get(
            ...     client="enterprise",
            ...     prn="prn:platform:auth:main:567:lambda"
            ... )
            >>> component_facts = response.data
            >>> print(component_facts["Component"])  # "lambda"
            >>> print(component_facts["Kms"]["KmsKeyArn"])  # Full KMS key ARN

            >>> # Using zone parameter instead of prn
            >>> response = FactsActions.get(
            ...     client="acme",
            ...     zone="prn:web-services:api:main:1234"
            ... )

            >>> # Client from environment (if set)
            >>> response = FactsActions.get(
            ...     prn="prn:web-services:api"
            ... )  # Client will be extracted from environment

            >>> # Error handling
            >>> try:
            ...     response = FactsActions.get(prn="invalid:prn:format")
            ... except BadRequestException as e:
            ...     print(f"Facts retrieval failed: {e}")

        Note:
            The facts aggregation process:
            1. Validates PRN format and extracts deployment components
            2. Creates DeploymentDetails object with client and hierarchy info
            3. Calls get_facts() which performs deep merge of registry data:
               - Client facts (global configuration)
               - Portfolio facts (portfolio-specific settings)
               - App facts (application configuration)
               - Zone facts (AWS account and environment config)
            4. Returns aggregated facts suitable for Jinja2 template rendering

            The client parameter can be provided explicitly or will be retrieved
            from the environment using util.get_client(). Both PRN and zone
            parameters are supported for backward compatibility.
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
            raise BadRequestException("Client, portfolio, and app are required in the PRN to retrieve Facts")

        deployment_details = DeploymentDetails(
            Client=client,
            Portfolio=portfolio,
            App=app,
            Branch=branch,
            Build=build,
            Component=component,
        )

        the_facts = get_facts(deployment_details)

        return SuccessResponse(data=the_facts, metadata={"client": client, "prn": prn})
