""" This module contains the actions list, get, create, delete, update for the Items.Build object in core-automation-items """
import core_framework as util

from core_framework.status import BuildStatus, INIT

from ...constants import (
    APP_PRN,
    BRANCH_PRN,
    BUILD_PRN,
    PORTFOLIO_PRN,
    PRN,
    ITEM_TYPE,
    STATUS,
)

from ...response import Response
from ...exceptions import BadRequestException

from ..actions import ItemTableActions

from .models import BuildModel


class BuildActions(ItemTableActions):
    """ Class container for Build Item specific validations and actions"""

    item_model = BuildModel

    @classmethod
    def validate_prn(cls, prn: str) -> str:
        if not util.validate_build_prn(prn):
            raise BadRequestException(f"Invalid build_prn: {prn}")
        return prn

    @classmethod
    def create(cls, **kwargs) -> Response:

        # Build Fields
        build_prn = kwargs.pop(PRN, kwargs.pop(BUILD_PRN, None))
        if not build_prn:
            build_prn = util.generate_build_prn(kwargs)
        kwargs[PRN] = cls.validate_prn(build_prn)
        kwargs[ITEM_TYPE] = util.constants.SCOPE_BUILD

        # Build Status is incredibly important
        try:
            build_status = BuildStatus.from_str(kwargs.get(STATUS, INIT))
            kwargs[STATUS] = str(build_status)
        except ValueError as e:
            print(e)
            raise BadRequestException(f"Invalid status: {build_status}")

        # Branch PRN reference
        branch_prn = kwargs.get(BRANCH_PRN, None)
        if not branch_prn:
            branch_prn = util.extract_branch_prn(kwargs)
        if not util.validate_branch_prn(branch_prn):
            raise BadRequestException(f"Invalid branch_prn: {branch_prn}")
        kwargs[BRANCH_PRN] = branch_prn

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
    def update(cls, **kwargs) -> Response:

        build_prn = kwargs.get(PRN, kwargs.get(BUILD_PRN, None))
        if not util.validate_build_prn(build_prn):
            raise BadRequestException(f"Invalid build_prn provided: {build_prn}")

        return super().update(**kwargs)

    @classmethod
    def list(cls, **kwargs) -> Response:
        branch_prn = kwargs.get(BRANCH_PRN, None)
        if not branch_prn:
            branch_prn = util.extract_branch_prn(kwargs)

        return super().list(parent_prn=branch_prn, **kwargs)
