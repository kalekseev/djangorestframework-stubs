import sys
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Concatenate, Literal, Protocol, TypeAlias, TypeVar, overload

from django.http import HttpRequest
from django.http.response import HttpResponseBase
from rest_framework.authentication import BaseAuthentication
from rest_framework.metadata import BaseMetadata
from rest_framework.negotiation import BaseContentNegotiation
from rest_framework.parsers import BaseParser
from rest_framework.permissions import _PermissionClass
from rest_framework.renderers import BaseRenderer
from rest_framework.request import Request
from rest_framework.schemas.inspectors import ViewInspector
from rest_framework.throttling import BaseThrottle
from rest_framework.versioning import BaseVersioning
from rest_framework.views import APIView, AsView  # noqa: F401
from typing_extensions import ParamSpec, Self, override

_P = ParamSpec("_P")
_Owner = TypeVar("_Owner")
_Owner_contra = TypeVar("_Owner_contra", contravariant=True)
_RESP = TypeVar("_RESP", bound=HttpResponseBase)
_RESP_co = TypeVar("_RESP_co", bound=HttpResponseBase, covariant=True)
_REQ = TypeVar("_REQ", bound=Request)
_View = TypeVar("_View", bound=Callable[..., HttpResponseBase])

_MixedCaseHttpMethod: TypeAlias = Literal[
    "GET",
    "POST",
    "DELETE",
    "PUT",
    "PATCH",
    "TRACE",
    "HEAD",
    "OPTIONS",
    "get",
    "post",
    "delete",
    "put",
    "patch",
    "trace",
    "head",
    "options",
]
if sys.version_info >= (3, 11):
    from http import HTTPMethod

    _HttpMethod: TypeAlias = _MixedCaseHttpMethod | HTTPMethod
else:
    _HttpMethod: TypeAlias = _MixedCaseHttpMethod

class MethodMapper(dict):
    def __init__(self, action: _View, methods: Sequence[str]) -> None: ...
    def _map(self, method: str, func: _View) -> _View: ...
    @override
    def get(self, func: _View) -> _View: ...  # type: ignore[override]
    def post(self, func: _View) -> _View: ...
    def put(self, func: _View) -> _View: ...
    def patch(self, func: _View) -> _View: ...
    def delete(self, func: _View) -> _View: ...
    def head(self, func: _View) -> _View: ...
    def options(self, func: _View) -> _View: ...
    def trace(self, func: _View) -> _View: ...

class ViewSetAction(Protocol[_Owner_contra, _P, _RESP_co]):
    detail: bool
    url_path: str
    url_name: str
    kwargs: Mapping[str, Any]
    mapping: MethodMapper
    def __call__(self, instance: _Owner_contra, /, *args: _P.args, **kwargs: _P.kwargs) -> _RESP_co: ...
    @overload
    def __get__(self, instance: None, owner: type[Any], /) -> Self: ...
    @overload
    def __get__(
        self, instance: _Owner_contra, owner: type[_Owner_contra] | None = ..., /
    ) -> Callable[_P, _RESP_co]: ...
    __name__: str

def api_view(
    http_method_names: Sequence[str] | None = ...,
) -> Callable[[Callable[Concatenate[_REQ, _P], _RESP]], AsView[Concatenate[HttpRequest, _P], _RESP]]: ...
def renderer_classes(renderer_classes: Sequence[BaseRenderer | type[BaseRenderer]]) -> Callable[[_View], _View]: ...
def parser_classes(parser_classes: Sequence[BaseParser | type[BaseParser]]) -> Callable[[_View], _View]: ...
def authentication_classes(
    authentication_classes: Sequence[BaseAuthentication | type[BaseAuthentication]],
) -> Callable[[_View], _View]: ...
def throttle_classes(throttle_classes: Sequence[BaseThrottle | type[BaseThrottle]]) -> Callable[[_View], _View]: ...
def permission_classes(permission_classes: Sequence[_PermissionClass]) -> Callable[[_View], _View]: ...
def content_negotiation_class(content_negotiation_class: type[BaseContentNegotiation]) -> Callable[[_View], _View]: ...
def metadata_class(metadata_class: type[BaseMetadata] | None) -> Callable[[_View], _View]: ...
def versioning_class(versioning_class: type[BaseVersioning] | None) -> Callable[[_View], _View]: ...
def schema(view_inspector: ViewInspector | type[ViewInspector] | None) -> Callable[[_View], _View]: ...
def action(
    methods: Sequence[_HttpMethod] | None = ...,
    detail: bool = ...,
    url_path: str | None = ...,
    url_name: str | None = ...,
    suffix: str | None = ...,
    name: str | None = ...,
    **kwargs: Any,
) -> Callable[[Callable[Concatenate[_Owner, _P], _RESP]], ViewSetAction[_Owner, _P, _RESP]]: ...
