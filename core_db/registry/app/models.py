"""Classes defining the Apps record model for the core-automation-apps table"""

from pynamodb.attributes import MapAttribute, UnicodeAttribute

import core_logging as log

from ...constants import CLIENT_PORTFOLIO_KEY, APP_KEY
from ...config import get_table_name, APP_FACTS
from ..models import RegistryModel


class AppFacts(RegistryModel):
    """
    Protocol defining the Apps record model interface for the core-automation-apps table.

    This protocol defines the structure for app facts models that can be created
    dynamically for different clients using the AppFactsFactory.

    Attributes
    ----------
    ClientPortfolio : UnicodeAttribute
        Client Portfolio identifier (alternate key "client-portfolio")
    AppRegex : UnicodeAttribute
        App Regex identifier (alternate key "app-regex")
    Name : UnicodeAttribute
        Name of the app (alternate key "name")
    Environment : UnicodeAttribute
        Environment of the app (alternate key "environment")
    Account : UnicodeAttribute
        Account of the app (alternate key "account")
    Zone : UnicodeAttribute
        Zone of the app (alternate key "zone")
    ImageAliases : MapAttribute
        Image Aliases of the app to reduce bake time (alternate key "image-aliases")
    Repository : UnicodeAttribute
        Git repository of the app (alternate key "repository")
    Region : UnicodeAttribute
        Region of the app (alternate key "region")
    Tags : MapAttribute
        Tags of the app (alternate key "tags")
    EnforceValidation : UnicodeAttribute
        Enforce validation of the app (alternate key "enforce-validation")
    Metadata : MapAttribute
        Metadata of the app (alternate key "metadata")

    Notes
    -----
    We call this "zone" now. A "zone" contains "apps" that are deployed together
    in an Account. A zone can have multiple region definitions.
    """

    class Meta(RegistryModel.Meta):
        pass

    ClientPortfolio = UnicodeAttribute(attr_name=CLIENT_PORTFOLIO_KEY, hash_key=True)
    AppRegex = UnicodeAttribute(attr_name=APP_KEY, range_key=True)
    Name = UnicodeAttribute(null=True)
    Environment = UnicodeAttribute(null=True)
    Account = UnicodeAttribute(null=True)
    Zone = UnicodeAttribute(null=False)
    ImageAliases = MapAttribute(null=True)
    Repository = UnicodeAttribute(null=True)
    Region = UnicodeAttribute(null=False)
    Tags = MapAttribute(null=True)
    EnforceValidation = UnicodeAttribute(null=True)
    Metadata = MapAttribute(null=True)
    UserInstantiated = UnicodeAttribute(null=True)


AppFactsType = type[AppFacts]


class AppFactsFactory:
    """Factory to create client-specific AppFacts models with dynamic table names."""

    _model_cache = {}

    @classmethod
    def get_model(cls, client: str, auto_create_table: bool = True) -> AppFactsType:
        """
        Get an AppFacts model class for a specific client.

        :param client: The client name for table name generation
        :type client: str
        :param auto_create_table: Whether to auto-create the table if it doesn't exist
        :type auto_create_table: bool
        :returns: An AppFacts model class configured for the specified client
        :rtype: type[AppFacts]
        """
        if client not in cls._model_cache:
            model_class = cls._create_client_model(client)
            cls._model_cache[client] = model_class

            # Auto-create table if requested
            if auto_create_table:
                cls._ensure_table_exists(model_class)

        return cls._model_cache[client]

    @classmethod
    def _ensure_table_exists(cls, model_class: AppFacts) -> None:
        """
        Ensure the table exists, create it if it doesn't.

        :param model_class: The model class to check/create table for
        :type model_class: type
        :param client: The client name for logging
        :type client: str
        """
        try:
            if not model_class.exists():
                log.info("Creating app table: %s", model_class.Meta.table_name)
                model_class.create_table(wait=True)
                log.info("Successfully created app table: %s", model_class.Meta.table_name)
        except Exception as e:
            log.error("Failed to create app table %s: %s", model_class.Meta.table_name, str(e))
            # Don't raise - let the operation proceed and fail naturally

    @classmethod
    def _create_client_model(cls, client: str) -> AppFactsType:
        """
        Create a new AppFacts model class for a specific client.

        :param client: The client name for table configuration
        :type client: str
        :returns: Dynamic AppFacts model class
        :rtype: type
        """

        class AppFactsModel(AppFacts):
            class Meta(AppFacts.Meta):
                table_name = get_table_name(APP_FACTS, client)

        return AppFactsModel
