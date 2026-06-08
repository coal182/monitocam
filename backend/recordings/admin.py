from django.contrib import admin
from recordings.models import Recording


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = ("filename", "camera", "start_time", "end_time", "duration", "size", "has_gif")
    list_filter = ("has_gif",)
    search_fields = ("filename",)
    raw_id_fields = ("camera",)
