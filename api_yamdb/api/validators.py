from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

User = get_user_model()

username_validator = RegexValidator(
    regex=r"^[\w.@+-]+\Z", message="Введите корректное имя пользователя."
)

username_unique_validator = UniqueValidator(
    queryset=User.objects.all(),
    message="Пользователь с таким username уже существует",
)


def validate_username_not_me(value):
    if value.lower() == "me":
        raise serializers.ValidationError("Имя пользователя <me> запрещено")
    return value
