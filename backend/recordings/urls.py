from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recordings.views import RecordingViewSet

router = DefaultRouter()
router.register(r"recordings", RecordingViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
