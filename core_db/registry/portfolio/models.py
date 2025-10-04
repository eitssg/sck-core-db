"""Definition of the Portfolio Facts in the core-automation-portfolios table"""

from typing import Any, Dict, Optional, List, Type
from pydantic import Field, ConfigDict, BaseModel
from pynamodb.attributes import (
    UnicodeAttribute,
    BooleanAttribute,
    NumberAttribute,
    MapAttribute,
    ListAttribute,
)

from ...constants import PORTFOLIO_KEY
from ...models import TableFactory, DatabaseRecord, DatabaseTable, EnhancedMapAttribute


class ContactFacts(EnhancedMapAttribute):

    name = UnicodeAttribute(attr_name="Name")
    email = UnicodeAttribute(null=True, attr_name="Email")
    attributes = MapAttribute(null=True, attr_name="Attributes")
    enabled = BooleanAttribute(default=True, attr_name="Enabled")


class ApproverFacts(EnhancedMapAttribute):

    sequence = NumberAttribute(default=1, attr_name="Sequence")
    name = UnicodeAttribute(attr_name="Name")
    email = UnicodeAttribute(null=True, attr_name="Email")
    roles = ListAttribute(of=UnicodeAttribute, null=True, attr_name="Roles")
    attributes = MapAttribute(of=UnicodeAttribute, null=True, attr_name="Attributes")
    depends_on = ListAttribute(of=NumberAttribute, null=True, attr_name="DependsOn")
    enabled = BooleanAttribute(default=True, attr_name="Enabled")


class OwnerFacts(EnhancedMapAttribute):

    name = UnicodeAttribute(attr_name="Name")
    email = UnicodeAttribute(null=True, attr_name="Email")
    phone = UnicodeAttribute(null=True, attr_name="Phone")
    attributes = MapAttribute(of=UnicodeAttribute, null=True, attr_name="Attributes")


class ProjectFacts(EnhancedMapAttribute):

    name = UnicodeAttribute(attr_name="Name")
    code = UnicodeAttribute(attr_name="Code")
    repository = UnicodeAttribute(null=True, attr_name="Repository")
    description = UnicodeAttribute(null=True, attr_name="Description")
    attributes = MapAttribute(of=UnicodeAttribute, null=True, attr_name="Attributes")


class LinkFacts(EnhancedMapAttribute):

    title = UnicodeAttribute(attr_name="Title")
    url = UnicodeAttribute(attr_name="Url")
    kind = UnicodeAttribute(null=True, attr_name="Kind")
    attributes = MapAttribute(of=UnicodeAttribute, null=True, attr_name="Attributes")


class PortfolioFactsModel(DatabaseTable):

    class Meta(DatabaseTable.Meta):

        pass

    # Composite primary key
    portfolio = UnicodeAttribute(hash_key=True, attr_name=PORTFOLIO_KEY)

    name = UnicodeAttribute(null=True, attr_name="Name")

    # Portfolio configuration
    contacts = ListAttribute(of=ContactFacts, null=True, attr_name="Contacts")
    approvers = ListAttribute(of=ApproverFacts, null=True, attr_name="Approvers")
    project = ProjectFacts(null=True, attr_name="Project")
    domain = UnicodeAttribute(null=True, attr_name="Domain")
    bizapp = ProjectFacts(null=True, attr_name="Bizapp")
    owner = OwnerFacts(null=True, attr_name="Owner")

    # Extended identity/presentation
    icon_url = UnicodeAttribute(null=True, attr_name="IconUrl")
    category = UnicodeAttribute(null=True, attr_name="Category")
    labels = ListAttribute(of=UnicodeAttribute, null=True, attr_name="Labels")
    portfolio_version = UnicodeAttribute(null=True, attr_name="PortfolioVersion")
    lifecycle_status = UnicodeAttribute(null=True, attr_name="LifecycleStatus")

    # Extended ownership
    business_owner = OwnerFacts(null=True, attr_name="BusinessOwner")
    technical_owner = OwnerFacts(null=True, attr_name="TechnicalOwner")

    # Metadata and attributes
    tags = MapAttribute(of=UnicodeAttribute, null=True, attr_name="Tags")
    metadata = MapAttribute(of=UnicodeAttribute, null=True, attr_name="Metadata")
    attributes = MapAttribute(of=UnicodeAttribute, null=True, attr_name="Attributes")
    compliance = MapAttribute(of=UnicodeAttribute, null=True, attr_name="Compliance")
    identifiers = MapAttribute(of=UnicodeAttribute, null=True, attr_name="Identifiers")

    # Ops and integration
    links = ListAttribute(of=LinkFacts, null=True, attr_name="Links")
    dependencies = ListAttribute(of=UnicodeAttribute, null=True, attr_name="Dependencies")

    app_count = NumberAttribute(default=0, attr_name="AppCount")

    def __repr__(self) -> str:
        return f"<PortfolioFactsModel(portfolio={self.portfolio})>"


