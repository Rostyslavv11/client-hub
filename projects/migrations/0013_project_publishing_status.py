from django.db import migrations, models


def set_existing_projects_launched(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    Project.objects.update(status_of_publishing="launched")


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0012_alter_application_availability"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="status_of_publishing",
            field=models.CharField(
                choices=[("drafted", "Drafted"), ("launched", "Launched")],
                default="drafted",
                max_length=20,
            ),
        ),
        migrations.RunPython(
            set_existing_projects_launched,
            migrations.RunPython.noop,
        ),
    ]
