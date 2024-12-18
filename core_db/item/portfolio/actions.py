"""
This module contains the actions list, get, create, delete, update for the Items.Portfolio object in core-automation-items
"""

import core_framework as util

from ...response import Response
from ...exceptions import BadRequestException
from ...constants import PRN, PORTFOLIO_PRN, ITEM_TYPE, CONTACT_EMAIL
from ..actions import ItemTableActions

from .models import PortfolioModel


class PortfolioActions(ItemTableActions):
    """ Class container for Portfolio Item specific validations and actions """

    item_model = PortfolioModel

    @classmethod
    def validate_prn(cls, prn: str) -> str:
        if not util.validate_portfolio_prn(prn):
            raise BadRequestException(f"Invalid portfolio_prn: {prn}")
        return prn

    @classmethod
    def create(cls, **kwargs) -> Response:

        # Portfolio Fields
        portfolio_prn = kwargs.pop(PRN, kwargs.pop(PORTFOLIO_PRN, None))
        if not portfolio_prn:
            portfolio_prn = util.generate_portfolio_prn(kwargs)
        kwargs[PRN] = cls.validate_prn(portfolio_prn)
        kwargs[ITEM_TYPE] = util.constants.SCOPE_PORTFOLIO
        if CONTACT_EMAIL not in kwargs:
            raise BadRequestException("Contact email is required for portfolo create")

        return super().create(**kwargs)

    @classmethod
    def list(cls, **kwargs) -> Response:
        return super().list(parent_prn=PRN, **kwargs)

    @classmethod
    def update(cls, **kwargs) -> Response:
        prn = kwargs.get(PRN, kwargs.get(PORTFOLIO_PRN, None))
        if not prn:
            raise BadRequestException(f"prn not specified: {kwargs}")

        if not util.validate_portfolio_prn(prn):
            raise BadRequestException(f"Invalid prn: {prn}")

        contact_email = kwargs.get("contact_email")
        if not contact_email:
            raise BadRequestException("Contact email is required")

        return super().update(**kwargs)
