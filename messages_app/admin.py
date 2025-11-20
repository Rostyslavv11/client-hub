from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["sender", "receiver", "created_at", "is_read"]
    list_filter = ["created_at", "content"]
    search_fields = ["content", "sender", "receiver"]
