import logging

from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from reviews.models import Category, Genre, Review, Title, User

from api.constants import NOREPLY_EMAIL
from api.filters import TitleFilter
from api.mixins import ModelMixinSet
from api.permissions import (
    AdminModeratorAuthorPermission,
    AdminOnly,
    IsAdminUserOrReadOnly,
)
from api.serializers import (
    AdminUserSerializer,
    CategorySerializer,
    CommentSerializer,
    GenreSerializer,
    GetTokenSerializer,
    ReviewSerializer,
    SignUpSerializer,
    TitleReadSerializer,
    TitleWriteSerializer,
    UserMeSerializer,
)

logger = logging.getLogger(__name__)


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = (permissions.IsAuthenticated, AdminOnly)
    lookup_field = "username"
    filter_backends = (SearchFilter,)
    search_fields = ("username",)
    http_method_names = ("get", "post", "patch", "delete")

    def get_serializer_class(self):
        if self.action == "get_current_user_info":
            return UserMeSerializer
        return AdminUserSerializer

    def get_object(self):
        if self.action == "get_current_user_info":
            return self.request.user
        return super().get_object()

    @action(
        methods=["GET", "PATCH"],
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
        url_path="me",
    )
    def get_current_user_info(self, request, *args, **kwargs):
        if request.method == "GET":
            return self.retrieve(request, *args, **kwargs)
        if request.method == "PATCH":
            return self.partial_update(request, *args, **kwargs)


class APIGetToken(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = GetTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        user = serializer.validated_data.get("user")
        token = RefreshToken.for_user(user).access_token
        logger.info(f"Успешное получение токена пользователем {username}")
        return Response({"token": str(token)}, status=status.HTTP_200_OK)


class APISignup(APIView):
    def send_confirmation_token(self, user):
        token = default_token_generator.make_token(user)
        send_mail(
            subject="Токен для завершения регистрации",
            message=(
                "Здравствуйте! "
                f"Используйте этот токен для завершения регистрации: {token}"
            ),
            from_email=NOREPLY_EMAIL,
            recipient_list=[user.email],
        )

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        username = serializer.validated_data["username"]
        user, _ = User.objects.get_or_create(
            email=email, defaults={"username": username}
        )
        self.send_confirmation_token(user)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class ListCreateDestroyViewSet(ModelMixinSet):
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"


class CategoryViewSet(ListCreateDestroyViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(ListCreateDestroyViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TitleViewSet(viewsets.ModelViewSet):
    queryset = (
        Title.objects.annotate(rating=Avg("reviews__score"))
        .select_related("category")
        .prefetch_related("genre")
    )
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = TitleFilter
    search_fields = ("name", "description")
    http_method_names = ("get", "post", "patch", "delete")
    ordering_fields = ("rating", "name", "year")
    ordering = ("-rating",)

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return TitleReadSerializer
        return TitleWriteSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        AdminModeratorAuthorPermission,
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("score", "pub_date")
    http_method_names = ("get", "post", "patch", "delete")

    def get_title(self):
        title_pk = self.kwargs.get("title_pk")
        return get_object_or_404(Title, id=title_pk)

    def get_queryset(self):
        title = self.get_title()
        return title.reviews.select_related("author").all()

    def perform_create(self, serializer):
        title = self.get_title()
        serializer.save(author=self.request.user, title=title)
        logger.info(
            f"Создан отзыв пользователем {self.request.user.username} "
            f"на произведение {title.name}"
        )


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        AdminModeratorAuthorPermission,
    )
    filter_backends = (DjangoFilterBackend,)
    http_method_names = ("get", "post", "patch", "delete")

    def get_review(self):
        review_pk = self.kwargs.get("review_pk")
        title_pk = self.kwargs.get("title_pk")
        return get_object_or_404(Review, id=review_pk, title_id=title_pk)

    def get_queryset(self):
        review = self.get_review()
        return review.comments.select_related("author").all()

    def perform_create(self, serializer):
        review = self.get_review()
        serializer.save(author=self.request.user, review=review)
        logger.info(
            f"Создан комментарий пользователем {self.request.user.username} "
            f"к отзыву {review.pk}"
        )
