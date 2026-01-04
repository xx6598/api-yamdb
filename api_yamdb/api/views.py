import logging

from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from api.filters import TitleFilter
from api.mixins import ModelMixinSet
from api.permissions import (AdminModeratorAuthorPermission, AdminOnly,
                             IsAdminUserOrReadOnly)
from api.serializers import (CategorySerializer, CommentSerializer,
                             GenreSerializer, GetTokenSerializer,
                             ReviewSerializer, SignUpSerializer,
                             TitleReadSerializer, TitleWriteSerializer,
                             UsersSerializer)
from reviews.models import Category, Genre, Review, Title, User

logger = logging.getLogger(__name__)


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        AdminOnly,
    )
    lookup_field = 'username'
    filter_backends = (SearchFilter,)
    search_fields = ('username',)
    http_method_names = ['get', 'post', 'patch', 'delete']

    @action(
        methods=['GET', 'PATCH'],
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
        url_path='me',
    )
    def get_current_user_info(self, request):
        if request.method == 'PATCH':
            serializer = UsersSerializer(
                request.user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = UsersSerializer(request.user,
                                     context={'request': request})
        return Response(serializer.data)


class APIGetToken(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = GetTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        confirmation_token = serializer.validated_data['confirmation_code']
        user = get_object_or_404(User, username=username)
        if default_token_generator.check_token(user, confirmation_token):
            token = RefreshToken.for_user(user).access_token
            logger.info('Успешное получение токена пользователем %s', username)
            return Response({'token': str(token)}, status=status.HTTP_200_OK)
        logger.warning(
            'Неверный код подтверждения (токен) для пользователя: %s', username
        )
        return Response(
            {'confirmation_code': 'Неверный код подтверждения!'},
            status=status.HTTP_400_BAD_REQUEST,
        )


class APISignup(APIView):
    def send_confirmation_token(self, user):
        token = default_token_generator.make_token(user)
        send_mail(
            subject='Токен для завершения регистрации',
            message=(
                'Здравствуйте! '
                f'Используйте этот токен для завершения регистрации: {token}'
            ),
            from_email='noreply@example.com',
            recipient_list=[user.email],
        )

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        username = serializer.validated_data['username']
        user, _ = User.objects.get_or_create(
            email=email,
            defaults={'username': username}
        )
        self.send_confirmation_token(user)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class CategoryViewSet(ModelMixinSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class GenreViewSet(ModelMixinSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class TitleViewSet(viewsets.ModelViewSet):
    queryset = (
        Title.objects.annotate(rating=Avg('reviews__score'))
        .select_related('category')
        .prefetch_related('genre')
        .all()
    )
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_class = TitleFilter
    search_fields = ('name', 'description')
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleReadSerializer
        return TitleWriteSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        AdminModeratorAuthorPermission,
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('score', 'pub_date')
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs.get('title_pk'))
        return title.reviews.select_related('author').all()

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs.get('title_pk'))
        serializer.save(author=self.request.user, title=title)
        logger.info(
            'Создан отзыв пользователем %s на произведение %s',
            self.request.user.username,
            title.name,
        )


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        AdminModeratorAuthorPermission,
    )
    filter_backends = (DjangoFilterBackend,)
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        review = get_object_or_404(Review, id=self.kwargs.get('review_pk'))
        return review.comments.select_related('author').all()

    def perform_create(self, serializer):
        review = get_object_or_404(Review, id=self.kwargs.get('review_pk'))
        serializer.save(author=self.request.user, review=review)
        logger.info(
            'Создан комментарий пользователем %s к отзыву %s',
            self.request.user.username,
            review.pk,
        )
