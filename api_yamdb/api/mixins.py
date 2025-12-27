from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet


class ModelMixinSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    """
    Кастомный ViewSet только с методами создания,
    получения списка и удаления объектов.

    Использование:
    - Для категорий (Category): создание, просмотр списка, удаление
    - Для жанров (Genre): создание, просмотр списка, удаление
    - Для любых сущностей, где не нужны update/retrieve
    """
    pass


class CreateViewSet(mixins.CreateModelMixin, GenericViewSet):
    """
    ViewSet только для создания объектов.

    Использование:
    - Для регистрации пользователей
    - Для отправки форм
    - Там, где нужен только POST запрос
    """
    pass
