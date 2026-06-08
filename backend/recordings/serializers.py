from rest_framework import serializers

from recordings.models import Recording


class RecordingSerializer(serializers.ModelSerializer):
    camera_name = serializers.CharField(source="camera.name", read_only=True)

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
        ]
        read_only_fields = ["id", "created_at"]
