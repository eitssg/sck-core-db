"""All table Actions share a CRUD interface and this Model class defines the functions for Create, Read, Update, Delete functions."""

from typing import Protocol

from .response import Response


class TableActions(Protocol):
    """
    Base Interface Protocol API for all table actions for list, get, update, create, delete, and patch.

    This protocol defines the standard CRUD interface that all table action classes must implement.
    It allows function routers to handle all types of actions for each table implementation
    in a type-safe manner.

    Lambda Handler events issue commands to the DB and route the command to the specific
    table implementation based on the action format.

    Command Format
    --------------
    Commands follow the pattern: ``{table}:{action}``

    Examples::

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

    Where ``lambda event.action.split(":")[0]`` is the table short name and the item after
    the colon is the action to perform (class method).

    Required Methods
    ----------------
    All implementing classes must provide these class methods:

    - **list(cls, \\**kwargs) -> Response**: List all items in the table
    - **get(cls, \\**kwargs) -> Response**: Get a specific item by primary key
    - **create(cls, \\**kwargs) -> Response**: Create a new item in the table
    - **update(cls, \\**kwargs) -> Response**: Update an existing item completely
    - **delete(cls, \\**kwargs) -> Response**: Delete an item from the table
    - **patch(cls, \\**kwargs) -> Response**: Partially update specific fields

    Usage Example
    -------------
    ::

        from typing import Type
        from core_db.actions import TableActions

        def handle_action(action_class: Type[TableActions], operation: str, **kwargs):
            if operation == "list":
                return action_class.list(**kwargs)
            elif operation == "get":
                return action_class.get(**kwargs)
            elif operation == "create":
                return action_class.create(**kwargs)
            # ... etc

        # Any class implementing the protocol works:
        from core_db.registry.portfolio.actions import PortfolioActions
        result = handle_action(PortfolioActions, "list", client="acme")

    Implementation Example
    ----------------------
    ::

        class MyTableActions:
            '''Automatically conforms to TableActions protocol'''

            @classmethod
            def list(cls, **kwargs) -> Response:
                # Implementation here
                return SuccessResponse([])

            @classmethod
            def get(cls, **kwargs) -> Response:
                # Implementation here
                return SuccessResponse({})

            # ... implement other required methods

    Notes
    -----
    - This is a Protocol, so classes don't need to explicitly inherit from it
    - Type checkers will verify that implementing classes have all required methods
    - All methods are class methods that accept **kwargs and return Response objects
    - Structural typing allows duck typing while maintaining type safety
    """

    @classmethod
    def list(cls, **kwargs) -> Response:
        """
        List all items in the table.  Various implementations in subclasses
        may behave differently.  Some may return a list of objects, some may return
        a list of keys.

        :param kwargs: Implementation-specific parameters
        :returns: Response object
        :rtype: Response
        :raises NotFoundException: If your subclass has not implemented the list method
        """
        ...

    @classmethod
    def get(cls, **kwargs) -> Response:
        """
        Returns a record from the table by primary hash_key and range_key. The intent
        is to return one and only one unique record.

        :param kwargs: Implementation-specific parameters including hash_key and range_key
        :returns: Response object
        :rtype: Response
        :raises NotFoundException: If your subclass has not implemented the get method
        """
        ...

    @classmethod
    def create(cls, **kwargs) -> Response:
        """
        Creates a new record in the table.  The primary hash_key and range_key must be provided.

        Other fields may be provided as required by the table model schema.

        :param kwargs: Record data including hash_key, range_key, and other fields
        :returns: Response object
        :rtype: Response
        :raises NotFoundException: If your subclass has not implemented the create method
        """
        ...

    @classmethod
    def update(cls, **kwargs) -> Response:
        """
        Updates a record in the table.  The primary hash_key and range_key must be provided.

        :param kwargs: Record data including hash_key, range_key, and fields to update
        :returns: Response object
        :rtype: Response
        :raises NotFoundException: If your subclass has not implemented the update method
        """
        ...

    @classmethod
    def delete(cls, **kwargs) -> Response:
        """
        Deletes a record from the table.  The primary hash_key and range_key must be provided.

        :param kwargs: Parameters including hash_key and range_key of record to delete
        :returns: Response object
        :rtype: Response
        :raises NotFoundException: If your subclass has not implemented the delete method
        """
        ...

    @classmethod
    def patch(cls, **kwargs) -> Response:
        """
        Allows you to specify only a partial set of fields to update in a record.

        The effect will be that the full record will be fetched, the fields specified
        will be updated, and the full record will be saved back to the table.

        Some implementations may use the dynamodb PATCH operation to update a field.

        :param kwargs: Parameters including hash_key, range_key, and partial field updates
        :returns: Response object
        :rtype: Response
        :raises NotFoundException: If your subclass has not implemented the patch method
        """
        ...
