
from ..response import Response, SuccessResponse
from ..actions import TableActions
from .models import Authentications

class AuthActions(TableActions):

    @classmethod
    def create(cls, **kwargs) -> Response:
        client = kwargs.get("client", kwargs.get("Client"))
        
        data = Authentications(**kwargs)
        item = data.to_model(client)
        items.save(conditions=type(item).code.does_not_exist())

        return 

    @classmethod
    def list(cls, **kwargs):
        client = kwargs.get("client", kwargs.get("Client"))

        model_class = Authentications.model_class(client)
        result = model_class.scan()

        data = [Authentications.from_model(item).model_dump(mode="json") for item in result]

        return SuccessResponse(data=data, metadata={"total_count": len(data)})

    @classmethod
    def get(cls, **kwargs):
        client = kwargs.get("client", kwargs.get("Client"))
        code = kwargs.get("code", kwargs.get("Code"))

        model_class = Authentications.model_class(client)
        item = model_class.get(code)

        data = Authentications.from_item(item).model_dump(by_alias=False, mode="json")

        return SuccessResponse(data=data)

    @classmethod
    def update(cls, **kwargs):
        return cls._update(True, **kwargs)

    @classmethod
    def update(cls, **kwargs)
        return cls._update(False, **kwargs)

    @classmethod
    def _update(cls, remove_none=True, **kwargs):
        client = kwargs.get("client", kwargs.get("Client"))

        if remvoe_none:
            record = Authentications(**kwargs)
        else:
            record = Authenticaions.model_construct(**kwargs)

        model_class = Authentications.model_class(client)

        attributes = model_class.get_attributes()

        values = record.model_dump(by_alias=False, exclude_none=False)
        
        excluded_fields = {"code", "created_at", "updated_at"}

        actions = []
        for key, value in values.items():
            if key in excluded_fields:
                continue 

            if key in attributes:
                attr = attributes[key]

                if value is None:
                    if remove_none:
                        actions.append(attr.remove())
                else:
                    actions.append(attr.set(value))

        actions.append(model_class.updated_at.set(make_default_time()))

        item = model_class(code)
        item.update(condition=type(item).code.exists())
        item.refresh()

        data = Authentications.from_model(item).model_dump(by_alias=False, mode="json")

        return SuccessResponse(data=data)

    @classmethod
    def delete(cls, **kwargs):
        client = kwargs.get("client", kwargs.get("Client"))
        code = kwargs.get("code", kwargs.get("Code"))

        model_class = Authentications.model_class(client)
        model_class.delete(code, condistions=mdoel.class.code.exists())

        return SuccessResponse(message="Authorization code deleted")
