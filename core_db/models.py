"""Base models and utilities for PynamoDB table definitions and Pydantic serialization.

This module provides the foundational classes and utilities for database table models,
including enhanced initialization, audit field management, client-specific table factories,
and custom attribute types for complex data structures.

Key Components:
    - **DatabaseTable**: Base PynamoDB model with audit fields and enhanced initialization
    - **DatabaseRecord**: Base Pydantic model for API serialization
    - **TableFactory**: Thread-safe factory for client-specific table creation
    - **DictAttribute**: Custom attribute for dictionary storage in DynamoDB
    - **EnhancedMapAttribute**: MapAttribute with enhanced initialization support

Features:
    - **Dual Naming Support**: Both snake_case (Python) and PascalCase (DynamoDB) field names
    - **Automatic Timestamps**: Created/updated timestamps with automatic management
    - **Client Isolation**: Dynamic table naming and creation per client
    - **Type Safety**: Full type hints and validation support
    - **Thread Safety**: Safe for concurrent access and model creation

Examples:
    >>> # Create a basic table model
    >>> class ItemModel(DatabaseTable):
    ...     class Meta:
    ...         table_name = "items"
    ...
    ...     item_id = UnicodeAttribute(hash_key=True, attr_name="ItemId")
    ...     name = UnicodeAttribute(attr_name="Name")

    >>> # Client-specific model creation
    >>> acme_model = TableFactory.get_model(ItemModel, "acme")
    >>> acme_item = acme_model(item_id="123", name="Test Item")

    >>> # Pydantic record for API responses
    >>> class ItemRecord(DatabaseRecord):
    ...     item_id: str = Field(..., alias="ItemId")
    ...     name: str = Field(..., alias="Name")
"""

# Standard library imports
import inspect
import threading
from abc import ABC
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union
import base64
from dateutil import parser
import json

