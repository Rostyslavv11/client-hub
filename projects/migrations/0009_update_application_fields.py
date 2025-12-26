from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0008_project_vibe_description_defaults"),
    ]

    operations = [
        migrations.AddField(
            model_name="application",
            name="full_name",
            field=models.CharField(default="Unknown", max_length=120),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="application",
            name="email",
            field=models.EmailField(default="unknown@example.com", max_length=254),
            preserve_default=False,
        ),
        migrations.RenameField(
            model_name="application",
            old_name="cover_letter",
            new_name="pitch",
        ),
        migrations.AddField(
            model_name="application",
            name="portfolio_url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="application",
            name="portfolio_file",
            field=models.FileField(blank=True, null=True, upload_to="application_portfolios/%Y/%m/"),
        ),
        migrations.AddField(
            model_name="application",
            name="availability",
            field=models.CharField(
                choices=[
                    ("immediate", "Start immediately"),
                    ("1_2_weeks", "1-2 weeks"),
                    ("3_4_weeks", "3-4 weeks"),
                    ("month_plus", "More than a month"),
                ],
                default="immediate",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="application",
            name="estimated_timeline",
            field=models.CharField(blank=True, default="", max_length=80),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="application",
            name="additional_notes",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
    ]
