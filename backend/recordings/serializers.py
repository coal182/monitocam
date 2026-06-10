from rest_framework import serializers
from django.utils import timezone

from recordings.models import Recording


class RecordingSerializer(serializers.ModelSerializer):
    camera_name = serializers.CharField(source="camera.name", read_only=True)
    timestamp = serializers.SerializerMethodField()

    class Meta:
        model = Recording
        fields = [
            "id",
            "camera",
            "camera_name",
            "filename",
            "path",
            "start_time",
            "end_time",
            "duration",
            "size",
            "has_gif",
            "created_at",
            "timestamp",
        ]
        read_only_fields = ["id", "created_at"]

    def get_timestamp(self, obj):
        if obj.start_time:
            return timezone.localtime(obj.start_time).isoformat()
        return None
