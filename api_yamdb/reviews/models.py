from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from api.constants import SCORE_MAX_VALUE, SCORE_MIN_VALUE
from reviews.constants import (EMAIL_MAX_LENGTH, FIRST_NAME_MAX_LENGTH,
                               LAST_NAME_MAX_LENGTH, NAME_MAX_LENGTH,
                               TITLE_NAME_MAX_LENGTH, USERNAME_MAX_LENGTH)
from reviews.validators import validate_username, validate_year

USER = 'user'
ADMIN = 'admin'
MODERATOR = 'moderator'

ROLE_CHOICES = [
    (USER, USER),
    (ADMIN, ADMIN),
    (MODERATOR, MODERATOR),
]

ROLE_MAX_LENGTH = max(len(role) for role, _ in ROLE_CHOICES)


class NamedModel(models.Model):
    name = models.CharField(verbose_name='имя', max_length=NAME_MAX_LENGTH)

    class Meta:
        abstract = True
        ordering = ('name',)


class User(AbstractUser):
    username = models.CharField(
        verbose_name='имя пользователя',
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=(validate_username,),
    )
    email = models.EmailField(
        verbose_name='e-mail',
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
    )
    role = models.CharField(
        verbose_name='роль',
        max_length=ROLE_MAX_LENGTH,
        choices=ROLE_CHOICES,
        default=USER,
        blank=True,
    )
    bio = models.TextField(
        verbose_name='биография',
        blank=True,
    )
    first_name = models.CharField(
        verbose_name='имя', max_length=FIRST_NAME_MAX_LENGTH, blank=True
    )
    last_name = models.CharField(
        verbose_name='фамилия', max_length=LAST_NAME_MAX_LENGTH, blank=True
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.role == ADMIN or self.is_staff

    @property
    def is_moderator(self):
        return self.role == MODERATOR


class TextAuthorDateModel(models.Model):
    text = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)ss_author',
        verbose_name='автор',
    )
    pub_date = models.DateTimeField(
        verbose_name='дата публикации', auto_now_add=True, db_index=True
    )

    class Meta:
        abstract = True
        ordering = ('pub_date',)

    def __str__(self):
        return self.text


class SlugModel(models.Model):
    models.CharField(
        verbose_name='имя',
    )
    slug = models.SlugField(verbose_name='слаг', unique=True, db_index=True)

    class Meta(NamedModel.Meta):
        abstract = True


class Category(NamedModel, SlugModel):
    class Meta(SlugModel.Meta):
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Genre(NamedModel, SlugModel):
    class Meta(SlugModel.Meta):
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Title(models.Model):
    name = models.CharField(
        verbose_name='название',
        max_length=TITLE_NAME_MAX_LENGTH,
        db_index=True,
    )
    year = models.SmallIntegerField(
        verbose_name='год', validators=(validate_year,)
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='titles',
        verbose_name='категория',
    )
    description = models.TextField(
        verbose_name='описание',
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


class Review(TextAuthorDateModel):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='произведение',
    )
    score = models.PositiveSmallIntegerField(
        verbose_name='оценка',
        validators=(
            MinValueValidator(SCORE_MIN_VALUE),
            MaxValueValidator(SCORE_MAX_VALUE),
        ),
        error_messages={
            'validators': f'Оценка от {SCORE_MIN_VALUE} до {SCORE_MAX_VALUE}!'
        },
    )

    class Meta(TextAuthorDateModel.Meta):
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


class Comment(TextAuthorDateModel):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='отзыв',
    )

    class Meta(TextAuthorDateModel.Meta):
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
