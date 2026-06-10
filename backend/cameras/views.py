import json
import queue

from django.http import StreamingHttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from cameras.models import Camera
from cameras.serializers import CameraSerializer, CameraCreateSerializer
from cameras.tasks import start_recording_task, stop_recording_task
from cameras.services.recording_status import (
    is_recording,
    subscribe_status,
    get_all_statuses,
)


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
        recording = is_recording(camera.id)
        return Response(
            {
                "id": camera.id,
                "name": camera.name,
                "status": "recording" if recording else "stopped",
                "is_recording": recording,
            }
        )

    @action(detail=False, methods=["get"])
    def statuses(self, request):
        statuses = get_all_statuses()
        result = []
        for camera in Camera.objects.all():
            result.append(
                {
                    "id": camera.id,
                    "name": camera.name,
                    "is_recording": statuses.get(camera.id, False),
                }
            )
        return Response(result)

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

    @action(detail=False, methods=["get"], url_path="events")
    def events(self, request):
        q = queue.Queue()

        def on_status_change(data):
            q.put(data)

        subscribe_status(on_status_change)

        def event_stream():
            yield f"data: {json.dumps(get_all_statuses())}\n\n"
            while True:
                try:
                    data = q.get(timeout=30)
                    yield f"data: {json.dumps(data)}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
