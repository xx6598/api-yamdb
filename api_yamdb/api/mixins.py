from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet


class ModelMixinSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    pass


class CreateViewSet(mixins.CreateModelMixin, GenericViewSet):
    pass
