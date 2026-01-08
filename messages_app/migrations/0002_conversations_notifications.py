from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0014_require_project_details"),
        ("messages_app", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Conversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="client_conversations", to=settings.AUTH_USER_MODEL)),
                ("freelancer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="freelancer_conversations", to=settings.AUTH_USER_MODEL)),
                ("project", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="conversations", to="projects.project")),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(fields=("project", "client", "freelancer"), name="unique_project_conversation")
                ],
            },
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("message", "Message"), ("invite", "Invite"), ("apply", "Apply")], max_length=20)),
                ("title", models.CharField(max_length=140)),
                ("body", models.TextField(blank=True)),
                ("link", models.CharField(blank=True, max_length=300)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("is_read", models.BooleanField(default=False)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="notifications_sent", to=settings.AUTH_USER_MODEL)),
                ("conversation", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="messages_app.conversation")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddField(
            model_name="message",
            name="kind",
            field=models.CharField(choices=[("user", "User"), ("system", "System")], default="user", max_length=20),
        ),
        migrations.AddField(
            model_name="message",
            name="conversation",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="messages_app.conversation"),
        ),
        migrations.RenameField(
            model_name="message",
            old_name="content",
            new_name="body",
        ),
    ]
