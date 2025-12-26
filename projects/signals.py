from django.db.models.signals import post_save
from django.dispatch import receiver

from projects.models import Application, Project


@receiver(post_save, sender=Application)
def update_project_status_on_application(sender, instance, **kwargs):
    if instance.status != Application.Status.COMPLETED:
        return
    if instance.project.status == Project.Status.COMPLETED:
        return
    instance.project.status = Project.Status.COMPLETED
    instance.project.save(update_fields=["status"])
