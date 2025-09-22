from typing import Optional, Any, Tuple

from pydantic import Field, ConfigDict

from pynamodb.attributes import (
    UnicodeAttribute,
    ListAttribute,
    MapAttribute,
    NumberAttribute,
)
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.exceptions import (
    DoesNotExist,
    GetError,
    PutError,
    DeleteError,
    QueryError,
)

from core_db.exceptions import NotFoundException, UnknownException, ConflictException


from ..models import DatabaseRecord, DatabaseTable, Paginator, TableFactory
from ..actions import TableActions


class AuditByActorIndex(GlobalSecondaryIndex):
    """GSI for querying audit events by actor with time ordering via SK."""

    class Meta:
        index_name = "actor-index"
        projection = AllProjection()
        billing_mode = "PAY_PER_REQUEST"

    actor_user_id = UnicodeAttribute(hash_key=True, attr_name="ActorUserId")
    sk = UnicodeAttribute(range_key=True, attr_name="SK")


class AuditByChangeTypeIndex(GlobalSecondaryIndex):
    """GSI for querying audit events by change type with time ordering via SK."""

    class Meta:
        index_name = "change-type-index"
        projection = AllProjection()
        billing_mode = "PAY_PER_REQUEST"

    change_type = UnicodeAttribute(hash_key=True, attr_name="ChangeType")
    sk = UnicodeAttribute(range_key=True, attr_name="SK")


class AuditByRequestIdIndex(GlobalSecondaryIndex):
    """GSI for retrieving audit events by request correlation id."""

    class Meta:
        index_name = "request-id-index"
        projection = AllProjection()
        billing_mode = "PAY_PER_REQUEST"

    request_id = UnicodeAttribute(hash_key=True, attr_name="RequestId")


class AuthAuditModel(DatabaseTable):
    """PynamoDB model for authorization audit events.

    PK format: tenant#<tenant_slug>#user#<user_id>
    SK format: ts#<ISO8601>|<epoch>#<nonce> (lexicographically sortable for time ordering)

    GSIs:
      - actor-index:    actor_user_id → SK (time-ordered per actor)
      - change-type-index: change_type → SK (time-ordered per change type)
      - request-id-index: request_id (fetch by correlation id)
    """

    class Meta(DatabaseTable.Meta):
        pass

    # Primary keys
    pk = UnicodeAttribute(hash_key=True, attr_name="PK")
    sk = UnicodeAttribute(range_key=True, attr_name="SK")

    # Core attributes
    actor_user_id = UnicodeAttribute(null=True, attr_name="ActorUserId")
    change_type = UnicodeAttribute(null=True, attr_name="ChangeType")
    before_hash = UnicodeAttribute(null=True, attr_name="BeforeHash")
    after_hash = UnicodeAttribute(null=True, attr_name="AfterHash")

    role_additions = ListAttribute(of=UnicodeAttribute, null=True, attr_name="RoleAdditions")
    role_removals = ListAttribute(of=UnicodeAttribute, null=True, attr_name="RoleRemovals")

    grant_additions = ListAttribute(of=MapAttribute, null=True, attr_name="GrantAdditions")
    grant_removals = ListAttribute(of=MapAttribute, null=True, attr_name="GrantRemovals")

    deny_additions = ListAttribute(of=MapAttribute, null=True, attr_name="DenyAdditions")
    deny_removals = ListAttribute(of=MapAttribute, null=True, attr_name="DenyRemovals")

    reason = UnicodeAttribute(null=True, attr_name="Reason")
    request_id = UnicodeAttribute(null=True, attr_name="RequestId")

    # Optional TTL support
    expire_at = NumberAttribute(null=True, attr_name="ExpireAt")

    # Indexes
    by_actor_index = AuditByActorIndex()
    by_change_type_index = AuditByChangeTypeIndex()
    by_request_id_index = AuditByRequestIdIndex()

    def __repr__(self) -> str:
        return f"<AuthAuditModel(pk={self.pk}, sk={self.sk}, change_type={self.change_type})>"


AuthAuditModelType = type[AuthAuditModel]


