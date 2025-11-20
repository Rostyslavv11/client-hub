from django.contrib import admin
from .models import (
    Project,
    Application
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "client", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["title", "description"]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["project", "freelancer", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["cover_letter", "status"]
