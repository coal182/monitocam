import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("cameras", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Recording",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("filename", models.CharField(max_length=255)),
                ("path", models.CharField(max_length=500)),
                ("start_time", models.DateTimeField(blank=True, null=True)),
                ("end_time", models.DateTimeField(blank=True, null=True)),
                ("duration", models.IntegerField(blank=True, null=True)),
                ("size", models.IntegerField(blank=True, null=True)),
                ("has_gif", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "camera",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recordings",
                        to="cameras.camera",
                    ),
                ),
            ],
            options={
                "verbose_name": "Recording",
                "verbose_name_plural": "Recordings",
                "ordering": ["-created_at"],
            },
        ),
    ]
