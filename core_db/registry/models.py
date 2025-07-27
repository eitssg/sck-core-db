"""Defines a common registry class model for all Registry items"""

import re
from typing import Protocol, Optional, Any, Iterator
from pynamodb.models import Model
from pynamodb.attributes import MapAttribute
from pynamodb.expressions.condition import Condition


class ModelProtocol(Protocol):
    """
    A Protocol defining the common methods for all models in the registry.

    This protocol defines the standard PynamoDB Model interface that all
    registry models should implement. Classes don't need to explicitly inherit
    from this protocol - type checkers will verify structural compatibility.
    """

    # Instance methods
    def __init__(self, *args, **kwargs) -> None:
        """Initialize a model instance."""
        ...

    def __repr__(self) -> str:
        """Return string representation of the model."""
        ...

    def save(self, condition: Optional[Condition] = None, **kwargs) -> None:
        """
        Save the model instance to DynamoDB.

        :param condition: Optional condition for the save operation
        :type condition: Condition, optional
        :param kwargs: Additional save parameters
        """
        ...

    def delete(self, condition: Optional[Condition] = None, **kwargs) -> None:
        """
        Delete the model instance from DynamoDB.

        :param condition: Optional condition for the delete operation
        :type condition: Condition, optional
        :param kwargs: Additional delete parameters
        """
        ...

    def update(
        self, actions: list, condition: Optional[Condition] = None, **kwargs
    ) -> None:
        """
        Update the model instance in DynamoDB.

        :param actions: List of update actions to perform
        :type actions: list
        :param condition: Optional condition for the update operation
        :type condition: Condition, optional
        :param kwargs: Additional update parameters
        """
        ...

    def refresh(self, consistent_read: Optional[bool] = None) -> None:
        """
        Refresh the model instance from DynamoDB.

        :param consistent_read: Whether to use consistent read
        :type consistent_read: bool, optional
        """
        ...

    def serialize(self, values: Optional[dict] = None, **kwargs) -> dict:
        """
        Serialize the model instance to a dictionary.

        :param values: Optional values to serialize
        :type values: dict, optional
        :param kwargs: Additional serialization parameters
        :returns: Serialized model data
        :rtype: dict
        """
        ...

    def deserialize(self, values: dict, **kwargs) -> None:
        """
        Deserialize values into the model instance.

        :param values: Values to deserialize
        :type values: dict
        :param kwargs: Additional deserialization parameters
        """
        ...

    def to_simple_dict(self) -> dict:
        """
        Convert the model instance to a simple dictionary.

        :returns: Dictionary representation of the model
        :rtype: dict
        """
        ...

    def get_attributes(self) -> dict:
        """
        Get all model attributes.

        :returns: Dictionary of model attributes
        :rtype: dict
        """
        ...

    def convert_keys(self, **kwargs) -> dict:
        """
        Convert attribute keys to proper case.

        :param kwargs: Key-value pairs to convert
        :returns: Dictionary with converted keys
        :rtype: dict
        """
        ...

    # Class methods
    @classmethod
    def get(
        cls, hash_key: Any, range_key: Optional[Any] = None, **kwargs
    ) -> "ModelProtocol":
        """
        Get a single item from DynamoDB.

        :param hash_key: The hash key value
        :type hash_key: Any
        :param range_key: The range key value (if applicable)
        :type range_key: Any, optional
        :param kwargs: Additional get parameters
        :returns: The retrieved model instance
        :rtype: ModelProtocol
        """
        ...

    @classmethod
    def query(cls, hash_key: Any, **kwargs) -> Iterator["ModelProtocol"]:
        """
        Query items from DynamoDB.

        :param hash_key: The hash key value to query
        :type hash_key: Any
        :param kwargs: Additional query parameters (range_key_condition, filter_condition, etc.)
        :returns: Iterator of model instances
        :rtype: Iterator[ModelProtocol]
        """
        ...

    @classmethod
    def scan(cls, **kwargs) -> Iterator["ModelProtocol"]:
        """
        Scan items from DynamoDB.

        :param kwargs: Scan parameters (filter_condition, attributes_to_get, etc.)
        :returns: Iterator of model instances
        :rtype: Iterator[ModelProtocol]
        """
        ...

    @classmethod
    def exists(cls) -> bool:
        """
        Check if the DynamoDB table exists.

        :returns: True if table exists, False otherwise
        :rtype: bool
        """
        ...

    @classmethod
    def create_table(cls, wait: bool = False, **kwargs) -> None:
        """
        Create the DynamoDB table.

        :param wait: Whether to wait for table creation to complete
        :type wait: bool
        :param kwargs: Additional table creation parameters
        """
        ...

    @classmethod
    def delete_table(cls) -> None:
        """Delete the DynamoDB table for this model."""
        ...

    @classmethod
    def describe_table(cls) -> dict:
        """
        Describe the DynamoDB table.

        :returns: Table description from DynamoDB
        :rtype: dict
        """
        ...

    @classmethod
    def count(cls, hash_key: Optional[Any] = None, **kwargs) -> int:
        """
        Count items in the table.

        :param hash_key: Optional hash key to count items for
        :type hash_key: Any, optional
        :param kwargs: Additional count parameters
        :returns: Number of items
        :rtype: int
        """
        ...

    @classmethod
    def batch_get(cls, keys: list, **kwargs) -> Iterator["ModelProtocol"]:
        """
        Batch get multiple items from DynamoDB.

        :param keys: List of key tuples to retrieve
        :type keys: list
        :param kwargs: Additional batch get parameters
        :returns: Iterator of retrieved model instances
        :rtype: Iterator[ModelProtocol]
        """
        ...

    @classmethod
    def batch_write(cls, auto_commit: bool = True) -> Any:
        """
        Create a batch write context manager.

        :param auto_commit: Whether to auto-commit the batch
        :type auto_commit: bool
        :returns: Batch write context manager
        :rtype: Any
        """
        ...

    @classmethod
    def get_meta_data(cls) -> dict:
        """
        Get model metadata.

        :returns: Model metadata dictionary
        :rtype: dict
        """
        ...

    @classmethod
    def from_raw_data(cls, data: dict) -> "ModelProtocol":
        """
        Create model instance from raw DynamoDB data.

        :param data: Raw DynamoDB item data
        :type data: dict
        :returns: Model instance
        :rtype: ModelProtocol
        """
        ...

    @classmethod
    def get_operation_kwargs_from_instance(
        cls, instance: "ModelProtocol", **kwargs
    ) -> dict:
        """
        Get operation kwargs from a model instance.

        :param instance: The model instance
        :type instance: ModelProtocol
        :param kwargs: Additional parameters
        :returns: Operation kwargs dictionary
        :rtype: dict
        """
        ...

    @classmethod
    def get_save_args(cls, instance: "ModelProtocol", **kwargs) -> dict:
        """
        Get save arguments for a model instance.

        :param instance: The model instance
        :type instance: ModelProtocol
        :param kwargs: Additional parameters
        :returns: Save arguments dictionary
        :rtype: dict
        """
        ...


