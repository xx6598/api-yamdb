from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from api.constants import SCORE_MAX_VALUE, SCORE_MIN_VALUE, USERNAME_MAX_LENGTH
from reviews.constants import (CATEGORY_NAME_MAX_LENGTH,
                               FIRST_NAME_MAX_LENGTH, GENRE_NAME_MAX_LENGTH,
                               LAST_NAME_MAX_LENGTH, TITLE_NAME_MAX_LENGTH)
from reviews.validators import validate_year

USER = 'user'
ADMIN = 'admin'
MODERATOR = 'moderator'

ROLE_CHOICES = [
    (USER, USER),
    (ADMIN, ADMIN),
    (MODERATOR, MODERATOR),
]


class User(AbstractUser):
    username = models.CharField(
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        blank=False,
        null=False,
    )
    email = models.EmailField(
        max_length=254, unique=True, blank=False, null=False
    )
    role = models.CharField(
        'роль', max_length=20, choices=ROLE_CHOICES, default=USER, blank=True
    )
    bio = models.TextField(
        'биография',
        blank=True,
    )
    first_name = models.CharField(
        'имя', max_length=FIRST_NAME_MAX_LENGTH, blank=True
    )
    last_name = models.CharField(
        'фамилия', max_length=LAST_NAME_MAX_LENGTH, blank=True
    )

    @property
    def is_user(self):
        return self.role == USER

    @property
    def is_admin(self):
        return self.role == ADMIN or self.is_staff

    @property
    def is_moderator(self):
        return self.role == MODERATOR

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Category(models.Model):
    name = models.CharField(
        'имя категории', max_length=CATEGORY_NAME_MAX_LENGTH
    )
    slug = models.SlugField('слаг категории', unique=True, db_index=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return f'{self.name} {self.name}'


class Genre(models.Model):
    name = models.CharField('имя жанра', max_length=GENRE_NAME_MAX_LENGTH)
    slug = models.SlugField('cлаг жанра', unique=True, db_index=True)

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return f'{self.name} {self.name}'


class Title(models.Model):
    name = models.CharField(
        'название', max_length=TITLE_NAME_MAX_LENGTH, db_index=True
    )
    year = models.IntegerField('год', validators=(validate_year,))
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='titles',
        verbose_name='категория',
    )
    description = models.TextField(
        'описание',
        null=True,
        blank=True,
    )
    genre = models.ManyToManyField(
        Genre, related_name='titles', verbose_name='жанр'
    )

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'

    def __str__(self):
        return self.name


class Review(models.Model):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='произведение',
    )
    text = models.CharField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='автор',
    )
    score = models.IntegerField(
        'оценка',
        validators=(
            MinValueValidator(SCORE_MIN_VALUE),
            MaxValueValidator(SCORE_MAX_VALUE),
        ),
        error_messages={
            'validators': f'Оценка от {SCORE_MIN_VALUE} до {SCORE_MAX_VALUE}!'
        },
    )
    pub_date = models.DateTimeField(
        'дата публикации', auto_now_add=True, db_index=True
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        constraints = (
            (
                models.UniqueConstraint(
                    fields=(
                        'title',
                        'author',
                    ),
                    name='unique review',
                )
            ),
        )
        ordering = ('pub_date',)

    def __str__(self):
        return self.text


class Comment(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='отзыв',
    )
    text = models.CharField(
        'текст комментария',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='автор',
    )
    pub_date = models.DateTimeField(
        'дата публикации', auto_now_add=True, db_index=True
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text
