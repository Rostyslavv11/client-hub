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
    list_display = ["project", "full_name", "email", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["full_name", "email", "pitch", "status"]
