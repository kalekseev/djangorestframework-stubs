from collections.abc import Callable, Container, Iterable, MutableMapping
from typing import Any, Protocol, TypeAlias, TypeVar, overload, type_check_only

from django.db.models import Manager, Model, Q, QuerySet
from django_stubs_ext import StrOrPromise
from rest_framework.fields import Field
from rest_framework.serializers import BaseSerializer

_Model = TypeVar("_Model", bound=Model)
_Row = TypeVar("_Row", default=_Model)
_V = TypeVar("_V", contravariant=True)

@type_check_only
class ContextValidator(Protocol[_V]):
    requires_context: bool
    def __call__(self, value: _V, context: Field, /) -> None: ...

Validator: TypeAlias = Callable[[_V], None] | ContextValidator[_V]

def qs_exists(queryset: QuerySet[Any, Any] | Manager[Any]) -> bool: ...
def qs_exists_with_condition(
    queryset: QuerySet[Any, Any] | Manager[Any], condition: Q | None, against: dict[str, Any]
) -> bool: ...
@overload
def qs_filter(queryset: QuerySet[_Model, _Row], **kwargs: Any) -> QuerySet[_Model, _Row]: ...
@overload
def qs_filter(queryset: Manager[_Model], **kwargs: Any) -> QuerySet[_Model]: ...

class UniqueValidator:
    message: StrOrPromise
    requires_context: bool
    queryset: QuerySet[Any, Any] | Manager[Any]
    lookup: str
    def __init__(
        self, queryset: QuerySet[Any, Any] | Manager[Any], message: StrOrPromise | None = None, lookup: str = "exact"
    ) -> None: ...
    @overload
    def filter_queryset(
        self, value: Any, queryset: QuerySet[_Model, _Row], field_name: str
    ) -> QuerySet[_Model, _Row]: ...
    @overload
    def filter_queryset(self, value: Any, queryset: Manager[_Model], field_name: str) -> QuerySet[_Model]: ...
    @overload
    def exclude_current_instance(
        self, queryset: QuerySet[_Model, _Row], instance: _Model | None
    ) -> QuerySet[_Model, _Row]: ...
    @overload
    def exclude_current_instance(self, queryset: Manager[_Model], instance: None) -> Manager[_Model]: ...
    @overload
    def exclude_current_instance(self, queryset: Manager[_Model], instance: _Model) -> QuerySet[_Model]: ...
    def __call__(self, value: Any, serializer_field: Field) -> None: ...

class UniqueTogetherValidator:
    message: StrOrPromise
    missing_message: StrOrPromise
    requires_context: bool
    code: str
    queryset: QuerySet[Any, Any] | Manager[Any]
    fields: Iterable[str]
    def __init__(
        self,
        queryset: QuerySet[Any, Any] | Manager[Any],
        fields: Iterable[str],
        message: StrOrPromise | None = None,
        condition_fields: Iterable[str] | None = None,
        condition: Q | None = None,
        code: str | None = None,
        nulls_distinct: bool | None = None,
    ) -> None: ...
    def enforce_required_fields(self, attrs: Container[str], serializer: BaseSerializer) -> None: ...
    @overload
    def filter_queryset(
        self, attrs: MutableMapping[str, Any], queryset: QuerySet[_Model, _Row], serializer: BaseSerializer
    ) -> QuerySet[_Model, _Row]: ...
    @overload
    def filter_queryset(
        self, attrs: MutableMapping[str, Any], queryset: Manager[_Model], serializer: BaseSerializer
    ) -> QuerySet[_Model]: ...
    @overload
    def exclude_current_instance(
        self, attrs: MutableMapping[str, Any], queryset: QuerySet[_Model, _Row], instance: _Model | None
    ) -> QuerySet[_Model, _Row]: ...
    @overload
    def exclude_current_instance(
        self, attrs: MutableMapping[str, Any], queryset: Manager[_Model], instance: None
    ) -> Manager[_Model]: ...
    @overload
    def exclude_current_instance(
        self, attrs: MutableMapping[str, Any], queryset: Manager[_Model], instance: _Model
    ) -> QuerySet[_Model]: ...
    def __call__(self, attrs: MutableMapping[str, Any], serializer: BaseSerializer) -> None: ...

class ProhibitSurrogateCharactersValidator:
    message: StrOrPromise
    code: str
    def __call__(self, value: Any) -> None: ...

class BaseUniqueForValidator:
    # DISCREPANCY: `message` cannot be None -- None is a placeholder, but subclasses must override this to StrOrPromise
    message: StrOrPromise
    missing_message: StrOrPromise
    requires_context: bool
    queryset: QuerySet[Any, Any] | Manager[Any]
    field: str
    date_field: str
    def __init__(
        self,
        queryset: QuerySet[Any, Any] | Manager[Any],
        field: str,
        date_field: str,
        message: StrOrPromise | None = None,
    ) -> None: ...
    def enforce_required_fields(self, attrs: Container[str]) -> None: ...
    @overload
    def filter_queryset(
        self, attrs: MutableMapping[str, Any], queryset: QuerySet[_Model, _Row], field_name: str, date_field_name: str
    ) -> QuerySet[_Model, _Row]: ...
    @overload
    def filter_queryset(
        self, attrs: MutableMapping[str, Any], queryset: Manager[_Model], field_name: str, date_field_name: str
    ) -> QuerySet[_Model]: ...
    @overload
    def exclude_current_instance(
        self, attrs: MutableMapping[str, Any], queryset: QuerySet[_Model, _Row], instance: _Model | None
    ) -> QuerySet[_Model, _Row]: ...
    @overload
    def exclude_current_instance(
        self, attrs: MutableMapping[str, Any], queryset: Manager[_Model], instance: None
    ) -> Manager[_Model]: ...
    @overload
    def exclude_current_instance(
        self, attrs: MutableMapping[str, Any], queryset: Manager[_Model], instance: _Model
    ) -> QuerySet[_Model]: ...
    def __call__(self, attrs: MutableMapping[str, Any], serializer: BaseSerializer) -> None: ...

class UniqueForDateValidator(BaseUniqueForValidator): ...
class UniqueForMonthValidator(BaseUniqueForValidator): ...
class UniqueForYearValidator(BaseUniqueForValidator): ...
