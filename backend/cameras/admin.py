from django.contrib import admin
from cameras.models import Camera


@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ("name", "rtsp_url", "enabled", "created_at")
    list_filter = ("enabled",)
    search_fields = ("name",)
