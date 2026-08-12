from collections.abc import MutableMapping
from typing import Any, Concatenate

from django.http import HttpRequest
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView, AsView

class ObtainAuthToken(APIView):
    serializer_class: type[Serializer]
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response: ...
    def get_serializer_context(self) -> MutableMapping[str, Any]: ...
    def get_serializer(self, *args: Any, **kwargs: Any) -> Serializer: ...

obtain_auth_token: AsView[Concatenate[HttpRequest, ...], Response]
