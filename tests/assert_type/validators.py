from typing import Any, assert_type

from django.contrib.auth.models import User
from django.db.models import Manager, Q, QuerySet
from rest_framework.serializers import BaseSerializer
from rest_framework.validators import (
    UniqueForDateValidator,
    UniqueForMonthValidator,
    UniqueForYearValidator,
    UniqueTogetherValidator,
    UniqueValidator,
    qs_exists,
    qs_exists_with_condition,
    qs_filter,
)


def queryset_inputs(values_qs: QuerySet[User, dict[str, Any]], validator: UniqueValidator, instance: User) -> None:
    # Preserve model and row types through filtering and exclusion.
    assert_type(qs_filter(values_qs, pk=1), QuerySet[User, dict[str, Any]])
    assert_type(validator.filter_queryset("value", values_qs, "name"), QuerySet[User, dict[str, Any]])
    assert_type(validator.exclude_current_instance(values_qs, instance), QuerySet[User, dict[str, Any]])


def manager_inputs(
    manager: Manager[User], serializer: BaseSerializer[User], user: User, values_qs: QuerySet[User, dict[str, Any]]
) -> None:
    assert_type(qs_exists(manager), bool)
    assert_type(qs_exists_with_condition(manager, Q(pk=1), {"pk": 1}), bool)
    assert_type(qs_filter(manager, pk=1), QuerySet[User])

    unique = UniqueValidator(manager)
    assert_type(unique.filter_queryset("name", manager, "username"), QuerySet[User])
    assert_type(unique.exclude_current_instance(manager, None), Manager[User])
    assert_type(unique.exclude_current_instance(manager, user), QuerySet[User])
    assert_type(unique.exclude_current_instance(values_qs, None), QuerySet[User, dict[str, Any]])

    together = UniqueTogetherValidator(manager, ("username", "email"))
    # Upstream Django stubs also bind Manager.__get__ on plain instances, so
    # check the stored attribute's declared type without that descriptor artifact.
    UniqueTogetherValidator.queryset = manager
    assert_type(together.filter_queryset({}, manager, serializer), QuerySet[User])
    assert_type(together.exclude_current_instance({}, manager, None), Manager[User])
    assert_type(together.exclude_current_instance({}, manager, user), QuerySet[User])

    for validator in (
        UniqueForDateValidator(manager, "username", "last_login"),
        UniqueForMonthValidator(manager, "username", "last_login"),
        UniqueForYearValidator(manager, "username", "last_login"),
    ):
        assert_type(validator.filter_queryset({}, manager, "username", "last_login"), QuerySet[User])
        assert_type(validator.exclude_current_instance({}, manager, None), Manager[User])
        assert_type(validator.exclude_current_instance({}, manager, user), QuerySet[User])
