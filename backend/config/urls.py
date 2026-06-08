from django.contrib import admin
from django.urls import path, include
from core.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health"),
    path("auth/", include("auth.urls")),
    path("cameras/", include("cameras.urls")),
    path("recordings/", include("recordings.urls")),
]
