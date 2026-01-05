from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0010_alter_freelancerprofile_weekly_capacity"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="email_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="customuser",
            name="phone_number",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name="customuser",
            name="phone_verified",
            field=models.BooleanField(default=False),
        ),
    ]
