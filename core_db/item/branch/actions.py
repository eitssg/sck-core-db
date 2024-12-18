"""
This module contains the actions list, get, create, delete, update for the Items.Branch object in core-automation-items
"""
import core_framework as util

from ...constants import (
    PRN,
    APP_PRN,
    BRANCH_PRN,
    PORTFOLIO_PRN,
    ITEM_TYPE,
    NAME,
    SHORT_NAME,
)

from ...response import Response
from ...exceptions import BadRequestException

from ..actions import ItemTableActions

from .models import BranchModel


class BranchActions(ItemTableActions):
    """ Class container for Branch Item specific validations and actions"""

    item_model = BranchModel

    @classmethod
    def validate_prn(cls, prn: str) -> str:
        if not util.validate_branch_prn(prn):
            raise BadRequestException(f"Invalid branch_prn: {prn}")
        return prn

    @classmethod
    def create(cls, **kwargs) -> Response:

        # Branch Fields
        branch_prn = kwargs.pop(PRN, kwargs.pop(BRANCH_PRN, None))
        if not branch_prn:
            branch_prn = util.generate_branch_prn(kwargs)
        kwargs[PRN] = cls.validate_prn(branch_prn)
        kwargs[ITEM_TYPE] = util.constants.SCOPE_BRANCH

        # Get the branch name, it's required
        if NAME not in kwargs:
            raise BadRequestException(f"Branch name is required: {kwargs}")

        # Get the short name and generate it if it doesn't exist
        if SHORT_NAME not in kwargs:
            kwargs[SHORT_NAME] = util.branch_short_name(kwargs.get(NAME, None))

        # App PRN reference
        app_prn = kwargs.get(APP_PRN, None)
        if not app_prn:
            app_prn = util.extract_app_prn(kwargs)
        if not util.validate_app_prn(app_prn):
            raise BadRequestException(f"Invalid app_prn: {app_prn}")
        kwargs[APP_PRN] = app_prn

        # Portfolio PRN Reference
        portfolio_prn = kwargs.get(PORTFOLIO_PRN, None)
        if not portfolio_prn:
            portfolio_prn = util.extract_portfolio_prn(kwargs)
        if not util.validate_portfolio_prn(portfolio_prn):
            raise BadRequestException(f"Invalid portfolio_prn: {portfolio_prn}")
        kwargs[PORTFOLIO_PRN] = portfolio_prn

        return super().create(**kwargs)

    @classmethod
    def list(cls, **kwargs) -> Response:
        """
        Return a list of branches by specifying the app_prn in the query parameters

        Returns:
            Response: SuccessResponse
        """
        app_prn = kwargs.get(APP_PRN, None)
        if not app_prn:
            app_prn = util.extract_app_prn(kwargs)
        if not util.validate_app_prn(app_prn):
            raise BadRequestException(f"Invalid app_prn: {app_prn}")

        return super().list(parent_prn=app_prn, **kwargs)

    @classmethod
    def update(cls, **kwargs) -> Response:
        released_build = BranchModel.construct_released_build(**kwargs)
        if released_build:
            prn = released_build.get(PRN)
            if not prn or not util.validate_build_prn(prn):
                raise BadRequestException(f"Invalid released_build_prn: {prn}")
        return super().update(**kwargs)
