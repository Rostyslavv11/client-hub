from django.contrib import admin
from .models import (
    CustomUser,
    Profile
)


@admin.register(CustomUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "email", "is_staff"]
    list_filter = ["email", "is_active", "last_name"]
    search_fields = ["last_name", "email"]


@admin.register(Profile)
class Profile(admin.ModelAdmin):
    list_display = ["user", "portfolio_website", "avatar"]
    list_filter = ["portfolio_website"]
    search_fields = ["user"]