# Third-party imports
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from pynamodb.attributes import (
    DESERIALIZE_CLASS_MAP,
    Attribute,
    BinaryAttribute,
    BinarySetAttribute,
    BooleanAttribute,
    ListAttribute,
    MapAttribute,
    NullAttribute,
    NumberAttribute,
    NumberSetAttribute,
    UnicodeAttribute,
    UnicodeSetAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.constants import MAP, NULL
from pynamodb.exceptions import AttributeNullError
from pynamodb.models import Model

import core_framework as util

# Local imports
from .config import get_dynamodb_host, get_region, get_table_name

# Type variables
_T = TypeVar("_T")
T = TypeVar("T", bound=Model)


def _get_class_for_serialize(value):
    """Return the class needed to serialize the given value.

    Copied from PynamoDB's private function. Determines the appropriate
    PynamoDB Attribute class based on the Python value type.

    Args:
        value: Python value to determine serialization class for

    Returns:
        Attribute: PynamoDB Attribute class instance for serialization

    Raises:
        ValueError: If value type cannot be mapped to a PynamoDB attribute

    Examples:
        >>> _get_class_for_serialize("hello")
        <UnicodeAttribute()>
        >>> _get_class_for_serialize(42)
        <NumberAttribute()>
        >>> _get_class_for_serialize({"key": "value"})
        <MapAttribute()>
        >>> _get_class_for_serialize([1, 2, 3])
        <ListAttribute()>
    """
    if isinstance(value, dict):
        return MapAttribute()
    elif isinstance(value, list):
        return ListAttribute()
    elif isinstance(value, set):
        if len(value):
            if isinstance(next(iter(value)), bool):
                raise ValueError("BooleanAttribute does not support sets")
            elif isinstance(next(iter(value)), str):
                return UnicodeSetAttribute()
            elif isinstance(next(iter(value)), (int, float)):
                return NumberSetAttribute()
            elif isinstance(next(iter(value)), bytes):
                return BinarySetAttribute()
        return UnicodeSetAttribute()
    elif isinstance(value, bool):
        return BooleanAttribute()
    elif isinstance(value, str):
        return UnicodeAttribute()
    elif isinstance(value, (int, float)):
        return NumberAttribute()
    elif isinstance(value, bytes):
        return BinaryAttribute()
    else:
        raise ValueError(f"Cannot determine PynamoDB attribute type for value: {value}")


class DictAttribute(Attribute[Dict[str, _T]]):
    """A dictionary attribute that stores key-value pairs where values are of a specific Attribute type.

    Similar to ListAttribute but for dictionaries with arbitrary string keys.
    The 'of' parameter specifies the type of the dictionary values.

    Args:
        hash_key (bool, optional): Whether this attribute is a hash key. Defaults to False.
        range_key (bool, optional): Whether this attribute is a range key. Defaults to False.
        null (bool, optional): Whether null values are allowed. Defaults to None.
        default: Default value or callable. Defaults to None.
        attr_name (str, optional): DynamoDB attribute name. Defaults to None.
        of (Type[_T], optional): The Attribute class for dictionary values. Defaults to None.

    Attributes:
        attr_type: DynamoDB attribute type (MAP)
        element_type: The Attribute class for dictionary values

    Examples:
        >>> # Dictionary of RegionFacts objects
        >>> region_facts = DictAttribute(of=RegionFacts, attr_name="RegionFacts")

        >>> # Dictionary of strings
        >>> string_dict = DictAttribute(of=UnicodeAttribute, attr_name="StringDict")

        >>> # Dictionary of numbers
        >>> number_dict = DictAttribute(of=NumberAttribute, attr_name="NumberDict")

        >>> # Usage in model
        >>> class ZoneModel(DatabaseTable):
        ...     zone_id = UnicodeAttribute(hash_key=True)
        ...     regions = DictAttribute(of=RegionFactsAttribute, attr_name="Regions")

        >>> # Creating instance
        >>> zone = ZoneModel(
        ...     zone_id="production",
        ...     regions={
        ...         "us-west-2": RegionFacts(aws_region="us-west-2", az_count=4),
        ...         "us-east-1": RegionFacts(aws_region="us-east-1", az_count=6)
        ...     }
        ... )
    """

    attr_type = MAP
    element_type: Optional[Type[Attribute]] = None

    def __init__(
        self,
        hash_key: bool = False,
        range_key: bool = False,
        null: Optional[bool] = None,
        default: Optional[Union[Any, Callable[..., Any]]] = None,
        attr_name: Optional[str] = None,
        of: Optional[Type[_T]] = None,
    ) -> None:
        super().__init__(
            hash_key=hash_key,
            range_key=range_key,
            null=null,
            default=default,
            attr_name=attr_name,
        )
        if of:
            if not issubclass(of, Attribute):
                raise ValueError("'of' must be a subclass of Attribute")
            self.element_type = of

    def serialize(self, values: Dict[str, Any], *, null_check: bool = True) -> Dict[str, Any]:
        """Encode the given dictionary of objects into a dictionary of AttributeValue types.

        Args:
            values (Dict[str, Any]): Dictionary to serialize
            null_check (bool, optional): Whether to perform null checks. Defaults to True.

        Returns:
            Dict[str, Any]: Serialized dictionary ready for DynamoDB

        Raises:
            TypeError: If values is not a dict or keys are not strings
            ValueError: If dictionary values don't match element_type
            AttributeNullError: If null value found when not allowed

        Examples:
            >>> # Serialize a dictionary of region facts
            >>> regions = {
            ...     "us-west-2": RegionFacts(aws_region="us-west-2"),
            ...     "us-east-1": RegionFacts(aws_region="us-east-1")
            ... }
            >>> serialized = dict_attr.serialize(regions)
        """
        if values is None:
            return None

        if not isinstance(values, dict):
            raise TypeError(f"Expected dict, got {type(values)}")

        rval = {}
        for key, value in values.items():
            if not isinstance(key, str):
                raise TypeError(f"Dictionary keys must be strings, got {type(key)} for key {key}")

            attr = self._get_serialize_class(value)

            # Same validation logic as ListAttribute
            if self.element_type and value is not None and not isinstance(attr, self.element_type):
                raise ValueError("Dictionary values must be of type: {}".format(self.element_type.__name__))

            attr_type = attr.attr_type
            try:
                if isinstance(attr, (ListAttribute, MapAttribute)):
                    attr_value = attr.serialize(value, null_check=null_check)
                else:
                    attr_value = attr.serialize(value)
            except AttributeNullError as e:
                e.prepend_path(f"[{key}]")
                raise

            if attr_value is None:
                # When attribute values serialize to "None" (e.g. empty sets) we store {"NULL": True} in DynamoDB.
                attr_type = NULL
                attr_value = True

            rval[key] = {attr_type: attr_value}

        return rval

    def deserialize(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """Decode from dictionary of AttributeValue types.

        Args:
            values (Dict[str, Any]): Serialized dictionary from DynamoDB

        Returns:
            Dict[str, Any]: Deserialized dictionary with proper types

        Raises:
            TypeError: If values is not a dict

        Examples:
            >>> # Deserialize from DynamoDB response
            >>> db_data = {
            ...     "us-west-2": {"M": {"AwsRegion": {"S": "us-west-2"}}},
            ...     "us-east-1": {"M": {"AwsRegion": {"S": "us-east-1"}}}
            ... }
            >>> regions = dict_attr.deserialize(db_data)
        """
        if values is None:
            return None

        if not isinstance(values, dict):
            raise TypeError(f"Expected dict, got {type(values)}")

        if self.element_type:
            # Same logic as ListAttribute - create element_attr instance
            element_attr: Attribute
            if issubclass(self.element_type, (BinaryAttribute, BinarySetAttribute)):
                element_attr = self.element_type(legacy_encoding=False)
            else:
                element_attr = self.element_type()
                if isinstance(element_attr, MapAttribute):
                    element_attr._make_attribute()  # ensure attr_name exists

            deserialized_dict = {}
            for key, attribute_value in values.items():
                value = None
                if NULL not in attribute_value:
                    # set attr_name in case `get_value` raises an exception
                    element_attr.attr_name = f"{self.attr_name}[{key}]" if self.attr_name else f"[{key}]"
                    value = element_attr.deserialize(element_attr.get_value(attribute_value))
                deserialized_dict[key] = value
            return deserialized_dict

        # Same fallback logic as ListAttribute for untyped dictionaries
        return {
            key: DESERIALIZE_CLASS_MAP[attr_type].deserialize(attr_value)
            for key, v in values.items()
            for attr_type, attr_value in v.items()
        }

    def _get_serialize_class(self, value):
        """Get the appropriate Attribute class for serializing a value.

        Args:
            value: Value to get serialization class for

        Returns:
            Attribute: Attribute class instance for serialization

        Examples:
            >>> attr = dict_attr._get_serialize_class("test")
            >>> isinstance(attr, UnicodeAttribute)
            True
        """
        # Same logic as ListAttribute._get_serialize_class
        if value is None:
            return NullAttribute()
        if isinstance(value, Attribute):
            return value
        if self.element_type:
            if issubclass(self.element_type, (BinaryAttribute, BinarySetAttribute)):
                return self.element_type(legacy_encoding=False)
            return self.element_type()
        return _get_class_for_serialize(value)

    @classmethod
    def is_raw(cls) -> bool:
        """Check if this is a raw DictAttribute.

        Returns:
            bool: True if this is the base DictAttribute class

        Examples:
            >>> DictAttribute.is_raw()
            True
            >>> class TypedDictAttribute(DictAttribute):
            ...     pass
            >>> TypedDictAttribute.is_raw()
            False
        """
        return cls == DictAttribute


class EnhancedInit:
    """Enhanced init mixin that supports both snake_case and PascalCase field names.

    This allows for compatibility with both PynamoDB's standard attribute names
    and the DynamoDB API's PascalCase naming convention. Enables round-trip
    compatibility with DynamoDB data and to_simple_dict() output.

    Features:
        - **Automatic Conversion**: PascalCase attr_names to snake_case Python fields
        - **Nested Object Support**: Handles MapAttribute, ListAttribute, DictAttribute
        - **Round-trip Compatible**: Works with to_simple_dict() output
        - **Mixed Usage**: Supports both naming conventions simultaneously

    Examples:
        >>> # Using snake_case (standard PynamoDB)
        >>> item = DatabaseTable(created_at=datetime.now(), updated_at=datetime.now())

        >>> # Using PascalCase attr_names (DynamoDB format)
        >>> item = DatabaseTable(CreatedAt=datetime.now(), UpdatedAt=datetime.now())

        >>> # Mixed usage (both formats)
        >>> item = DatabaseTable(created_at=datetime.now(), UpdatedAt=datetime.now())

        >>> # Round-trip from to_simple_dict()
        >>> original = DatabaseTable(created_at=datetime.now())
        >>> data = original.to_simple_dict()
        >>> restored = DatabaseTable(**data)  # Uses PascalCase attr_names

        >>> # Complex nested structures
        >>> data = {
        ...     "Client": "acme",
        ...     "AccountFacts": {
        ...         "Client": "acme",
        ...         "Kms": {"AwsAccountId": "123", "AllowSNS": True}
        ...     },
        ...     "Contacts": [{"Name": "John", "Email": "john@acme.com"}]
        ... }
        >>> item = ZoneFactsModel(**data)  # Nested objects auto-converted
    """

    def __init__(self, *args, **kwargs):
        """Initialize with support for both snake_case and PascalCase field names.

        Enables round-trip compatibility with DynamoDB data and to_simple_dict() output.
        This allows loading data directly from DynamoDB command line dumps or API responses.
        Handles nested MapAttribute, ListAttribute, and DictAttribute objects with custom __init__ methods.

        Args:
            *args: Positional arguments for PynamoDB Model.__init__
            **kwargs: Keyword arguments with either snake_case or PascalCase (attr_name) keys

        Examples:
            >>> # Standard initialization
            >>> item = MyModel(field1="value1", field2="value2")

            >>> # PascalCase initialization (from DynamoDB)
            >>> item = MyModel(Field1="value1", Field2="value2")

            >>> # Nested object initialization
            >>> item = MyModel(
            ...     NestedData={"SubField": "value"},
            ...     ListData=[{"Item": "test"}]
            ... )
        """
        # Create a mapping of attr_name -> snake_case attribute name
        attr_name_map = {}

        # Use PynamoDB's _attributes class variable to get all model attributes
        if hasattr(self.__class__, "_attributes"):
            for snake_case_name, attr_obj in self.__class__._attributes.items():
                # Check if this attribute has an attr_name (PascalCase DynamoDB name)
                if hasattr(attr_obj, "attr_name") and attr_obj.attr_name:
                    # Map PascalCase attr_name to snake_case attribute name
                    attr_name_map[attr_obj.attr_name] = snake_case_name

        # Process kwargs to convert PascalCase attr_names to snake_case AND handle nested objects
        converted_kwargs = {}

        for key, value in kwargs.items():
            if key in attr_name_map:
                # Convert PascalCase attr_name to snake_case attribute name
                snake_case_key = attr_name_map[key]

                # Get the actual attribute object to check its type
                attr_obj = self.__class__._attributes[snake_case_key]

                # Handle nested objects that need custom __init__ processing
                processed_value = self._process_nested_value(attr_obj, value)
                converted_kwargs[snake_case_key] = processed_value
            else:
                # Keep original key (assume it's already snake_case)
                # But still check if it needs nested processing
                if key in self.__class__._attributes:
                    attr_obj = self.__class__._attributes[key]
                    processed_value = self._process_nested_value(attr_obj, value)
                    converted_kwargs[key] = processed_value
                else:
                    converted_kwargs[key] = value

        # Call parent __init__ with converted kwargs
        super().__init__(*args, **converted_kwargs)

    def _process_nested_value(self, attr_obj, value):
        """Process nested values for MapAttribute, ListAttribute, and DictAttribute objects.

        Handles the case where nested MapAttribute, ListAttribute, or DictAttribute classes have
        custom __init__ methods that need PascalCase -> snake_case conversion.

        Args:
            attr_obj: PynamoDB attribute object
            value: Value to process

        Returns:
            Any: Processed value with nested objects properly initialized

        Examples:
            >>> # Internal usage - handles nested object conversion
            >>> processed = self._process_nested_value(map_attr, {"PascalField": "value"})
        """
        # Handle None values
        if value is None:
            return value

        # Handle MapAttribute with custom __init__
        if isinstance(attr_obj, MapAttribute):
            # Check if the MapAttribute class has a custom __init__ (our enhanced one)
            map_class = attr_obj.__class__
            if hasattr(map_class, "__init__") and isinstance(value, dict):
                # Create new instance using our enhanced __init__ that handles PascalCase
                return map_class(**value)
            else:
                # Standard dict - let PynamoDB handle it
                return value

        # Handle DictAttribute with MapAttribute elements
        elif isinstance(attr_obj, DictAttribute):
            if isinstance(value, dict) and value:
                # Check if dict contains dict objects that need MapAttribute processing
                processed_dict = {}
                for key, item in value.items():
                    if isinstance(item, dict) and hasattr(attr_obj, "element_type"):
                        # Get the element type of the DictAttribute
                        element_class = attr_obj.element_type
                        if inspect.isclass(element_class) and issubclass(element_class, MapAttribute):
                            if hasattr(element_class, "__init__"):
                                # Create new instance with enhanced __init__
                                processed_item = element_class(**item)
                                processed_dict[key] = processed_item
                            else:
                                processed_dict[key] = item
                        else:
                            processed_dict[key] = item
                    else:
                        processed_dict[key] = item
                return processed_dict
            else:
                return value

        # Handle ListAttribute with MapAttribute elements
        elif isinstance(attr_obj, ListAttribute):
            if isinstance(value, list) and value:
                # Check if list contains dict objects that need MapAttribute processing
                processed_list = []
                for item in value:
                    if isinstance(item, dict) and hasattr(attr_obj, "element_type"):
                        # Get the element type of the ListAttribute
                        element_class = attr_obj.element_type
                        if inspect.isclass(element_class) and issubclass(element_class, MapAttribute):
                            if hasattr(element_class, "__init__"):
                                processed_item = element_class(**item)
                                processed_list.append(processed_item)
                            else:
                                processed_list.append(item)
                        else:
                            processed_list.append(item)
                    else:
                        processed_list.append(item)
                return processed_list
            else:
                return value

        # For all other attribute types, return as-is
        else:
            return value


class EnhancedMapAttribute(EnhancedInit, MapAttribute):
    """Enhanced MapAttribute that supports both snake_case and PascalCase field names.

    Inherits from EnhancedInit to provide automatic conversion between naming conventions.
    This allows for compatibility with both PynamoDB's standard attribute names
    and the DynamoDB API's PascalCase naming convention.

    Features:
        - **Dual Naming Support**: Both snake_case and PascalCase initialization
        - **Nested Object Handling**: Automatic conversion of nested structures
        - **API Compatibility**: Works with DynamoDB API responses
        - **Type Safety**: Maintains full type checking and validation

    Examples:
        >>> class RegionFacts(EnhancedMapAttribute):
        ...     aws_region = UnicodeAttribute(attr_name="AwsRegion")
        ...     az_count = NumberAttribute(attr_name="AzCount")

        >>> # Both naming styles work
        >>> region1 = RegionFacts(aws_region="us-west-2", az_count=4)
        >>> region2 = RegionFacts(AwsRegion="us-west-2", AzCount=4)

        >>> # From DynamoDB API response
        >>> api_data = {"AwsRegion": "us-west-2", "AzCount": 4}
        >>> region3 = RegionFacts(**api_data)

        >>> # Nested usage in models
        >>> class ZoneModel(DatabaseTable):
        ...     regions = DictAttribute(of=RegionFacts, attr_name="Regions")
    """

    pass


class DatabaseTable(EnhancedInit, Model):
    """Base model for all PynamoDB tables with enhanced initialization and audit fields.

    Provides automatic audit field management and supports both snake_case and PascalCase
    field names for compatibility with DynamoDB API responses. All database table models
    should inherit from this base class.

    Attributes:
        created_at (Optional[datetime]): Timestamp of the item creation (auto-managed)
        updated_at (Optional[datetime]): Timestamp of the item update (auto-managed)

    Features:
        - **Automatic Timestamps**: Created/updated timestamps managed automatically
        - **Enhanced Initialization**: Support for both naming conventions
        - **Audit Trail**: Built-in creation and modification tracking
        - **API Compatibility**: Works with DynamoDB API responses

    Examples:
        >>> class ItemModel(DatabaseTable):
        ...     class Meta:
        ...         table_name = "items"
        ...
        ...     item_id = UnicodeAttribute(hash_key=True, attr_name="ItemId")
        ...     name = UnicodeAttribute(attr_name="Name")

        >>> # Create and save item
        >>> item = ItemModel(item_id="123", name="Test Item")
        >>> item.save()  # Automatically sets created_at and updated_at

        >>> # Load from DynamoDB API response
        >>> api_data = {"ItemId": "123", "Name": "Test Item"}
        >>> item2 = ItemModel(**api_data)

        >>> # Check audit fields
        >>> print(f"Created: {item.created_at}")
        >>> print(f"Updated: {item.updated_at}")
    """

    class Meta:
        """Meta class for the PynamoDB model.

        This should be overridden in subclasses to define table name and region.

        Attributes:
            table_name (str): DynamoDB table name (must be overridden)
            host (str): DynamoDB host endpoint
            region (str): AWS region
            read_capacity_units (int): Read capacity for provisioned mode
            write_capacity_units (int): Write capacity for provisioned mode
            billing_mode (str): DynamoDB billing mode

        Examples:
            >>> class MyTable(DatabaseTable):
            ...     class Meta:
            ...         table_name = "my-table"
            ...         region = "us-west-2"
        """

        table_name = None
        host = get_dynamodb_host()
        region = get_region()
        read_capacity_units = 1
        write_capacity_units = 1
        billing_mode = "PAY_PER_REQUEST"

    created_at = UTCDateTimeAttribute(null=True, attr_name="CreatedAt")
    updated_at = UTCDateTimeAttribute(null=True, attr_name="UpdatedAt")


class TableFactory:
    """Thread-safe factory for creating client-specific PynamoDB models.

    Provides dynamic model creation with client-specific table naming and caching
    for performance optimization. Ensures thread safety for concurrent access
    and maintains a cache of created model classes.

    Attributes:
        _model_cache (Dict[str, Type[Model]]): Cache of created model classes
        _cache_lock (threading.Lock): Thread lock for cache operations

    Features:
        - **Dynamic Model Creation**: Client-specific models with proper table names
        - **Thread Safety**: Safe for concurrent access and model creation
        - **Performance Caching**: Avoids recreating identical model classes
        - **Table Management**: Create, delete, and check table existence

    Examples:
        >>> # Get client-specific model
        >>> acme_model = TableFactory.get_model(BaseFactsModel, "acme")
        >>> enterprise_model = TableFactory.get_model(BaseFactsModel, "enterprise")

        >>> # Create table for client
        >>> TableFactory.create_table(BaseFactsModel, "acme", wait=True)

        >>> # Check if table exists
        >>> exists = TableFactory.exists(BaseFactsModel, "acme")
        >>> print(f"Table exists: {exists}")

        >>> # Use client-specific model
        >>> acme_item = acme_model(field1="value1", field2="value2")
        >>> acme_item.save()
    """

    _model_cache: Dict[str, Type[Model]] = {}
    _cache_lock = threading.Lock()

    @classmethod
    def get_model(cls, base_model: Type[T], client: str | None = None) -> Type[T]:
        """Get a client-specific model class with proper table naming.

        Creates a new class dynamically to avoid Meta class conflicts.
        Thread-safe with caching for performance. Each client gets their
        own table with a unique name.

        Args:
            base_model (Type[T]): Base model class (e.g., ClientFactsModel)
            client (str): Client name for table naming

        Returns:
            Type[T]: Client-specific model class with proper table name

        Examples:
            >>> # Get client-specific models
            >>> acme_portfolio = TableFactory.get_model(PortfolioFactsModel, "acme")
            >>> enterprise_portfolio = TableFactory.get_model(PortfolioFactsModel, "enterprise")

            >>> # Table names are automatically different
            >>> print(acme_portfolio.Meta.table_name)      # "acme-core-automation-portfolios"
            >>> print(enterprise_portfolio.Meta.table_name) # "enterprise-core-automation-portfolios"

            >>> # Use the client-specific models
            >>> acme_item = acme_portfolio(client="acme", portfolio="web-services")
            >>> enterprise_item = enterprise_portfolio(client="enterprise", portfolio="platform")
        """
        cache_key = f"{base_model.__name__}_{client}" if client else base_model.__name__

        # Check cache first (outside lock for performance)
        if cache_key in cls._model_cache:
            return cls._model_cache[cache_key]

        # Create new class with thread safety
        with cls._cache_lock:
            # Double-check pattern - another thread might have created it
            if cache_key in cls._model_cache:
                return cls._model_cache[cache_key]

            # Create a new Meta class for this client
            meta_attrs = {}
            if hasattr(base_model, "Meta"):
                # Copy all Meta attributes from base class
                for attr in dir(base_model.Meta):
                    if not attr.startswith("_"):
                        meta_attrs[attr] = getattr(base_model.Meta, attr)

            # Override table_name for this client
            meta_attrs["table_name"] = get_table_name(base_model, client)

            # Create new Meta class
            ClientMeta = type("Meta", (), meta_attrs)

            # Create new model class with client-specific Meta
            client_model = type(cache_key, (base_model,), {"Meta": ClientMeta})

            # Cache the new class
            cls._model_cache[cache_key] = client_model

            return client_model

    @classmethod
    def create_table(cls, base_model: Type[T], client: str | None = None, wait: bool = True) -> bool:
        """Create the table for a client-specific model.

        Args:
            base_model (Type[T]): Base model class (e.g., ClientFactsModel)
            client (str): Client name for table naming
            wait (bool, optional): Whether to wait for the table creation to complete. Defaults to True.

        Returns:
            bool: True if table was created, False if it already exists

        Examples:
            >>> # Create table and wait for completion
            >>> created = TableFactory.create_table(PortfolioFactsModel, "acme", wait=True)
            >>> print(f"Table created: {created}")

            >>> # Create table without waiting
            >>> TableFactory.create_table(ZoneFactsModel, "acme", wait=False)

            >>> # Check if table was actually created
            >>> if TableFactory.create_table(ItemModel, "acme"):
            ...     print("New table created")
            ... else:
            ...     print("Table already existed")
        """
        model_class = cls.get_model(base_model, client)

        if not model_class.exists():
            model_class.create_table(wait=wait)
            return True
        return False

    @classmethod
    def delete_table(cls, base_model: Type[T], client: str | None = None, wait: bool = True) -> bool:
        """Delete the table for a client-specific model.

        Args:
            base_model (Type[T]): Base model class (e.g., ClientFactsModel)
            client (str): Client name for table naming
            wait (bool, optional): Whether to wait for the deletion to complete. Defaults to True.

        Returns:
            bool: True if table was deleted, False if it did not exist

        Examples:
            >>> # Delete table and wait for completion
            >>> deleted = TableFactory.delete_table(PortfolioFactsModel, "acme", wait=True)
            >>> print(f"Table deleted: {deleted}")

            >>> # Delete table without waiting
            >>> TableFactory.delete_table(ZoneFactsModel, "acme", wait=False)

            >>> # Conditional deletion
            >>> if TableFactory.exists(ItemModel, "test-client"):
            ...     TableFactory.delete_table(ItemModel, "test-client")
            ...     print("Test table cleaned up")
        """
        model_class = cls.get_model(base_model, client)

        if model_class.exists():
            result = model_class.delete_table(wait=wait)
            return True
        return False

    @classmethod
    def exists(cls, base_model: Type[T], client: str | None = None) -> bool:
        """Check if the table for a client-specific model exists.

        Args:
            base_model (Type[T]): Base model class (e.g., ClientFactsModel)
            client (str): Client name for table naming

        Returns:
            bool: True if the table exists, False otherwise

        Examples:
            >>> # Check table existence
            >>> if TableFactory.exists(PortfolioFactsModel, "acme"):
            ...     print("ACME portfolio table exists")
            ... else:
            ...     print("Need to create ACME portfolio table")

            >>> # Conditional operations
            >>> clients = ["acme", "enterprise", "startup"]
            >>> for client in clients:
            ...     if not TableFactory.exists(ItemModel, client):
            ...         TableFactory.create_table(ItemModel, client)
            ...         print(f"Created table for {client}")
        """
        model_class = cls.get_model(base_model, client)
        return model_class.exists()

    @classmethod
    def clear_cache(cls):
        """Clear the model cache (useful for testing).

        Removes all cached client-specific model classes. This is primarily
        used in testing scenarios to ensure clean state between tests.

        Examples:
            >>> # Clear cache in test teardown
            >>> TableFactory.clear_cache()

            >>> # Ensure clean state for tests
            >>> def test_cleanup():
            ...     TableFactory.clear_cache()
            ...     # Models will be recreated on next get_model() call
        """
        with cls._cache_lock:
            cls._model_cache.clear()


class DatabaseRecord(BaseModel, ABC):
    """Base Pydantic model that mirrors DatabaseTable functionality.

    Provides audit fields and common serialization patterns for all domain models.
    Should be subclassed by all Pydantic models that correspond to PynamoDB DatabaseTable models.
    Used for API serialization and data transfer objects.

    Attributes:
        created_at (Optional[datetime]): Record creation timestamp (auto-managed by DatabaseTable)
        updated_at (Optional[datetime]): Last modification timestamp (auto-managed by DatabaseTable)

    Features:
        - **API Serialization**: Optimized for JSON API responses
        - **Type Safety**: Full Pydantic validation and type checking
        - **Audit Fields**: Mirrors DatabaseTable audit functionality
        - **Flexible Serialization**: Control over field inclusion/exclusion

    Examples:
        >>> class ItemRecord(DatabaseRecord):
        ...     item_id: str = Field(..., alias="ItemId")
        ...     name: str = Field(..., alias="Name")
        ...
        ...     @classmethod
        ...     def from_dynamodb(cls, db_model: ItemModel) -> "ItemRecord":
        ...         return cls(
        ...             ItemId=db_model.item_id,
        ...             Name=db_model.name,
        ...             CreatedAt=db_model.created_at,
        ...             UpdatedAt=db_model.updated_at
        ...         )

        >>> # Convert from database model
        >>> db_item = ItemModel.get("123")
        >>> api_record = ItemRecord.from_dynamodb(db_item)

        >>> # Serialize for API response
        >>> response_data = api_record.model_dump()
        >>> # {"ItemId": "123", "Name": "Test Item", "CreatedAt": "2025-01-01T12:00:00Z"}
    """

    model_config = ConfigDict(from_attributes=True, validate_assignment=True, populate_by_name=True)

    # Audit fields - mirror DatabaseTable
    created_at: Optional[datetime] = Field(
        alias="CreatedAt",
        description="Record creation timestamp (auto-managed by DatabaseTable)",
        default_factory=lambda: datetime.now(tz=timezone.utc),
    )
    updated_at: Optional[datetime] = Field(
        alias="UpdatedAt",
        description="Last modification timestamp (auto-managed by DatabaseTable)",
        default_factory=lambda: datetime.now(tz=timezone.utc),
    )

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Smart serialization with audit field control.

        Args:
            **kwargs: Additional arguments for BaseModel.model_dump()

        Returns:
            Dict[str, Any]: Serialized dictionary

        Examples:
            >>> record = ItemRecord(ItemId="123", Name="Test")

            >>> # Default - PascalCase with audit excluded
            >>> api_data = record.model_dump()
            >>> # {"ItemId": "123", "Name": "Test"}

            >>> # Snake case for database
            >>> db_data = record.model_dump(by_alias=False)
            >>> # {"item_id": "123", "name": "Test"}
        """
        kwargs.setdefault("by_alias", True)
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)

    def model_dump_with_audit(self, **kwargs) -> Dict[str, Any]:
        """Convenience method for serialization that includes audit fields.

        Args:
            **kwargs: Additional arguments for model_dump()

        Returns:
            Dict[str, Any]: Serialized dictionary with audit fields

        Examples:
            >>> record = ItemRecord(ItemId="123", Name="Test")
            >>> full_data = record.model_dump_with_audit()
            >>> # {"ItemId": "123", "Name": "Test", "CreatedAt": "2025-01-01T12:00:00Z", "UpdatedAt": "2025-01-01T12:00:00Z"}
        """
        return self.model_dump(include_audit=True, **kwargs)

    def __repr__(self) -> str:
        """Base representation showing class name and key identifying fields.

        Returns:
            str: String representation of the record

        Examples:
            >>> record = ItemRecord(ItemId="123", Name="Test")
            >>> repr(record)
            '<ItemRecord(id=123)>'

            >>> # Falls back to available fields
            >>> record_no_id = SomeRecord(Name="Test")
            >>> repr(record_no_id)
            '<SomeRecord(id=Test)>'
        """
        class_name = self.__class__.__name__
        # Try to find a primary identifier field
        identifier = getattr(self, "prn", getattr(self, "id", getattr(self, "name", "unknown")))
        return f"<{class_name}(id={identifier})>"


class Paginator(BaseModel):
    """Paginator class to handle pagination."""

    model_config = ConfigDict(from_attributes=True, validate_assignment=True)

    cursor: str | None = Field(default=None, description="Last evaluated key from AWS for pagination")
    limit: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Maximum number of items to return per page",
    )

    earliest_time: datetime | None = Field(default=None, description="Earliest time to filter items")
    latest_time: datetime | None = Field(default=None, description="Latest time to filter items")
    sort_forward: bool | None = Field(default=True, description="Sort order: True for ascending, False for descending")
    active_filter: str | None = Field(default=None, description="Filter by active status")
    email_filter: str | None = Field(default=None, description="Filter by email address")
    page_size: int | None = Field(default=None, ge=1, le=100, description="Number of items per page")

    total_count: int = Field(default=0, description="Total count of items in the result set")

    def get_query_args(self) -> dict:
        args = {"limit": self.limit}
        if self.cursor is not None:
            args["last_evaluated_key"] = self.last_evaluated_key
        if self.sort_forward is not None:
            args["scan_index_forward"] = self.sort_forward
        if self.page_size is not None:
            args["page_size"] = self.page_size
        return args

    def get_scan_args(self) -> dict:
        """
        Docstring for get_query_args
        """
        args = {"limit": self.limit}
        if self.cursor is not None:
            args["last_evaluated_key"] = self.last_evaluated_key
        if self.page_size is not None:
            args["page_size"] = self.page_size

        return args

    @property
    def last_evaluated_key(self) -> dict | None:
        """Return the last evaluated key (cursor)."""
        return self._decode_cursor(self.cursor)

    @last_evaluated_key.setter
    def last_evaluated_key(self, value: dict | None) -> None:
        """Set the last evaluated key (cursor) from a dict.  Use the 'cursor' key for the base64 string."""
        if isinstance(value, dict):
            self.cursor = self._encode_cursor(value)

    @property
    def sort(self) -> str:
        """Return the sort order as a string."""
        return "ascending" if self.sort_forward else "descending"

    @sort.setter
    def sort(self, value: str) -> None:
        """Set the sort order based on a string value."""
        if value.lower() == "ascending":
            self.sort_forward = True
        elif value.lower() == "descending":
            self.sort_forward = False

    @model_validator(mode="before")
    def validate_model_before(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Validate and convert pagination parameters."""
        if not "sort_forward" in values and "sort" in values:
            values["sort_forward"] = str(values.get("sort", "ascending")).lower() == "ascending"
        return values

    @field_validator("earliest_time", mode="before")
    def validate_earliest_time(cls, v: Any) -> Optional[datetime]:
        """Validate earliest_time to ensure it is a valid datetime or None."""
        return cls.validate_date(v)

    @field_validator("latest_time", mode="before")
    def validate_latest_time(cls, v: Any) -> Optional[datetime]:
        """Validate latest_time to ensure it is a valid datetime or None."""
        return cls.validate_date(v)

    @staticmethod
    def _decode_cursor(cursor: str | dict) -> Optional[dict]:
        """Decode a base64 encoded cursor string to a dictionary."""
        if cursor is None:
            return None
        try:
            decoded = base64.b64decode(cursor).decode(encoding="utf-8")
            # Don't use my parser.  My parser converts date string to datetime, which is not what we want here.
            return json.loads(decoded)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _encode_cursor(cursor: str | None) -> str:
        """Return the last evaluated key as a JSON string."""
        if cursor is None:
            return None
        json_str = json.dumps(cursor)
        return base64.b64encode(json_str.encode(encoding="utf-8")).decode(encoding="utf-8")

    @classmethod
    def validate_date(cls, date: Any) -> datetime | None:
        """
        Validate and convert date strings to datetime objects.
        """
        if not date:
            return None
        if isinstance(date, str):
            try:
                return parser.parse(date)
            except Exception:
                return None
        return date

    def get_metadata(self):
        """Get metadata for the paginator.

        Returns:
            dict: Metadata including cursor and total count

        Examples:
            >>> paginator = Paginator(cursor={"id": "123"}, total_count=50)
            >>> paginator.get_metadata()
            {'cursor': '{"id": "123"}', 'total_count': 50}
        """
        return {
            "cursor": self.cursor,
            "page_size": self.limit,
            "total_count": self.total_count,
            "has_more_pages": self.cursor is not None,
        }