PortfolioFactsType = Type[PortfolioFactsModel]


class PortfolioFactsFactory:

    @classmethod
    def get_model(cls, client_name: str) -> PortfolioFactsType:
        return TableFactory.get_model(PortfolioFactsModel, client=client_name)

    @classmethod
    def create_table(cls, client_name: str, wait: bool = True) -> bool:
        return TableFactory.create_table(PortfolioFactsModel, client_name, wait=wait)

    @classmethod
    def delete_table(cls, client_name: str, wait: bool = True) -> bool:
        return TableFactory.delete_table(PortfolioFactsModel, client_name, wait=wait)

    @classmethod
    def exists(cls, client_name: str) -> bool:
        return TableFactory.exists(PortfolioFactsModel, client_name)


# =============================================================================
# Pydantic MapAttribute Models
# =============================================================================


class ContactFactsItem(BaseModel):

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    name: str = Field(
        ...,
        alias="Name",
        description="Name of the contact",
    )
    email: Optional[str] = Field(
        default=None,
        alias="Email",
        description="Email address of the contact",
    )
    attributes: Optional[Dict[str, str]] = Field(
        default=None,
        alias="Attributes",
        description="Additional attributes for the contact",
    )
    enabled: bool = Field(
        default=True,
        alias="Enabled",
        description="Is the contact enabled",
    )


class ApproverFactsItem(BaseModel):

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    sequence: int = Field(
        1,
        alias="Sequence",
        description="Sequence number of the approver",
    )
    name: str = Field(
        ...,
        alias="Name",
        description="Name of the approver",
    )
    email: Optional[str] = Field(
        default=None,
        alias="Email",
        description="Email address of the approver",
    )
    roles: Optional[List[str]] = Field(
        default=None,
        alias="Roles",
        description="List of roles for the approver",
    )
    attributes: Optional[Dict[str, str]] = Field(
        default=None,
        alias="Attributes",
        description="Additional attributes for the approver",
    )
    depends_on: Optional[List[int]] = Field(
        default=None,
        alias="DependsOn",
        description="List of sequence numbers of approvers that this approver depends on",
    )
    enabled: bool = Field(
        default=True,
        alias="Enabled",
        description="Is the approver enabled",
    )


class OwnerFactsItem(BaseModel):

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    name: str = Field(
        ...,
        alias="Name",
        description="Name of the owner",
    )
    email: Optional[str] = Field(
        default=None,
        alias="Email",
        description="Email address of the owner",
    )
    phone: Optional[str] = Field(
        default=None,
        alias="Phone",
        description="Phone number of the owner",
    )
    attributes: Optional[Dict[str, str]] = Field(
        default=None,
        alias="Attributes",
        description="Additional attributes for the owner",
    )


class ProjectFactsItem(BaseModel):

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    name: str = Field(
        ...,
        alias="Name",
        description="Name of the project",
    )
    code: str = Field(
        ...,
        alias="Code",
        description="Code of the project",
    )
    repository: Optional[str] = Field(
        default=None,
        alias="Repository",
        description="Git repository of the project",
    )
    description: Optional[str] = Field(
        default=None,
        alias="Description",
        description="Description of the project",
    )
    attributes: Optional[Dict[str, str]] = Field(
        default=None,
        alias="Attributes",
        description="Additional attributes for the project",
    )


class LinkFactsItem(BaseModel):

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    title: str = Field(
        ...,
        alias="Title",
        description="Display title for the link",
    )
    url: str = Field(
        ...,
        alias="Url",
        description="Destination URL",
    )
    kind: Optional[str] = Field(
        default=None,
        alias="Kind",
        description="Type classification (runbook, dashboard, docs)",
    )
    attributes: Optional[Dict[str, str]] = Field(
        default=None,
        alias="Attributes",
        description="Free-form attributes for the link",
    )