class AuthAuditModelFactory:
    """Factory for creating client-scoped AuthAuditModel tables and models.

    Why?  This module supports Multi-Tenancy by allowing each client to have its own table.

    PynamoDB models are tied to a specific table name at class definition time,
    so we need a factory to create per-client subclasses with the appropriate table name.

    """

    @classmethod
    def get_model(cls, client: str) -> AuthAuditModelType:
        return TableFactory.get_model(AuthAuditModel, client=client)

    @classmethod
    def create_table(cls, client: str, wait: bool = True) -> bool:
        return TableFactory.create_table(AuthAuditModel, client, wait=wait)

    @classmethod
    def delete_table(cls, client: str, wait: bool = True) -> bool:
        return TableFactory.delete_table(AuthAuditModel, client, wait=wait)

    @classmethod
    def exists(cls, client: str) -> bool:
        return TableFactory.exists(AuthAuditModel, client)


class AuthAuditSchemas(DatabaseRecord):
    """Pydantic record for authorization audit events (validation + serialization).

    Notes:
    - All mutation list fields default to empty arrays to simplify diffs and queries
    - Optional fields may be omitted by writers (e.g., before/after hash on create)
    - Keys use simple snake_case (no aliases) for internal DB serialization
    """

    model_config = ConfigDict(populate_by_name=True)

    pk: str = Field(..., description="Partition key, e.g. tenant#<tenant_slug>#user#<user_id>")
    sk: str = Field(..., description="Sort key, e.g. ts#<ISO8601>#<short-uuid>")

    actor_user_id: Optional[str] = Field(None, description="ID (email) of actor performing the change")
    change_type: Optional[str] = Field(None, description="Type of change, e.g. permissions.update")

    before_hash: Optional[str] = Field(None, description="Hash of effective state before the change")
    after_hash: Optional[str] = Field(None, description="Hash of effective state after the change")

    role_additions: list[str] = Field(default_factory=list, description="Roles added")
    role_removals: list[str] = Field(default_factory=list, description="Roles removed")

    grant_additions: list[dict[str, Any]] = Field(default_factory=list, description="Grants added")
    grant_removals: list[dict[str, Any]] = Field(default_factory=list, description="Grants removed")

    deny_additions: list[dict[str, Any]] = Field(default_factory=list, description="Denies added")
    deny_removals: list[dict[str, Any]] = Field(default_factory=list, description="Denies removed")

    reason: Optional[str] = Field(None, description="Reason/comment for the change")
    request_id: Optional[str] = Field(None, description="Request correlation id (if available)")
    expire_at: Optional[int] = Field(
        None,
        description="Optional UNIX epoch seconds for TTL expiry (DynamoDB TTL)",
    )

    @classmethod
    def from_model(cls, model: AuthAuditModel) -> "AuthAuditSchemas":
        return cls(**model.to_simple_dict())

    def to_model(self, client: str) -> AuthAuditModel:
        model_cls = AuthAuditModelFactory.get_model(client)
        return model_cls(**self.model_dump())


