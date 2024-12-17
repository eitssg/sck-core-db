from .response import Response
from .exceptions import NotFoundException


class TableActions:
    """Base API for all table actions"""

    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    def list(cls, **kwargs) -> Response:
        raise NotFoundException("GET list not implemented")

    @classmethod
    def get(cls, **kwargs) -> Response:
        raise NotFoundException("GET not implemented")

    @classmethod
    def create(cls, **kwargs) -> Response:
        raise NotFoundException("POST create not implemented")

    @classmethod
    def update(cls, **kwargs) -> Response:
        raise NotFoundException("PUT update not implemented")

    @classmethod
    def delete(cls, **kwargs) -> Response:
        raise NotFoundException("DELETE not implemented")

    @classmethod
    def patch(cls, **kwargs) -> Response:
        raise NotFoundException("PATCH update not implemented")
