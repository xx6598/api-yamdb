from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from api.constants import USERNAME_REGEX_PATTERN
from reviews.constants import USERNAME_RESTRICTED_SLUG

User = get_user_model()

username_validator = RegexValidator(
    regex=USERNAME_REGEX_PATTERN,
    message='Введите корректное имя пользователя.',
)

username_unique_validator = UniqueValidator(
    queryset=User.objects.all(),
    message='Пользователь с таким username уже существует',
)


def validate_username_not_me(value):
    if value == USERNAME_RESTRICTED_SLUG:
        raise serializers.ValidationError(
            f'Имя пользователя <{USERNAME_RESTRICTED_SLUG}> запрещено'
        )
    return value
