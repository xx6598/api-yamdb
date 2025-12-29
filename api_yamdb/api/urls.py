from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import (APIGetToken, APISignup, CategoryViewSet, CommentViewSet,
                    GenreViewSet, ReviewViewSet, TitleViewSet, UsersViewSet)

app_name = 'api'

router = DefaultRouter()
router.register('users', UsersViewSet, basename='users')
router.register('categories', CategoryViewSet, basename='categories')
router.register('genres', GenreViewSet, basename='genres')
router.register('titles', TitleViewSet, basename='titles')

titles_router = routers.NestedDefaultRouter(router, 'titles', lookup='title')
titles_router.register('reviews', ReviewViewSet, basename='title-reviews')

reviews_router = routers.NestedDefaultRouter(titles_router,
                                             'reviews', lookup='review')
reviews_router.register('comments', CommentViewSet, basename='review-comments')

auth_urlpatterns = [
    path('auth/', include('djoser.urls.jwt')),
    path('auth/signup/', APISignup.as_view(), name='signup'),
    path('auth/token/', APIGetToken.as_view(), name='get_token'),
]

v1_urlpatterns = [
    path('', include(router.urls)),
    path('', include(titles_router.urls)),
    path('', include(reviews_router.urls)),
    *auth_urlpatterns,
]

urlpatterns = [
    path('v1/', include(v1_urlpatterns)),
]