class AuthAuditActions(TableActions):

    @classmethod
    def get(*, client: str, pk: str, sk: str) -> Optional[AuthAuditSchemas]:

        try:
            model_cls = AuthAuditModelFactory.get_model(client)
            item = model_cls.get(pk, sk)

            return AuthAuditSchemas.from_model(item)

        except DoesNotExist:
            raise NotFoundException("Audit record not found")
        except (Exception, GetError) as e:
            raise UnknownException(str(e)) from e

    @classmethod
    def create(cls, *, client: str, record: AuthAuditSchemas) -> AuthAuditSchemas:
        """
        Create a new audit record.

        Args:
            client (str): The client identifier for which the audit record is being created.
            record (AuthAuditSchemas): The audit record data to create.

        Returns:
            AuthAuditSchemas: The created audit record.

        Raises:
            UnknownException: If there is an error creating the audit record.
        """

        model_cls = AuthAuditModelFactory.get_model(client)

        try:

            item = record.to_model(client)
            item.save(condition=model_cls.pk.does_not_exist() & model_cls.sk.does_not_exist())

            return AuthAuditSchemas.from_model(item)

        except PutError as e:
            if "ConditionalCheckFailedException" in str(e):
                raise ConflictException("Audit record already exists") from e
            raise UnknownException(str(e)) from e
        except Exception as e:
            raise UnknownException(str(e)) from e

    @classmethod
    def query_by_actor(cls, *, client: str, actor_user_id: str, limit: int = 50) -> Tuple[list[AuthAuditSchemas], Paginator]:

        try:
            model_cls = AuthAuditModelFactory.get_model(client)

            paginator = Paginator(limit=limit)

            result = model_cls.by_actor_index.query(actor_user_id, **paginator.get_query_args())

            results = []
            for item in result:
                results.append(AuthAuditSchemas.from_model(item))
            paginator.last_evaluated_key = getattr(result, "last_evaluated_key", None)
            paginator.total_count = len(results)

            return results, paginator

        except DoesNotExist:
            raise NotFoundException("Audit record not found")

        except (Exception, QueryError) as e:
            raise UnknownException(str(e)) from e

    @classmethod
    def query_by_change_type(cls, *, client: str, change_type: str, limit: int = 50) -> Tuple[list[AuthAuditSchemas], Paginator]:
        try:
            model_cls = AuthAuditModelFactory.get_model(client)

            paginator = Paginator(limit=limit)

            result = model_cls.by_change_type_index.query(change_type, **paginator.get_query_args())

            results = []
            for item in result:
                results.append(AuthAuditSchemas.from_model(item))

            paginator.last_evaluated_key = getattr(result, "last_evaluated_key", None)
            paginator.total_count = len(results)

            return results, paginator
        except Exception as e:
            raise UnknownException(str(e)) from e

    @classmethod
    def query_by_request_id(cls, *, client: str, request_id: str) -> list[AuthAuditSchemas]:
        model_cls = AuthAuditModelFactory.get_model(client)

        try:
            paginator = Paginator()

            # don't use paginator here, just return all matching records for the request_id
            result = model_cls.by_request_id_index.query(request_id)

            results = []
            for item in result:
                results.append(AuthAuditSchemas.from_model(item))

            paginator.last_evaluated_key = getattr(result, "last_evaluated_key", None)
            paginator.total_count = len(results)

            return results, paginator

        except Exception as e:
            raise UnknownException(str(e)) from e

    @classmethod
    def list_all(cls, *, client: str, limit: int = 50) -> Tuple[list[AuthAuditSchemas], Paginator]:

        try:
            model_cls = AuthAuditModelFactory.get_model(client)
            paginator = Paginator(limit=limit)

            result = model_cls.scan(**paginator.get_scan_args())

            results = []
            for item in result:
                results.append(AuthAuditSchemas.from_model(item))

            paginator.last_evaluated_key = getattr(result, "last_evaluated_key", None)
            paginator.total_count = len(results)

            return results, paginator

        except Exception as e:
            raise UnknownException(str(e)) from e

    @classmethod
    def delete(cls, *, client: str, pk: str, sk: str) -> bool:

        model_cls = AuthAuditModelFactory.get_model(client)

        try:
            item = model_cls(pk, sk)
            item.delete(condition=model_cls.pk.exists() & model_cls.sk.exists())
            return True

        except DeleteError as e:
            if "ConditionalCheckFailedException" in str(e):
                raise NotFoundException("Audit record not found") from e
            raise UnknownException(str(e)) from e
        except Exception as e:
            raise UnknownException("Audit record delete failed") from e

    @classmethod
    def update(cls, *, client: str, record: AuthAuditSchemas) -> Optional[AuthAuditSchemas]:

        model_cls = AuthAuditModelFactory.get_model(client)

        try:

            item = record.to_model(client)
            item.save(conditions=model_cls.pk.exists() & model_cls.sk.exists())

            return record

        except PutError as e:
            if "ConditionalCheckFailedException" in str(e):
                raise NotFoundException("Audit record not found") from e
            raise UnknownException(str(e)) from e
        except Exception as e:
            raise UnknownException("Audit record update failed") from e
