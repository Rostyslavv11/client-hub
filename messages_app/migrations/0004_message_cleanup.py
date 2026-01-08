from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("messages_app", "0003_message_conversation_backfill"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="message",
            name="receiver",
        ),
        migrations.AlterField(
            model_name="message",
            name="conversation",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="messages_app.conversation"),
        ),
    ]
