from django.core.exceptions import ValidationError
import secrets
from datetime import datetime
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from reviews.models import Category, Comment, Genre, Review, Title, User


class UsersSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User (полный доступ для админов)."""

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role'
        )


class NotAdminSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User (ограниченный доступ для обычных пользователей)."""

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role'
        )
        read_only_fields = ('role',)


class GetTokenSerializer(serializers.ModelSerializer):
    """Сериализатор для получения JWT токена."""

    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('username', 'confirmation_code')


class SignUpSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации новых пользователей."""

    def validate_username(self, value):
        if value.lower() == 'me':
            raise serializers.ValidationError(
                'Использовать имя "me" в качестве username запрещено.'
            )
        return value

    def create(self, validated_data):
        """Создание пользователя с генерацией кода подтверждения."""
        # Генерируем 6-значный код из цифр
        validated_data['confirmation_code'] = ''.join(
            secrets.choice('0123456789') for _ in range(6)
        )
        return super().create(validated_data)

    class Meta:
        model = User
        fields = ('email', 'username')


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для модели Category."""

    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Genre."""

    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных модели Title."""

    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(read_only=True, many=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = '__all__'


class TitleWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи данных модели Title."""

    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug'
    )
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug',
        many=True
    )

    def validate_year(self, value):
        current_year = datetime.now().year
        if value > current_year:
            raise serializers.ValidationError(
                'Год выпуска не может быть больше текущего года.'
            )
        return value

    class Meta:
        model = Title
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Review."""

    title = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True
    )
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    def validate_score(self, value):
        """Валидация оценки по 10-балльной шкале."""
        if value < 1 or value > 10:
            raise serializers.ValidationError(
                'Оценка должна быть от 1 до 10!'
            )
        return value

    class Meta:
        model = Review
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Review.objects.all(),
                fields=['title', 'author'],
                message='Вы уже оставили отзыв на это произведение!'
            )
        ]


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Comment."""

    review = serializers.SlugRelatedField(
        slug_field='id',
        read_only=True
    )
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    def validate_text(self, value):
        """Валидация текста комментария."""
        if len(value.strip()) < 1:
            raise serializers.ValidationError(
                'Комментарий не может быть пустым!'
            )
        return value

    class Meta:
        model = Comment
        fields = '__all__'
