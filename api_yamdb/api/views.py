import logging
import secrets

from django.core.mail import EmailMessage
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from reviews.models import Category, Genre, Review, Title, User
from .filters import TitleFilter
from .mixins import ModelMixinSet
from .permissions import (AdminModeratorAuthorPermission, AdminOnly,
                          IsAdminUserOrReadOnly)
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, GetTokenSerializer,
                          NotAdminSerializer, ReviewSerializer,
                          SignUpSerializer, TitleReadSerializer,
                          TitleWriteSerializer, UsersSerializer)

logger = logging.getLogger(__name__)


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    permission_classes = (permissions.IsAuthenticated, AdminOnly,)
    lookup_field = 'username'
    filter_backends = (SearchFilter,)
    search_fields = ('username',)
    http_method_names = ['get', 'post', 'patch', 'delete']

    @action(
        methods=['GET', 'PATCH'],
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
        url_path='me')
    def get_current_user_info(self, request):
        serializer_class = (UsersSerializer if request.user.is_admin
                            else NotAdminSerializer)
        if request.method == 'PATCH':
            serializer = serializer_class(
                request.user,
                data=request.data,
                partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = serializer_class(request.user)
        return Response(serializer.data)


class APIGetToken(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = GetTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        confirmation_code = serializer.validated_data['confirmation_code']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.warning(f'Попытка получения токена для несуществующего'
                           f' пользователя: {username}')
            return Response(
                {'username': 'Пользователь не найден!'},
                status=status.HTTP_404_NOT_FOUND)
        if confirmation_code == user.confirmation_code:
            token = RefreshToken.for_user(user).access_token
            logger.info(f'Успешное получение токена'
                        f' пользователем: {username}')
            return Response(
                {'token': str(token)},
                status=status.HTTP_200_OK)
        logger.warning(f'Неверный код подтверждения для'
                       f' пользователя: {username}')
        return Response(
            {'confirmation_code': 'Неверный код подтверждения!'},
            status=status.HTTP_400_BAD_REQUEST)


class APISignup(APIView):
    permission_classes = (permissions.AllowAny,)

    def send_email(self, data):
        try:
            email = EmailMessage(
                subject=data.get('email_subject', 'Код подтверждения'),
                body=data.get('email_body', ''),
                to=[data.get('to_email')]
            )
            email.send()
            logger.info(f'Email отправлен на {data.get("to_email")}')
            return True
        except Exception as e:
            logger.error(f'Ошибка отправки email'
                         f' на {data.get("to_email")}: {e}')
            return False

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        username = serializer.validated_data['username']
        try:
            user = User.objects.get(username=username)
            if user.email != email:
                return Response(
                    {'email': 'Email не совпадает с ранее указанным'
                              ' для этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.confirmation_code = ''.join(
                secrets.choice('0123456789') for _ in range(6)
            )
            user.save()
            logger.info(f'Обновлен код подтверждения для существующего'
                        f' пользователя: {username}')
        except User.DoesNotExist:
            if User.objects.filter(email=email).exists():
                return Response(
                    {'email': 'Пользователь с таким email уже существует'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user = serializer.save()
            logger.info(f'Создан новый пользователь: {username}')

        email_body = (
            f'Доброе время суток, {user.username}.\n\n'
            f'Код подтверждения для доступа к API:'
            f' {user.confirmation_code}\n\n'
            f'Используйте этот код для получения токена доступа.'
        )
        email_data = {
            'email_body': email_body,
            'to_email': user.email,
            'email_subject': 'Код подтверждения для доступа к API!'
        }

        if not self.send_email(email_data):
            logger.warning(f'Не удалось отправить email'
                           f' пользователю {username}')

        return Response(
            {'username': user.username, 'email': user.email},
            status=status.HTTP_200_OK
        )


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
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')
    ).select_related('category').prefetch_related('genre').all()
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
    permission_classes = (AdminModeratorAuthorPermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('score', 'pub_date')
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        title = get_object_or_404(
            Title,
            id=self.kwargs.get('title_pk'))
        return title.reviews.select_related('author').all()

    def perform_create(self, serializer):
        title = get_object_or_404(
            Title,
            id=self.kwargs.get('title_pk'))
        serializer.save(author=self.request.user, title=title)
        logger.info(f'Создан отзыв пользователем {self.request.user.username}'
                    f' на произведение {title.name}')


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (AdminModeratorAuthorPermission,)
    filter_backends = (DjangoFilterBackend,)
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get('review_pk'))
        return review.comments.select_related('author').all()

    def perform_create(self, serializer):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get('review_pk'))
        serializer.save(author=self.request.user, review=review)
        logger.info(f'Создан комментарий пользователем'
                    f' {self.request.user.username} к отзыву {review.pk}')
