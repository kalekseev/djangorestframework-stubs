from http import HTTPMethod
from typing import Any, TypeGuard, assert_type

from django.http import HttpRequest
from mypy_extensions import Arg
from rest_framework import viewsets
from rest_framework.decorators import ViewSetAction, action, api_view, permission_classes
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView, AsView
from typing_extensions import override


# case: api_view
@api_view()
def view_func1(request: Any) -> Any: ...


view_func1(HttpRequest())
assert_type(view_func1, AsView[[HttpRequest], Any])
assert_type(view_func1(HttpRequest()), Any)


# case: api_view_fancy
@api_view(["GET", "POST"])
def view_func2(request: Request, arg: str) -> Response: ...


view_func2(HttpRequest(), "test")
view_func2(HttpRequest(), arg="test")
assert_type(view_func2, AsView[[HttpRequest, Arg(str, "arg")], Response])
assert_type(view_func2(HttpRequest(), "test"), Response)


# case: permission_classes_with_operators
class Permission(BasePermission):
    pass


permission_classes([IsAuthenticated & Permission])
permission_classes([IsAuthenticated | Permission])
permission_classes([~Permission])


# case: permission_classes_narrowing
class NarrowRequest(Request):
    narrow_attr: int


class IsNarrow(BasePermission):
    @override
    def has_permission(self, request: Request, view: APIView) -> TypeGuard[NarrowRequest]: ...


@permission_classes([IsNarrow])
def narrowed_view(request: NarrowRequest, arg: str) -> Response: ...


request: Request
assert_type(narrowed_view(request, "test"), Response)


@permission_classes((IsNarrow,))
def narrowed_view_wider_request(request: Request) -> Response: ...


assert_type(narrowed_view_wider_request(request), Response)


@permission_classes([IsNarrow])  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
def narrowed_view_unrelated_request(request: int) -> Response: ...


# case: permission_classes_without_narrowing_keeps_view
@permission_classes([AllowAny])
def plain_view(request: NarrowRequest, arg: str) -> Response: ...


narrow_request: NarrowRequest
assert_type(plain_view(narrow_request, "test"), Response)
plain_view(request, "test")  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]


@permission_classes([])
def no_permissions_view(request: NarrowRequest) -> Response: ...


assert_type(no_permissions_view(narrow_request), Response)
no_permissions_view(request)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]


@permission_classes([IsNarrow & AllowAny])
def combined_permissions_view(request: NarrowRequest) -> Response: ...


@api_view(["GET"])
@permission_classes([IsNarrow])
def narrowed_api_view(request: NarrowRequest, arg: str) -> Response: ...


assert_type(narrowed_api_view, AsView[[HttpRequest, Arg(str, "arg")], Response])


@api_view(["GET"])  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
def api_view_narrow_request_without_permission(request: NarrowRequest) -> Response: ...


@api_view(["GET"])  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
@permission_classes([AllowAny])
def api_view_narrow_request_with_plain_permission(request: NarrowRequest) -> Response: ...


# case: method_decorator
class MyView(viewsets.ViewSet):
    @action(methods=("get",), detail=False)
    def view_func_1(self, request: Request) -> Response: ...
    @action(methods=["post"], detail=False)
    def view_func_2(self, request: Request) -> Response: ...
    @action(methods=("GET",), detail=False)
    def view_func_3(self, request: Request) -> Response: ...


assert_type(MyView.view_func_1, ViewSetAction[MyView, [Arg(Request, "request")], Response])
assert_type(MyView().view_func_1(request), Response)


# case: method_decorator_http_libary
MY_VAR: HTTPMethod = HTTPMethod.POST


class MyView2(viewsets.ViewSet):
    @action(methods=[HTTPMethod.GET], detail=False)
    def view_func_1(self, request: Request) -> Response: ...
    @action(methods=[MY_VAR], detail=False)
    def view_func_2(self, request: Request) -> Response: ...
