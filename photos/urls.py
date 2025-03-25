from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PhotoViewSet,
    AlbumViewSet,
    ShareViewSet,
    SharedWithMePhotosView,
    SharedWithMeAlbumsView,
    UserCreateView,
    HomePageView
)

router = DefaultRouter()
router.register(r"photos", PhotoViewSet, basename="photo")
router.register(r"albums", AlbumViewSet, basename="album")
router.register(r"share", ShareViewSet, basename="share")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "share/received/photos/",
        SharedWithMePhotosView.as_view(),
        name="shared-with-me-photos",
    ),
    path(
        "share/received/albums/",
        SharedWithMeAlbumsView.as_view(),
        name="shared-with-me-albums",
    ),
    path('users/register/', UserCreateView.as_view(), name='user-register'),
    path('homepage/', HomePageView.as_view(), name='homepage'),
]
