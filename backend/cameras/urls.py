from django.urls import path, include
from rest_framework.routers import DefaultRouter

from cameras.views import CameraViewSet

router = DefaultRouter()
router.register(r"", CameraViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
