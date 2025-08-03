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

from .models import BranchModelFactory


class BranchActions(ItemTableActions):
    """Class container for Branch Item specific validations and actions"""

    @classmethod
    def get_item_model(cls):
        """
        Get the ItemModel for Branch

        Returns:
            ItemModel: The ItemModel for Branch
        """
        return BranchModelFactory.get_model(util.get_client())

    @classmethod
    def validate_prn(cls, prn: str) -> str:
        """
        Override the class validate_prn method to validate the Branch PRN

        Args:
            prn (str): The branch PRN to validate

        Raises:
            BadRequestException: If the prn is not a branch prn

        Returns:
            str: The PRN provided
        """
        if not util.validate_branch_prn(prn):
            raise BadRequestException(f"Invalid branch_prn: {prn}")
        return prn

    @classmethod
    def create(cls, **kwargs) -> Response:
        """
        Create a Branch Item in the core-automation-items database

        Args:
            **kwargs: The fields required to create a branch
                * prn: The Branch PRN
                * name: The Branch Name
                * short_name: The Branch Short Name
                * branch_prn: The Branch PRN
                * app_prn: The App PRN
                * portfolio_prn: The Portfolio PRN

        Raises:
            BadRequestException: If Data is missing

        Returns:
            Response: Response data with the branch item that was created
        """
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

        Args:
            **kwargs: The fields required to list Items. (ignored for branch lists)
                * app_prn: The App PRN that this branch belongs to

        Returns:
            Response: SuccessResponse with the list of branch items
        """
        app_prn = kwargs.get(APP_PRN, None)
        if not app_prn:
            app_prn = util.extract_app_prn(kwargs)
        if not util.validate_app_prn(app_prn):
            raise BadRequestException(f"Invalid app_prn: {app_prn}")

        return super().list(parent_prn=app_prn, **kwargs)

    @classmethod
    def update(cls, **kwargs) -> Response:
        """
        Update an existing branch item

        Raises:
            BadRequestException: if the release build PRN is not a valid build PRN

        Returns:
            Response: The updated build item
        """
        item_model = cls.get_item_model()
        released_build = item_model.construct_released_build(**kwargs)
        if released_build:
            prn = released_build.get(PRN)
            if not prn or not util.validate_build_prn(prn):
                raise BadRequestException(f"Invalid released_build_prn: {prn}")
        return super().update(**kwargs)
