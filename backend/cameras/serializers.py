from rest_framework import serializers

from cameras.models import Camera


class CameraCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    rtsp_url = serializers.CharField(max_length=500)
    enabled = serializers.BooleanField(default=True)

    def validate_rtsp_url(self, value):
        if not value.startswith("rtsp://"):
            raise serializers.ValidationError("URL must start with rtsp://")
        return value


class CameraUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    rtsp_url = serializers.CharField(max_length=500, required=False)
    enabled = serializers.BooleanField(required=False)

    def validate_rtsp_url(self, value):
        if value is not None and not value.startswith("rtsp://"):
            raise serializers.ValidationError("URL must start with rtsp://")
        return value


class CameraSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Camera
        fields = ["id", "name", "rtsp_url", "enabled", "status", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_status(self, obj):
        from cameras.services.recorder import recorder_service

        is_recording = recorder_service.is_recording(obj.id)
        if is_recording:
            return "recording"
        return "stopped" if obj.enabled else "disabled"
