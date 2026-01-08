from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0014_require_project_details"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Invitation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("sent", "Sent"), ("accepted", "Accepted"), ("declined", "Declined"), ("canceled", "Canceled")], default="sent", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sent_invitations", to=settings.AUTH_USER_MODEL)),
                ("freelancer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="received_invitations", to=settings.AUTH_USER_MODEL)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="invitations", to="projects.project")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
