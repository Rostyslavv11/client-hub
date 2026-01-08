from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_message(message):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        f"thread_{message.conversation_id}",
        {
            "type": "chat.message",
            "message": {
                "id": message.id,
                "conversation_id": message.conversation_id,
                "sender_id": message.sender_id,
                "sender_name": message.sender.get_full_name() or message.sender.email,
                "body": message.body,
                "kind": message.kind,
                "created_at": message.created_at.isoformat(),
            },
        },
    )


def broadcast_notification(notification):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
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
