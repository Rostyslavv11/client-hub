from datetime import timedelta

from django.db import migrations, models
from django.utils import timezone


def fill_project_details(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    today = timezone.now().date()

    for project in Project.objects.all():
        updates = {}
        if not project.project_overview:
            overview = f"Overview for {project.title}."
            if project.description:
                overview = f"{overview} {project.description[:160]}"
            updates["project_overview"] = overview
        if not project.responsibilities:
            updates["responsibilities"] = (
                "Define scope and deliverables\n"
                "Share weekly progress updates\n"
                "Deliver final assets and handoff notes"
            )
        if not project.requirements:
            updates["requirements"] = (
                "Relevant portfolio\n"
                "Clear communication and feedback cadence\n"
                "Availability for milestone check-ins"
            )
        if project.deadline is None:
            base_date = project.created_at.date() if project.created_at else today
            updates["deadline"] = base_date + timedelta(days=30)

        if updates:
            for key, value in updates.items():
                setattr(project, key, value)
            project.save(update_fields=list(updates.keys()))


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0013_project_publishing_status"),
    ]

    operations = [
        migrations.RunPython(fill_project_details, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="project",
            name="deadline",
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name="project",
            name="project_overview",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="project",
            name="responsibilities",
            field=models.TextField(
                help_text="What you will do (one item per line or markdown list)"
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="requirements",
            field=models.TextField(
                help_text="Requirements of client (one item per line or markdown list)"
            ),
        ),
    ]
