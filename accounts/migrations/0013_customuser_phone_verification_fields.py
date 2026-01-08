from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0012_customuser_email_verification_sent_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="phone_verification_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="customuser",
            name="phone_verification_code",
            field=models.CharField(blank=True, max_length=6),
        ),
    ]
