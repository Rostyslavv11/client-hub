from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.db.models import Q

from .models import Conversation, Message, Notification
from .services import create_message, create_notification


@sync_to_async
def get_conversation_for_user(conversation_id, user):
    return Conversation.objects.filter(
        Q(client=user) | Q(freelancer=user),
        pk=conversation_id,
    ).select_related("client", "freelancer").first()


@sync_to_async
def mark_conversation_read(conversation, user):
    Message.objects.filter(
        conversation=conversation,
        is_read=False,
    ).exclude(sender=user).update(is_read=True)
    Notification.objects.filter(
        user=user,
        conversation=conversation,
        is_read=False,
    ).update(is_read=True)


@sync_to_async
def create_message_and_notification(conversation, sender, body):
    message = create_message(conversation, sender, body, kind=Message.Kind.USER)
    recipient = conversation.other_party(sender)
    notification = create_notification(
        user=recipient,
        actor=sender,
        kind=Notification.Kind.MESSAGE,
        title="New message",
        body=body,
        conversation=conversation,
    )
    return message, notification


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        conversation = await get_conversation_for_user(self.conversation_id, user)
        if not conversation:
            await self.close()
            return
        self.conversation = conversation
        await self.channel_layer.group_add(
            f"thread_{self.conversation_id}",
            self.channel_name,
        )
        await self.accept()
        await mark_conversation_read(self.conversation, user)

    async def disconnect(self, close_code):
        if hasattr(self, "conversation_id"):
            await self.channel_layer.group_discard(
                f"thread_{self.conversation_id}",
                self.channel_name,
            )

    async def receive_json(self, content, **kwargs):
        action = content.get("type")
        if action == "read":
            await mark_conversation_read(self.conversation, self.scope["user"])
            return
        if action != "message":
            return
        body = (content.get("body") or "").strip()
        if not body:
            return
        message, notification = await create_message_and_notification(
            self.conversation,
            self.scope["user"],
            body,
        )
        await self.channel_layer.group_send(
            f"thread_{self.conversation_id}",
            {
                "type": "chat.message",
                "message": {
                    "id": message.id,
                    "conversation_id": message.conversation_id,
                    "sender_id": message.sender_id,
                    "sender_name": message.sender.get_full_name()
                    or message.sender.email,
                    "body": message.body,
                    "kind": message.kind,
                    "created_at": message.created_at.isoformat(),
                },
            },
        )
        await self.channel_layer.group_send(
            f"user_{notification.user_id}",
            {
                "type": "notify.message",
                "notification": {
                    "id": notification.id,
                    "kind": notification.kind,
                    "title": notification.title,
                    "body": notification.body,
                    "link": notification.link,
                    "created_at": notification.created_at.isoformat(),
                    "is_read": notification.is_read,
                },
            },
        )

    async def chat_message(self, event):
        await self.send_json({"type": "message", **event["message"]})


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return
        self.user_id = user.id
        await self.channel_layer.group_add(
            f"user_{self.user_id}",
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "user_id"):
            await self.channel_layer.group_discard(
                f"user_{self.user_id}",
                self.channel_name,
            )

    async def notify_message(self, event):
        await self.send_json({"type": "notification", **event["notification"]})
