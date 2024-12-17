from pynamodb.attributes import UnicodeAttribute

from ..models import ItemModel


class AppModel(ItemModel):

    # Attributes
    contact_email = UnicodeAttribute(null=False)

    portfolio_prn = UnicodeAttribute(null=False)

    def __repr__(self):
        return f"<App(prn={self.prn},name={self.name})>"