from django.core.exceptions import ValidationError
from django.utils import timezone

from reviews.constants import USERNAME_RESTRICTED_SLUG


def validate_username(value):
    if value == USERNAME_RESTRICTED_SLUG:
        raise ValidationError(
            f'Имя пользователя не может быть {USERNAME_RESTRICTED_SLUG}.',
            params={'value': value},
        )


def validate_year(value):
    now = timezone.now().year
    if value > now:
        raise ValidationError(
            f'{value} не может быть больше {now}'
        )
