import os
from pathlib import Path
from datetime import datetime, timedelta

from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from recordings.models import Recording
from recordings.serializers import RecordingSerializer


class RecordingViewSet(viewsets.ModelViewSet):
    queryset = Recording.objects.select_related("camera").all()
    serializer_class = RecordingSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        camera_id = self.request.query_params.get("camera_id")
        if camera_id:
            qs = qs.filter(camera_id=camera_id)
        return qs

    def destroy(self, request, *args, **kwargs):
        recording = self.get_object()
        file_path = Path(recording.path)

        if file_path.exists():
            os.remove(file_path)

        gif_path = file_path.with_suffix(".gif")
        if gif_path.exists():
            os.remove(gif_path)

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["get"])
    def stream(self, request, pk=None):
        recording = self.get_object()
        file_path = Path(recording.path)

        if not file_path.exists():
            raise Http404("Recording file not found")

        return FileResponse(
            open(file_path, "rb"),
            content_type="video/mp4",
            as_attachment=False,
            filename=recording.filename,
        )

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        recording = self.get_object()
        file_path = Path(recording.path)

        if not file_path.exists():
            raise Http404("Recording file not found")

        return FileResponse(
            open(file_path, "rb"),
            content_type="video/mp4",
            as_attachment=True,
            filename=recording.filename,
        )

    @action(detail=True, methods=["get"])
    def get_gif(self, request, pk=None):
        recording = self.get_object()
        gif_path = Path(recording.path).with_suffix(".gif")

        if not gif_path.exists():
            from recordings.tasks import generate_gif_task
            generate_gif_task.delay(recording.id)
            return Response({"status": "generating", "message": "GIF generation started"})

        return FileResponse(
            open(gif_path, "rb"),
            content_type="image/gif",
            as_attachment=False,
            filename=gif_path.name,
        )

    @action(detail=False, methods=["get"], url_path="gifs/list")
    def gifs_list(self, request):
        qs = self.get_queryset().filter(has_gif=True)
        camera_id = request.query_params.get("camera_id")
        if camera_id:
            qs = qs.filter(camera_id=camera_id)
        serializer = RecordingSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="gifs/(?P<pk>[0-9]+)/file")
    def gif_file(self, request, pk=None):
        try:
            recording = Recording.objects.get(id=pk)
        except Recording.DoesNotExist:
            raise Http404("Recording not found")

        gif_path = Path(recording.path).with_suffix(".gif")

        if not gif_path.exists():
            from recordings.tasks import generate_gif_task
            generate_gif_task.delay(recording.id)
            return Response({"status": "generating", "message": "GIF generation started"})

        return FileResponse(
            open(gif_path, "rb"),
            content_type="image/gif",
            as_attachment=False,
            filename=gif_path.name,
        )

    @action(detail=False, methods=["delete"], url_path="cleanup/(?P<days>[0-9]+)")
    def cleanup(self, request, days=None):
        days = int(days)
        cutoff_date = datetime.now() - timedelta(days=days)

        recordings = Recording.objects.filter(
            created_at__lt=cutoff_date,
        )

        deleted_count = 0
        for recording in recordings:
            file_path = Path(recording.path)
            if file_path.exists():
                os.remove(file_path)

            gif_path = file_path.with_suffix(".gif")
            if gif_path.exists():
                os.remove(gif_path)

            recording.delete()
            deleted_count += 1

        return Response({"deleted": deleted_count, "days": days})
