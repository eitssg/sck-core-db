from pynamodb.attributes import UnicodeAttribute

from ..models import ItemModel

from core_framework.status import (
    INIT,
    DEPLOY_REQUESTED,
    DEPLOY_IN_PROGRESS,
    DEPLOY_COMPLETE,
    DEPLOY_FAILED,
    RELEASE_COMPLETE,
    RELEASE_FAILED,
    RELEASE_REQUESTED,
    RELEASE_IN_PROGRESS,
    TEARDOWN_REQUESTED,
    TEARDOWN_COMPLETE,
    TEARDOWN_FAILED,
    TEARDOWN_IN_PROGRESS,
    COMPILE_COMPLETE,
    COMPILE_FAILED,
    COMPILE_IN_PROGRESS,
    STATUS_LIST,
)


class ComponentStatus:

    def __init__(self, value):
        value = value.upper()
        self.value = value if value in STATUS_LIST else None

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, value) -> "ComponentStatus":
        status = cls(value)
        if status:
            return status
        raise ValueError(f"{value} is not a valid status")

    def is_init(self):
        return self.value == INIT

    def is_deploy(self):
        return self.value in [
            DEPLOY_REQUESTED,
            DEPLOY_IN_PROGRESS,
            DEPLOY_COMPLETE,
            DEPLOY_FAILED,
        ]

    def is_release(self):
        return self.value in [
            RELEASE_REQUESTED,
            RELEASE_IN_PROGRESS,
            RELEASE_COMPLETE,
            RELEASE_FAILED,
        ]

    def is_teardown(self):
        return self.value in [
            TEARDOWN_REQUESTED,
            TEARDOWN_IN_PROGRESS,
            TEARDOWN_COMPLETE,
            TEARDOWN_FAILED,
        ]

    def is_in_progress(self):
        return self.value in [
            RELEASE_REQUESTED,
            TEARDOWN_REQUESTED,
            DEPLOY_REQUESTED,
            COMPILE_IN_PROGRESS,
            DEPLOY_IN_PROGRESS,
            RELEASE_IN_PROGRESS,
            TEARDOWN_IN_PROGRESS,
        ]

    def is_complete(self):
        return self.value in [
            COMPILE_COMPLETE,
            DEPLOY_COMPLETE,
            RELEASE_COMPLETE,
            TEARDOWN_COMPLETE,
        ]

    def is_failed(self):
        return self.value in [
            COMPILE_FAILED,
            DEPLOY_FAILED,
            RELEASE_FAILED,
            TEARDOWN_FAILED,
        ]


class ComponentModel(ItemModel):

    # Attribute status is required
    status = UnicodeAttribute(default_for_new=INIT)

    message = UnicodeAttribute(null=True)
    component_type = UnicodeAttribute(null=True)

    # This may be a VM and we want to record the AMI information.
    image_id = UnicodeAttribute(null=True)
    image_alias = UnicodeAttribute(null=True)

    # PRN References
    portfolio_prn = UnicodeAttribute(null=False)
    app_prn = UnicodeAttribute(null=False)
    branch_prn = UnicodeAttribute(null=False)
    build_prn = UnicodeAttribute(null=False)

    def __repr__(self):
        return f"<Component(prn={self.prn},name={self.name},component_type={self.component_type})>"