class RegistryModel(Model):
    """Common Top-Level Registry Model as a pynamodb Model"""

    # Pre-compile regex pattern to avoid recompilation on every call
    _KEY_SPLIT_PATTERN = re.compile(r"[-_]")

    def __init__(self, *args, **kwargs):
        # Convert snake_case and kebab-case keys to PascalCase keys
        kwargs = self.convert_keys(**kwargs)
        super().__init__(*args, **kwargs)

    def convert_keys(self, **kwargs) -> dict:
        # Convert snake_case and kebab-case keys to PascalCase keys
        if not kwargs:
            return kwargs
        attributes = self.get_attributes()
        return {
            self._convert_key_with_attrs(k, attributes): v for k, v in kwargs.items()
        }

    def _convert_key_with_attrs(self, key: str, attributes: dict) -> str:
        # Convert snake_case and kebab-case keys to PascalCase keys
        if hasattr(self, key) or key in attributes:
            return key
        words = self._KEY_SPLIT_PATTERN.split(key)
        return "".join(word.capitalize() for word in words)

    def _convert_key(self, key):
        # Legacy method - for backward compatibility
        attributes = self.get_attributes()
        return self._convert_key_with_attrs(key, attributes)


class ExtendedMapAttribute(MapAttribute):
    """Convert Keys to PascalCase in MapAttributes"""

    # Add the same compiled regex pattern
    _KEY_SPLIT_PATTERN = re.compile(r"[-_]")

    def __init__(self, *args, **kwargs):
        # Convert snake_case and kebab-case keys to PascalCase keys
        kwargs = self.convert_keys(**kwargs)
        super().__init__(*args, **kwargs)

    def convert_keys(self, **kwargs) -> dict:
        # Convert snake_case and kebab-case keys to PascalCase keys
        if not kwargs:
            return kwargs
        attributes = self.get_attributes()
        return {
            self._convert_key_with_attrs(k, attributes): v for k, v in kwargs.items()
        }

    def _convert_key_with_attrs(self, key: str, attributes: dict) -> str:
        # Convert snake_case and kebab-case keys to PascalCase keys
        if hasattr(self, key) or key in attributes:
            return key
        words = self._KEY_SPLIT_PATTERN.split(key)
        return "".join(word.capitalize() for word in words)

    def _convert_key(self, key):
        # Legacy method
        attributes = self.get_attributes()
        return self._convert_key_with_attrs(key, attributes)
