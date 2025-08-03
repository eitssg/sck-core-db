"""
This module contains the actions list, get, create, delete, update for the Items.Portfolio object in core-automation-items
"""

import core_framework as util
from core_framework.constants import SCOPE_PORTFOLIO

from ...response import Response
from ...exceptions import BadRequestException
from ...constants import PRN, PORTFOLIO_PRN, ITEM_TYPE, CONTACT_EMAIL
from ..actions import ItemTableActions

from .models import PortfolioModelFactory


class PortfolioActions(ItemTableActions):
    """Class container for Portfolio Item specific validations and actions"""

    @classmethod
    def get_item_model(cls):
        """
        Get the ItemModel for Portfolio

        Returns:
            ItemModel: The ItemModel for Portfolio
        """
        return PortfolioModelFactory.get_model(util.get_client())

    @classmethod
    def validate_prn(cls, prn: str) -> str:
        """
        Override the class validate_prn method to validate the Portfolio PRN

        Args:
            prn (str): A portfolio PRN

        Raises:
            BadRequestException: If the prn is not a portfolio prn

        Returns:
            str: the PRN provided
        """
        if not util.validate_portfolio_prn(prn):
            raise BadRequestException(f"Invalid portfolio_prn: {prn}")
        return prn

    @classmethod
    def create(cls, **kwargs) -> Response:
        """
        Create a Portfolio Item

        Args:
            **kwargs: The fields required to create a Portfolio
                * prn: The Portfolio PRN
                * portfolio_prn: The Portfolio PRN
                * name: The Portfolio Name
                * contact_email: The Portfolio Contact Email

        Raises:
            BadRequestException: if contact email is not provided

        Returns:
            Response: Standard Response object
        """

        # Portfolio Fields
        portfolio_prn = kwargs.pop(PRN, kwargs.pop(PORTFOLIO_PRN, None))
        if not portfolio_prn:
            portfolio_prn = util.generate_portfolio_prn(kwargs)
        kwargs[PRN] = cls.validate_prn(portfolio_prn)
        kwargs[ITEM_TYPE] = SCOPE_PORTFOLIO
        if CONTACT_EMAIL not in kwargs:
            raise BadRequestException("Contact email is required for portfolo create")

        return super().create(**kwargs)

    @classmethod
    def list(cls, **kwargs) -> Response:
        """
        List Portfolio Items

        Args:
            **kwargs: The fields required to list Items. (ignored for portfolio lists)

        Returns:
            Response: Response data with the list of portfolio items
        """
        kwargs.pop("parent_prn", None)
        return super().list(parent_prn=PRN, **kwargs)

    @classmethod
    def update(cls, **kwargs) -> Response:
        """
        Update an existing portflio item

        Raises:
            BadRequestException: If the PRN is not present, it's invalid, or the contact_email is mising

        Returns:
            Response: Response data with the record updated
        """

        prn = kwargs.get(PRN, kwargs.get(PORTFOLIO_PRN, None))
        if not prn:
            raise BadRequestException(f"prn not specified: {kwargs}")

        if not util.validate_portfolio_prn(prn):
            raise BadRequestException(f"Invalid prn: {prn}")

        contact_email = kwargs.get("contact_email")
        if not contact_email:
            raise BadRequestException("Contact email is required")

        return super().update(**kwargs)
