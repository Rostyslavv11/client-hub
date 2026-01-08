from django.urls import reverse

from .models import Conversation, Message, Notification


def get_or_create_conversation(project, client, freelancer):
    return Conversation.objects.get_or_create(
        project=project,
        client=client,
        freelancer=freelancer,
    )


def create_message(conversation, sender, body, kind=Message.Kind.USER, application=None):
    return Message.objects.create(
        conversation=conversation,
        sender=sender,
        body=body,
        kind=kind,
        application=application,
    )


def create_notification(user, actor, kind, title, body="", conversation=None):
    link = reverse("dashboard:messages")
    if conversation:
        link = f"{link}?conversation={conversation.id}"
    return Notification.objects.create(
        user=user,
        actor=actor,
        kind=kind,
        title=title,
        body=body,
        link=link,
        conversation=conversation,
    )
