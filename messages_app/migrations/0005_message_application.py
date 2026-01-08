from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0015_invitation"),
        ("messages_app", "0004_message_cleanup"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="application",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="messages", to="projects.application"),
        ),
    ]
