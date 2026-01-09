from datetime import datetime

from rest_framework import serializers

from api.constants import CONF_CODE_MAX_LENGTH
from api.validators import (
    username_unique_validator,
    username_validator,
    validate_username_not_me,
)
from reviews.constants import (
    EMAIL_MAX_LENGTH,
    USERNAME_MAX_LENGTH,
)
from reviews.models import Category, Comment, Genre, Review, Title, User


class BaseUserSerializer(serializers.ModelSerializer):
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


class UserMeSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        read_only_fields = ('role',)


class AdminUserSerializer(BaseUserSerializer):
    pass


class GetTokenSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=True, max_length=USERNAME_MAX_LENGTH
    )
    confirmation_code = serializers.CharField(
        required=True, max_length=CONF_CODE_MAX_LENGTH
    )


class SignUpSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=USERNAME_MAX_LENGTH,
        validators=(username_validator, validate_username_not_me),
    )
    email = serializers.EmailField(max_length=EMAIL_MAX_LENGTH)

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')
        errors = {}
        username_user = User.objects.filter(username=username).first()
        if username_user and username_user.email.lower() != email.lower():
            errors['username'] = (
                'Пользователь с таким username уже существует.'
            )
        email_user = User.objects.filter(email__iexact=email).first()
        if email_user and email_user.username != username:
            errors['email'] = 'Пользователь с таким email уже существует.'
        if errors:
            raise serializers.ValidationError(errors)
        return data


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
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if representation['description'] is None:
            representation['description'] = ''
        return representation


class TitleWriteSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field='slug'
    )
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug',
        many=True,
        allow_empty=False,
    )
    year = serializers.IntegerField()

    class Meta:
        model = Title
        fields = '__all__'

    def validate_year(self, value):
        current_year = datetime.now().year
        if value > current_year:
            raise serializers.ValidationError(
                'Год выпуска не может быть больше текущего года.'
            )
        return value

    def to_representation(self, instance):
        if not hasattr(instance, 'rating'):
            instance.rating = None
        return TitleReadSerializer(instance, context=self.context).data


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True
    )

    class Meta:
        model = Review
        exclude = ('title',)

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


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
