"""
This module contains the actions list, get, create, delete, update for the Items.App object in core-automation-items
"""

import core_framework as util

from ...constants import (
    PRN,
    APP_PRN,
    PORTFOLIO_PRN,
    CONTACT_EMAIL,
    ITEM_TYPE,
    NAME,
)

from ...response import Response
from ...exceptions import BadRequestException
from ..actions import ItemTableActions
from .models import AppModel


class AppActions(ItemTableActions):
    """Class container for App Item specific validations and actions"""

    item_model = AppModel
    """ItemModel: The :class:`core_db.item.models.ItemModel` class for the ``AppActions`` to work on.  Set to :class:`core_db.item.app.models.AppModel` """

    @classmethod
    def validate_prn(cls, prn: str) -> str:
        if not util.validate_app_prn(prn):
            raise BadRequestException(f"Invalid app_prn: {prn}")
        return prn

    @classmethod
    def create(cls, **kwargs) -> Response:
        """
        Create a App Item in the core-automation-items database

        Args:
            **kwargs: The fields required to create an app
                * prn: The App PRN
                * app_prn: The App PRN
                * name: The App Name
                * contact_email: The App Contact Email
                * portfolio_prn: The Portfolio PRN

        Raises:
            BadRequestException: If field values are missing

        Returns:
            Response: Response data with the app item that was created
        """
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
            raise BadRequestException("contact_email is required to create an app")

        return super().create(**kwargs)

    @classmethod
    def list(cls, **kwargs) -> Response:
        """
        Return a list of apps by specifying the portfolio_prn in the query parameters

        Args:
            **kwargs: The fields required to list Items. (ignored for app lists)
                * portfolio_prn: The Portfolio PRN taht this app belongs to

        Returns:
            Response: SuccessResponse or FaiureResponse
        """
        portfolio_prn = kwargs.get(PORTFOLIO_PRN, None)
        if not portfolio_prn:
            portfolio_prn = util.extract_portfolio_prn(kwargs)
        if not util.validate_portfolio_prn(portfolio_prn):
            raise BadRequestException(f"Invalid portfolio prn: {portfolio_prn}")

        return super().list(parent_prn=portfolio_prn, **kwargs)
