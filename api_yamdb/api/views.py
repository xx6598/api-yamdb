import uuid

from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import IsAdmin
from .serializers import (
    SignUpSerializer,
    TokenSerializer,
    UsersNotAdminSerializer,
    UsersSerializer,
)

User = get_user_model()


class UsersViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    permission_classes = (
        IsAuthenticated,
        IsAdmin,
    )
    filter_backends = (SearchFilter,)
    search_fields = ["=username"]
    lookup_field = "username"
    pagination_class = LimitOffsetPagination
    http_method_names = ["get", "post", "patch", "delete"]

    @action(
        methods=["GET", "PATCH"],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path="me",
    )
    def get_user_info(self, request):
        serializer = UsersSerializer(request.user)
        if request.method == "PATCH":
            if request.user.is_admin:
                serializer = UsersSerializer(
                    request.user, data=request.data, partial=True
                )
            else:
                serializer = UsersNotAdminSerializer(
                    request.user, data=request.data, partial=True
                )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.data)


class APIToken(APIView):
    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            user = User.objects.get(username=data["username"])
        except User.DoesNotExist:
            return Response(
                {"username": "Пользователь не найден!"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if data.get("confirmation_code") == user.confirmation_code:
            token = RefreshToken.for_user(user).access_token
            return Response(
                {"token": str(token)}, status=status.HTTP_201_CREATED
            )
        return Response(
            {"confirmation_code": "Неверный код подтверждения!"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class APISignup(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject=data["email_subject"],
            body=data["email_body"],
            to=[data["to_email"]],
        )
        email.send()

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        email = serializer.validated_data["email"]
        user_by_username = User.objects.filter(username=username).first()
        user_by_email = User.objects.filter(email=email).first()

        if user_by_username:
            if user_by_username.email != email:
                return Response(
                    {
                        "details": (
                            f"Пользователь <{username}> уже зарегистрирован "
                            "с другим email"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = user_by_username
        else:
            if user_by_email:
                return Response(
                    {
                        "details": (
                            f"Email <{email}> уже зарегистрирован "
                            "другим пользователем"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = User.objects.create(username=username, email=email)
        user.confirmation_code = uuid.uuid4().hex
        user.save(update_fields=["confirmation_code"])
        email_body = (
            "\nВаш код подтвержения для доступа к API: "
            f"{user.confirmation_code}"
        )
        data = {
            "email_body": email_body,
            "to_email": user.email,
            "email_subject": "Код подтвержения для доступа к API",
        }
        self.send_email(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
