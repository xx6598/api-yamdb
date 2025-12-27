from django.contrib.auth import get_user_model
from rest_framework import serializers

from .validators import (username_unique_validator, username_validator,
                         validate_username_not_me)

User = get_user_model()


class UsersSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=150,
        validators=[
            username_validator,
            validate_username_not_me,
            username_unique_validator,
        ],
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "bio",
            "role",
        )


class UsersNotAdminSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=150,
        validators=[
            username_validator,
        ],
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "bio",
            "role",
        )
        read_only_fields = ("role",)


class SignUpSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=254)
    username = serializers.CharField(
        max_length=150,
        validators=[username_validator, validate_username_not_me],
    )

    class Meta:
        model = User
        fields = ("email", "username")


class TokenSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ("username", "confirmation_code")