# =============================================================================
# Main Pydantic Model
# =============================================================================


class PortfolioFact(DatabaseRecord):

    portfolio: str = Field(
        ...,
        alias="Portfolio",
        description="Portfolio identifier (unique portfolio name within client namespace)",
    )
    name: Optional[str] = Field(
        default=None,
        alias="Name",
        description="Optional descriptive name for the portfolio",
    )

    # Portfolio Configuration Fields
    contacts: Optional[List[ContactFactsItem]] = Field(
        default=None,
        alias="Contacts",
        description="List of contact details for the portfolio",
    )
    approvers: Optional[List[ApproverFactsItem]] = Field(
        default=None,
        alias="Approvers",
        description="List of approver details for approval workflows",
    )
    project: Optional[ProjectFactsItem] = Field(
        default=None,
        alias="Project",
        description="Primary project details for the portfolio",
    )
    domain: Optional[str] = Field(
        default=None,
        alias="Domain",
        description="Domain name or identifier for the portfolio",
    )
    bizapp: Optional[ProjectFactsItem] = Field(
        default=None,
        alias="Bizapp",
        description="Business application details, alternative to project",
    )
    owner: Optional[OwnerFactsItem] = Field(
        default=None,
        alias="Owner",
        description="Owner details for the portfolio",
    )

    # Extended identity/presentation
    icon_url: Optional[str] = Field(
        default=None,
        alias="IconUrl",
        description="URL to portfolio icon (SVG/PNG)",
    )
    category: Optional[str] = Field(
        default=None,
        alias="Category",
        description="Portfolio category (Platform, Internal, etc.)",
    )
    labels: Optional[List[str]] = Field(
        default=None,
        alias="Labels",
        description="Free-form labels for faceting",
    )
    portfolio_version: Optional[str] = Field(
        default=None,
        alias="PortfolioVersion",
        description="Version tag for the portfolio",
    )
    lifecycle_status: Optional[str] = Field(
        default=None,
        alias="LifecycleStatus",
        description="Lifecycle status (Active, Sunset, etc.)",
    )

    # Extended ownership
    business_owner: Optional[OwnerFactsItem] = Field(
        default=None,
        alias="BusinessOwner",
        description="Business owner details",
    )
    technical_owner: Optional[OwnerFactsItem] = Field(
        default=None,
        alias="TechnicalOwner",
        description="Technical owner details",
    )

    # Metadata Fields
    tags: Optional[Dict[str, str]] = Field(
        default=None,
        alias="Tags",
        description="Tags for deployment resources",
    )
    metadata: Optional[Dict[str, str]] = Field(
        default=None,
        alias="Metadata",
        description="Additional metadata for the portfolio",
    )
    attributes: Optional[Dict[str, str]] = Field(
        default=None,
        alias="Attributes",
        description="Custom attributes for the portfolio",
    )
    compliance: Optional[Dict[str, Any]] = Field(
        default=None,
        alias="Compliance",
        description="Compliance flags/levels for the portfolio",
    )
    identifiers: Optional[Dict[str, Any]] = Field(
        default=None,
        alias="Identifiers",
        description="External identifiers (Jira, CMDB, etc.)",
    )
    links: Optional[List[LinkFactsItem]] = Field(
        default=None,
        alias="Links",
        description="External links: runbooks, dashboards, docs",
    )
    dependencies: Optional[List[str]] = Field(
        default=None,
        alias="Dependencies",
        description="Other portfolios this one depends on",
    )
    app_count: int = Field(
        default=0,
        alias="AppCount",
        description="Number of applications in this portfolio",
    )

    @classmethod
    def from_model(cls, model: PortfolioFactsModel) -> "PortfolioFact":
        return cls(**model.to_simple_dict())

    @classmethod
    def model_class(cls, client: str) -> PortfolioFactsType:
        return PortfolioFactsFactory.get_model(client)

    def to_model(self, client: str) -> PortfolioFactsModel:
        model_class = PortfolioFactsFactory.get_model(client)
        return model_class(**self.model_dump(by_alias=False, exclude_none=True))

    def __repr__(self) -> str:
        return f"<PortfolioFact(portfolio={self.portfolio})>"
