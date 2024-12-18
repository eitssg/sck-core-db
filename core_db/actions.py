""" All table Actions share a CRUD interface and this Model class defines the functions for Create, Read, Update, Delete functions. """
from .response import Response
from .exceptions import NotFoundException


class TableActions(object):
    """
    Base Interface Class API for all table actions for list, get, update, create, delete, and patch
    """

    def __init__(self, *args, **kwargs):
        """
        Base API for all table actions

        This abstraction defining the base API for all table actions.  This allows
        function routers to handle all types of actions for each table
        implementation.

        Lambda Handler event will issue a command to the DB and will route the
        command to the specific table implementation.

        Commands are similar to:

            - item:get
            - item:list
            - item:create
            - item:update

            or

            - event:create
            - event:get
            - event:list

        Where the lambda event.action split(":")[0] is the table short name and the item after
        the colon is the action to perform. (Class method)

        """
        pass

    @classmethod
    def list(cls, **kwargs) -> Response:
        """
        List all items in the table.  Various implmenentations in subclasses
        may behave differently.  Some pay return a list of objects, some may return
        a list of keys.

        Raises:
            NotFoundException: If your subclass has not implmeneted the list method

        Returns:
            Response: :class:`Response` object
        """
        raise NotFoundException("GET list not implemented")

    @classmethod
    def get(cls, **kwargs) -> Response:
        """
        Returns a record from the table by primary hash_key and range_key. The intent
        is to return one and only one unique record.

        Raises:
            NotFoundException: If your subclass has not implmeneted the get method

        Returns:
            Response: :class:`Response` object
        """
        raise NotFoundException("GET not implemented")

    @classmethod
    def create(cls, **kwargs) -> Response:
        """
        Creates a new record in the table.  The primary hash_key and range_key must be provided.

        Other fields may be provided as requred by the table model schema.

        Raises:
            NotFoundException: if your subclass has not implemented the create method

        Returns:
            Response: :class:`Response` object
        """
        raise NotFoundException("POST create not implemented")

    @classmethod
    def update(cls, **kwargs) -> Response:
        """
        Updates a record in the table.  The primary hash_key and range_key must be provided.

        Raises:
            NotFoundException: If your subclass has not implemented the update method

        Returns:
            Response: :class:`Response` object
        """
        raise NotFoundException("PUT update not implemented")

    @classmethod
    def delete(cls, **kwargs) -> Response:
        """
        Deletes a record from the table.  The primary hash_key and range_key must be provided.

        Raises:
            NotFoundException: If your subclass has not implemented the delete method

        Returns:
            Response: :class:`Response` object
        """
        raise NotFoundException("DELETE not implemented")

    @classmethod
    def patch(cls, **kwargs) -> Response:
        """
        Allows you to specify only a partial set of fields to update in a record.

        The effect will be that the full record will be fetched, the fields specified
        will be updated, and the full record will be saved back to the table.

        Some implementations may use the dynamodb PATCH operation to update a field.

        Raises:
            NotFoundException: If your subclass has not implemented the patch method

        Returns:
            Response: :class:`Response` object
        """

        raise NotFoundException("PATCH update not implemented")
