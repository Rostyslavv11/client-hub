from django.contrib import admin
from .models import CustomUser, ClientProfile, FreelancerProfile


@admin.register(CustomUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "email", "is_staff"]
    list_filter = ["email", "is_active", "last_name"]
    search_fields = ["last_name", "email"]


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "company_name", "location", "hire_rate", "is_open_to_agencies"]
    list_filter = ["is_open_to_agencies", "location"]
    search_fields = ["company_name", "user__email"]


@admin.register(FreelancerProfile)
class FreelancerProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "portfolio_website", "avatar"]
    list_filter = ["portfolio_website"]
    search_fields = ["user__email"]
