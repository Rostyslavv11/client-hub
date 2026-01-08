from django.contrib import admin
from .models import Conversation, Message, Notification


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "project", "client", "freelancer", "updated_at"]
    list_select_related = ["project", "client", "freelancer"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["conversation", "sender", "kind", "created_at", "is_read"]
    list_select_related = ["conversation", "sender"]
    list_filter = ["created_at", "kind", "is_read"]
    search_fields = ["body", "sender__email"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "kind", "title", "created_at", "is_read"]
    list_select_related = ["user", "actor", "conversation"]
    list_filter = ["kind", "created_at", "is_read"]
    search_fields = ["title", "body"]
