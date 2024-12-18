""" Defines the get method for the Facts table view. """
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

from ..constants import PRN
from ..actions import TableActions

from ..response import Response, SuccessResponse
from ..exceptions import BadRequestException

from .facter import get_facts


class FactsActions(TableActions):
    """
    This is a VIEW model on the registry combining the following 4 tables into a "context" for Jinja2 rendering.

    1. Load Registry Client Facts
    2. Load Registry Portfolip Facts
    3. Load Registry App Facts
    4. Load Registry Zone Facts

    Combine them with a deep merge and present as the Jinja2 Context (a.k.a. Facts)

    """

    @classmethod
    def validate_prn_scope(
        cls, prn: str | None
    ) -> tuple[str | None, str | None, str | None, str | None, str | None]:
        # Validation mapping
        validators = {
            SCOPE_PORTFOLIO: (util.validate_portfolio_prn, 2),
            SCOPE_APP: (util.validate_app_prn, 3),
            SCOPE_BRANCH: (util.validate_branch_prn, 4),
            SCOPE_BUILD: (util.validate_build_prn, 5),
            SCOPE_COMPONENT: (util.validate_component_prn, 6),
        }

        if prn is None:
            raise BadRequestException("PRN must be provided to the facts API")

        scope = util.prn_utils.get_prn_scope(prn)
        parts = prn.split(":")

        # Default values
        portfolio = app = branch = build = component = None

        if scope == SCOPE_CLIENT:
            return portfolio, app, branch, build, component

        if scope not in validators:
            raise BadRequestException(f"Invalid scope: {scope}")

        validator_func, num_parts = validators[scope]

        if not validator_func(prn):
            raise BadRequestException(f"Invalid PRN: {prn}. Not a valid {scope} PRN.")

        # Unpack only the parts we need based on scope
        values = parts[1:num_parts] + [None] * (5 - len(parts[1:num_parts]))
        portfolio, app, branch, build, component = values

        return portfolio, app, branch, build, component

    @classmethod
    def get(cls, **kwargs: dict) -> Response:

        # The client information can come from the query string or the environment variables
        # client must come from pathParameters
        client = str(kwargs.pop(SCOPE_CLIENT, os.environ.get(SCOPE_CLIENT, "")))

        # based on the scope, is the PRN valid?  The PRN must be specified in the query parameters
        prn = str(kwargs.pop(PRN, kwargs.pop(SCOPE_ZONE, None)))
        portfolio, app, branch, build, component = cls.validate_prn_scope(prn)

        if not client or not portfolio or not app:
            raise BadRequestException(
                "Client, portfolio, and app are required in the PRN to retreive Facts"
            )

        the_facts = get_facts(client, portfolio, app, branch, build, component)

        return SuccessResponse(the_facts)
