from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from api.views import (APIGetToken, APISignup, CategoryViewSet, CommentViewSet,
                       GenreViewSet, ReviewViewSet, TitleViewSet, UsersViewSet)

app_name = 'api'

v1_router = DefaultRouter()
v1_router.register('users', UsersViewSet, basename='users')
v1_router.register('categories', CategoryViewSet, basename='categories')
v1_router.register('genres', GenreViewSet, basename='genres')
v1_router.register('titles', TitleViewSet, basename='titles')

titles_router = routers.NestedDefaultRouter(
    v1_router, 'titles', lookup='title'
)
titles_router.register('reviews', ReviewViewSet, basename='title-reviews')

reviews_router = routers.NestedDefaultRouter(
    titles_router, 'reviews', lookup='review'
)
reviews_router.register('comments', CommentViewSet, basename='review-comments')

auth_urlpatterns = [
    path('signup/', APISignup.as_view(), name='signup'),
    path('token/', APIGetToken.as_view(), name='get_token'),
]

v1_urlpatterns = [
    path('', include(v1_router.urls)),
    path('', include(titles_router.urls)),
    path('', include(reviews_router.urls)),
    path('auth/', include(auth_urlpatterns)),
]

urlpatterns = [
    path('v1/', include(v1_urlpatterns)),
]
