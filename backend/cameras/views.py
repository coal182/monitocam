from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from cameras.models import Camera
from cameras.serializers import CameraSerializer, CameraCreateSerializer
from cameras.tasks import start_recording_task, stop_recording_task


class CameraViewSet(viewsets.ModelViewSet):
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return CameraCreateSerializer
        return CameraSerializer

    def create(self, request, *args, **kwargs):
        serializer = CameraCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        camera = Camera.objects.create(
            name=serializer.validated_data["name"],
            rtsp_url=serializer.validated_data["rtsp_url"],
            enabled=serializer.validated_data.get("enabled", True),
        )

        if camera.enabled:
            start_recording_task.delay(camera.id)

        return Response(
            CameraSerializer(camera).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"])
    def status(self, request, pk=None):
        camera = self.get_object()
        from cameras.services.recorder import recorder_service

        is_recording = recorder_service.is_recording(camera.id)
        return Response(
            {
                "id": camera.id,
                "name": camera.name,
                "status": "recording" if is_recording else "stopped",
                "is_recording": is_recording,
            }
        )

    @action(detail=True, methods=["post"], url_path="start")
    def start_recording(self, request, pk=None):
        camera = self.get_object()
        start_recording_task.delay(camera.id)
        return Response({"status": "recording", "camera_id": camera.id})

    @action(detail=True, methods=["post"], url_path="stop")
    def stop_recording(self, request, pk=None):
        camera = self.get_object()
        stop_recording_task.delay(camera.id)
        return Response({"status": "stopped", "camera_id": camera.id})
