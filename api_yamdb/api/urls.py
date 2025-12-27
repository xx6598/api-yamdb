from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import APISignup, APIToken, UsersViewSet

app_name = "api"

router = DefaultRouter()

router.register("users", UsersViewSet, basename="users")
v1_urlpatterns = [
    path("auth/", include("djoser.urls.jwt")),
    path("auth/signup/", APISignup.as_view(), name="signup"),
    path("auth/token/", APIToken.as_view(), name="get_token"),
]

urlpatterns = [
    path("v1/", include(v1_urlpatterns)),
    path("v1/", include(router.urls)),
]
