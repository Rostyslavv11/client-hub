from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0011_customuser_contact_verification"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="email_verification_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
