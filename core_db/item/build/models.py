from pynamodb.attributes import UnicodeAttribute

from core_framework.status import INIT

from ..models import ItemModel


class BuildModel(ItemModel):

    # Attribute status is required
    status = UnicodeAttribute(default_for_new=INIT)

    message = UnicodeAttribute(null=True)
    context = UnicodeAttribute(null=True)

    # Computed fields
    portfolio_prn = UnicodeAttribute(null=False)
    app_prn = UnicodeAttribute(null=False)
    branch_prn = UnicodeAttribute(null=False)

    def __repr__(self):
        return f"<Build(prn={self.prn},name={self.name},status={self.status})>"
