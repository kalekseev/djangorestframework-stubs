from typing import assert_type

from rest_framework.request import Request


# case: request_querydict
# `QueryDict`, not django-stubs' `_ImmutableQueryDict`, so the stubs work with django-types.
def some_view(request: Request) -> None:
    assert_type(request.query_params["field"], str | list[object])
    assert_type(request.POST["field"], str | list[object])
