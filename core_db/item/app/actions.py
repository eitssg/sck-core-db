"""
This module contains the schemas for the core API for the APP Actions.
"""

import core_framework as util
import core_framework.constants

from ...constants import (
    PRN,
    APP_PRN,
    PORTFOLIO_PRN,
    CONTACT_EMAIL,
    ITEM_TYPE,
    NAME,
)

from ...response import Response
from ...exceptions import BadRequestException, ConflictException
from ..actions import ItemTableActions
from .models import AppModel


class AppActions(ItemTableActions):

    item_model = AppModel

    @classmethod
    def validate_prn(cls, prn: str) -> str:
        if not util.validate_app_prn(prn):
            raise BadRequestException(f"Invalid app_prn: {prn}")
        return prn

    @classmethod
    def create(cls, **kwargs) -> Response:

        # Application PRN
        app_prn = kwargs.pop(PRN, kwargs.pop(APP_PRN, None))
        if not app_prn:
            app_prn = util.generate_app_prn(kwargs)

        kwargs[PRN] = cls.validate_prn(app_prn)
        kwargs[ITEM_TYPE] = util.constants.SCOPE_APP

        if NAME not in kwargs:
            raise BadRequestException("The field 'name' is required to create an app")

        # Portfolio PRN reference
        portfolio_prn = kwargs.get(PORTFOLIO_PRN)
        if not portfolio_prn:
            portfolio_prn = util.generate_portfolio_prn(kwargs)
        if not util.validate_portfolio_prn(portfolio_prn):
            raise BadRequestException(f"Invalid portfolio_prn: {portfolio_prn}")
        kwargs[PORTFOLIO_PRN] = portfolio_prn

        if CONTACT_EMAIL not in kwargs:
            raise ConflictException("contact_email is required to create an app")

        return super().create(**kwargs)

    @classmethod
    def list(cls, **kwargs) -> Response:
        """
        Return a list of apps by specifying the portfolio_prn in the query parameters

        Returns:
            Response: SuccessResponse or FaiureResponse
        """
        portfolio_prn = kwargs.get(PORTFOLIO_PRN, None)
        if not portfolio_prn:
            portfolio_prn = util.extract_portfolio_prn(kwargs)
        if not util.validate_portfolio_prn(portfolio_prn):
            raise BadRequestException(f"Invalid portfolio prn: {portfolio_prn}")

        return super().list(parent_prn=portfolio_prn, **kwargs)
