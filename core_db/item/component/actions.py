""" This module contains the actions list, get, create, delete, update for the Items.Component object in core-automation-items """

import core_framework as util

from ...exceptions import BadRequestException
from ...response import Response
from ...constants import (
    PRN,
    APP_PRN,
    BRANCH_PRN,
    BUILD_PRN,
    PORTFOLIO_PRN,
    COMPONENT_PRN,
    ITEM_TYPE,
)

from ..actions import ItemTableActions

from .models import ComponentModel


class ComponentActions(ItemTableActions):
    """Class container for Component Item specific validations and actions"""

    item_model = ComponentModel

    @classmethod
    def validate_prn(cls, prn: str) -> str:
        if not util.validate_component_prn(prn):
            raise BadRequestException(f"Invalid component_prn: {prn}")
        return prn

    @classmethod
    def create(cls, **kwargs) -> Response:

        # Component Fields
        component_prn = kwargs.pop(PRN, kwargs.pop(COMPONENT_PRN, None))
        if not component_prn:
            component_prn = util.generate_component_prn(kwargs)

        kwargs[PRN] = cls.validate_prn(component_prn)
        kwargs[ITEM_TYPE] = util.constants.SCOPE_COMPONENT

        # Build PRN Reference
        build_prn = kwargs.get(BUILD_PRN, None)
        if not build_prn:
            build_prn = util.extract_build_prn(kwargs)
        if not util.validate_build_prn(build_prn):
            raise BadRequestException(f"Invalid build_prn: {build_prn}")
        kwargs[BUILD_PRN] = build_prn

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
        component_prn = kwargs.get(PRN, kwargs.get(COMPONENT_PRN, None))
        if not component_prn:
            raise BadRequestException("Component PRN is required to update a component")

        return super().update(**kwargs)

    @classmethod
    def list(cls, **kwargs):
        build_prn = kwargs.get(BUILD_PRN, None)
        if not build_prn:
            build_prn = util.extract_build_prn(kwargs)

        return super().list(parent_prn=build_prn, **kwargs)
