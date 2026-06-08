from django.db import models


class Recording(models.Model):
    camera = models.ForeignKey("cameras.Camera", on_delete=models.CASCADE, related_name="recordings")
    filename = models.CharField(max_length=255)
    path = models.CharField(max_length=500)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)
    size = models.IntegerField(null=True, blank=True)
    has_gif = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Recording"
        verbose_name_plural = "Recordings"

    def __str__(self):
        return f"{self.camera.name} - {self.filename}"
