"""All table Actions share a CRUD interface and this Model class defines the functions for Create, Read, Update, Delete functions."""

from typing import Protocol, Any


class TableActions(Protocol):
    """Base Interface Protocol API for all table actions for list, get, update, create, delete, and patch.

    This protocol defines the standard CRUD interface that all table action classes must implement.
    It allows function routers to handle all types of actions for each table implementation
    in a type-safe manner.

    Lambda Handler events issue commands to the DB and route the command to the specific
    table implementation based on the action format.

    Note:
        **Command Format**: Commands follow the pattern: `{table}:{action}`

        Examples:
        - item:get
        - item:list
        - item:create
        - item:update
        - item:delete
        - item:patch
        - event:create
        - event:get
        - event:list
        - portfolio:create
        - portfolio:list
        - zone:get

        Where `lambda event.action.split(":")[0]` is the table short name and the item after
        the colon is the action to perform (class method).

        **Required Methods**: All implementing classes must provide these class methods:

        - **list(cls, \\**kwargs)**: List all items in the table
        - **get(cls, \\**kwargs)**: Get a specific item by primary key
        - **create(cls, \\**kwargs)**: Create a new item in the table
        - **update(cls, \\**kwargs)**: Update an existing item completely
        - **delete(cls, \\**kwargs)**: Delete an item from the table
        - **patch(cls, \\**kwargs)**: Partially update specific fields

        **Protocol Benefits**:
        - This is a Protocol, so classes don't need to explicitly inherit from it
        - Type checkers will verify that implementing classes have all required methods
        - All methods are class methods that accept **kwargs and return target objects
        - Structural typing allows duck typing while maintaining type safety

    Examples:
        >>> from typing import Type
        >>> from core_db.actions import TableActions

        >>> def handle_action(action_class: Type[TableActions], operation: str, **kwargs):
        ...     if operation == "list":
        ...         return action_class.list(**kwargs)
        ...     elif operation == "get":
        ...         return action_class.get(**kwargs)
        ...     elif operation == "create":
        ...         return action_class.create(**kwargs)
        ...     # ... etc

        >>> # Any class implementing the protocol works:
        >>> from core_db.registry.portfolio.actions import PortfolioActions
        >>> result = handle_action(PortfolioActions, "list", client="acme")

    """

    @classmethod
    def list(cls, **kwargs) -> Any:
        """List all items in the table.

        Various implementations in subclasses may behave differently. Some may return
        a list of objects, some may return a list of keys.

        Args:
            **kwargs: Implementation-specific parameters. Common parameters include:
                - client (str): Client identifier for client-specific tables
                - limit (int): Maximum number of items to return
                - offset (int): Number of items to skip for pagination
                - filters (dict): Query filters for result filtering

        Returns:
            BaseModel object containing the list of items or an error

        Raises:
            NotFoundException: If your subclass has not implemented the list method

        Examples:
            >>> # List all portfolios for a client
            >>> response = PortfolioActions.list(client="acme")

            >>> # List with pagination
            >>> response = ItemActions.list(limit=10, offset=20)

            >>> # List with filters
            >>> response = ZoneActions.list(client="acme", environment="prod")
        """
        ...

    @classmethod
    def get(cls, **kwargs) -> Any:
        """Returns a record from the table by primary hash_key and range_key.

        The intent is to return one and only one unique record.

        Args:
            **kwargs: Implementation-specific parameters including:
                - hash_key: Primary hash key value (required)
                - range_key: Primary range key value (required for composite keys)
                - client (str): Client identifier for client-specific tables
                - Additional parameters specific to the table implementation

        Returns:
            BaseModel object containing the requested item or an error

        Raises:
            NotFoundException: If your subclass has not implemented the get method
            ItemNotFoundException: If the requested item doesn't exist

        Examples:
            >>> # Get a portfolio by client and portfolio name
            >>> response = PortfolioActions.get(client="acme", portfolio="web-services")

            >>> # Get a zone by client and zone name
            >>> response = ZoneActions.get(client="acme", zone="production-east")

            >>> # Get an item by ID
            >>> response = ItemActions.get(id="12345")
        """
        ...

    @classmethod
    def create(cls, **kwargs) -> Any:
        """Creates a new record in the table.

        The primary hash_key and range_key must be provided. Other fields may be
        provided as required by the table model schema.

        Args:
            **kwargs: Record data including:
                - hash_key: Primary hash key value (required)
                - range_key: Primary range key value (required for composite keys)
                - Additional fields as defined by the table model schema
                - client (str): Client identifier for client-specific tables

        Returns:
            BaseModel: BaseModel object containing the created item or an error

        Raises:
            NotFoundException: If your subclass has not implemented the create method
            ValidationError: If the provided data doesn't meet schema requirements
            ConflictError: If an item with the same primary key already exists

        Examples:
            >>> # Create a new portfolio
            >>> response = PortfolioActions.create(
            ...     client="acme",
            ...     portfolio="new-service",
            ...     domain="newservice.acme.com",
            ...     owner={"name": "John Doe", "email": "john@acme.com"}
            ... )

            >>> # Create a new zone
            >>> response = ZoneActions.create(
            ...     client="acme",
            ...     zone="staging-west",
            ...     account_facts={"aws_account_id": "123456789012"},
            ...     region_facts={"us-west-2": {"aws_region": "us-west-2"}}
            ... )
        """
        ...

    @classmethod
    def update(cls, **kwargs) -> Any:
        """Updates a record in the table.

        The primary hash_key and range_key must be provided. This performs a complete
        update of the record, replacing all fields with the provided values.

        Args:
            **kwargs: Record data including:
                - hash_key: Primary hash key value (required)
                - range_key: Primary range key value (required for composite keys)
                - All fields that should be updated in the record
                - client (str): Client identifier for client-specific tables

        Returns:
            BaseModel: BaseModel object containing the updated item or an error

        Raises:
            NotFoundException: If your subclass has not implemented the update method
            ItemNotFoundException: If the item to update doesn't exist
            ValidationError: If the provided data doesn't meet schema requirements

        Examples:
            >>> # Update a portfolio completely
            >>> response = PortfolioActions.update(
            ...     client="acme",
            ...     portfolio="web-services",
            ...     domain="webservices.acme.com",
            ...     owner={"name": "Jane Smith", "email": "jane@acme.com"},
            ...     tags={"Environment": "production"}
            ... )

            >>> # Update a zone configuration
            >>> response = ZoneActions.update(
            ...     client="acme",
            ...     zone="production-east",
            ...     account_facts={"aws_account_id": "123456789012"},
            ...     region_facts={"us-east-1": {"aws_region": "us-east-1", "az_count": 3}}
            ... )
        """
        ...

    @classmethod
    def delete(cls, **kwargs) -> bool:
        """Deletes a record from the table.

        The primary hash_key and range_key must be provided.

        Args:
            **kwargs: Parameters including:
                - hash_key: Primary hash key value (required)
                - range_key: Primary range key value (required for composite keys)
                - client (str): Client identifier for client-specific tables
                - force (bool): Force deletion even if dependent resources exist

        Returns:
            BaseModel: BaseModel object confirming deletion or an error

        Raises:
            NotFoundException: If your subclass has not implemented the delete method
            ItemNotFoundException: If the item to delete doesn't exist
            ConflictError: If the item cannot be deleted due to dependencies

        Examples:
            >>> # Delete a portfolio
            >>> response = PortfolioActions.delete(client="acme", portfolio="old-service")

            >>> # Delete a zone
            >>> response = ZoneActions.delete(client="acme", zone="deprecated-zone")

            >>> # Force delete (bypass dependency checks)
            >>> response = ItemActions.delete(id="12345", force=True)
        """
        ...

    @classmethod
    def patch(cls, **kwargs) -> Any:
        """Allows you to specify only a partial set of fields to update in a record.

        The effect will be that the full record will be fetched, the fields specified
        will be updated, and the full record will be saved back to the table.
        Some implementations may use the DynamoDB PATCH operation to update a field.

        Args:
            **kwargs: Parameters including:
                - hash_key: Primary hash key value (required)
                - range_key: Primary range key value (required for composite keys)
                - Partial field updates (only the fields to be changed)
                - client (str): Client identifier for client-specific tables

        Returns:
            BaseModel: BaseModel object containing the patched item or an error

        Raises:
            NotFoundException: If your subclass has not implemented the patch method
            ItemNotFoundException: If the item to patch doesn't exist
            ValidationError: If the provided patch data is invalid

        Examples:
            >>> # Patch only the domain field of a portfolio
            >>> response = PortfolioActions.patch(
            ...     client="acme",
            ...     portfolio="web-services",
            ...     domain="newdomain.acme.com"
            ... )

            >>> # Patch only specific tags
            >>> response = ZoneActions.patch(
            ...     client="acme",
            ...     zone="production-east",
            ...     tags={"Owner": "platform-team", "CostCenter": "engineering"}
            ... )

            >>> # Patch nested fields
            >>> response = PortfolioActions.patch(
            ...     client="acme",
            ...     portfolio="web-services",
            ...     owner={"email": "newemail@acme.com"}
            ... )
        """
        ...
