from django.db import models


class Camera(models.Model):
    name = models.CharField(max_length=100)
    rtsp_url = models.CharField(max_length=500)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Camera"
        verbose_name_plural = "Cameras"

    def __str__(self):
        return self.name
