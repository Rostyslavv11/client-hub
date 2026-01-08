from django.db import migrations


def backfill_conversations(apps, schema_editor):
    Message = apps.get_model("messages_app", "Message")
    Conversation = apps.get_model("messages_app", "Conversation")
    User = apps.get_model("accounts", "CustomUser")
    db_alias = schema_editor.connection.alias

    messages = (
        Message.objects.using(db_alias)
        .filter(conversation__isnull=True)
        .only("id", "sender_id", "receiver_id")
    )
    user_ids = set()
    for message in messages:
        user_ids.add(message.sender_id)
        user_ids.add(message.receiver_id)

    users = User.objects.using(db_alias).in_bulk(user_ids)
    conv_cache = {}

    for message in messages:
        sender = users.get(message.sender_id)
        receiver = users.get(message.receiver_id)
        if not sender or not receiver:
            continue
        sender_role = getattr(sender, "role", "")
        receiver_role = getattr(receiver, "role", "")
        if sender_role == "client" and receiver_role == "freelancer":
            client = sender
            freelancer = receiver
        elif receiver_role == "client" and sender_role == "freelancer":
            client = receiver
            freelancer = sender
        elif sender_role == "client":
            client = sender
            freelancer = receiver
        elif receiver_role == "client":
            client = receiver
            freelancer = sender
        else:
            client = sender
            freelancer = receiver
        key = (client.id, freelancer.id)
        conversation_id = conv_cache.get(key)
        if not conversation_id:
            conversation, _ = Conversation.objects.using(db_alias).get_or_create(
                project_id=None,
                client_id=client.id,
                freelancer_id=freelancer.id,
            )
            conversation_id = conversation.id
            conv_cache[key] = conversation_id
        Message.objects.using(db_alias).filter(pk=message.id).update(
            conversation_id=conversation_id
        )


class Migration(migrations.Migration):

    dependencies = [
        ("messages_app", "0002_conversations_notifications"),
    ]

    operations = [
        migrations.RunPython(backfill_conversations, migrations.RunPython.noop),
    ]
