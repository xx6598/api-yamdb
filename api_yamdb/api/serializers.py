import secrets
from datetime import datetime
from typing import Any, Dict

from rest_framework import serializers

from api.constants import (EMAIL_MAX_LENGTH, USERNAME_MAX_LENGTH,
                           CONF_CODE_MAX_LENGTH
                           )
from api.validators import (username_unique_validator, username_validator,
                            validate_username_not_me)
from reviews.models import Category, Comment, Genre, Review, Title, User


class UsersSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=USERNAME_MAX_LENGTH,
        validators=[
            username_validator,
            validate_username_not_me,
            username_unique_validator,
        ],
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if not request.user.is_admin:
                self.fields['role'].read_only = True


class GetTokenSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=True,
        max_length=USERNAME_MAX_LENGTH
    )
    confirmation_code = serializers.CharField(
        required=True,
        max_length=CONF_CODE_MAX_LENGTH
    )


class SignUpSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=USERNAME_MAX_LENGTH,
        validators=(username_validator, validate_username_not_me),
    )
    email = serializers.EmailField(max_length=EMAIL_MAX_LENGTH)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleReadSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(read_only=True, many=True)
    rating = serializers.FloatField(read_only=True)

    def get_rating(self, obj):
        if hasattr(obj, 'rating') and obj.rating is not None:
            return round(float(obj.rating), 1)
        return None

    class Meta:
        model = Title
        fields = '__all__'


class TitleWriteSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field='slug'
    )
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(), slug_field='slug', many=True,
        allow_empty=False
    )
    year = serializers.IntegerField()

    def validate_year(self, value):
        current_year = datetime.now().year
        if value > current_year:
            raise serializers.ValidationError(
                'Год выпуска не может быть больше текущего года.'
            )
        return value

    def to_representation(self, instance):
        return TitleReadSerializer(instance, context=self.context).data

    class Meta:
        model = Title
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True
    )

    def validate(self, data):
        request = self.context.get('request')
        view = self.context.get('view')

        if request and view and request.method == 'POST':
            title_pk = view.kwargs.get('title_pk')
            if title_pk and request.user:
                if Review.objects.filter(
                        author=request.user, title_id=title_pk
                ).exists():
                    raise serializers.ValidationError(
                        'Вы уже оставили отзыв на это произведение!'
                    )
        return data

    class Meta:
        model = Review
        exclude = ('title',)


class CommentSerializer(serializers.ModelSerializer):
    review = serializers.SlugRelatedField(slug_field='id', read_only=True)
    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True
    )

    class Meta:
        model = Comment
        fields = '__all__'
