""" This module provides the field extensions for Items.Portfolios in the core-automation-items table """

from pynamodb.attributes import UnicodeAttribute
from ..models import ItemModel


class PortfolioModel(ItemModel):
    """
    Portfolio model field extensions

    """

    class Meta:
        """
        :no-index:
        """
        pass

    contact_email = UnicodeAttribute(null=False)
    """str: Contact email for the portfolio. Example: """

    def __repr__(self):
        return f"<Portfolio(prn={self.prn},name={self.name})>"
