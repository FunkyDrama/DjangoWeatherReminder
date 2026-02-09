from rest_framework import serializers
from .models import NotificationLog


class NotificationLogSerializer(serializers.ModelSerializer):
    city = serializers.CharField(source="subscription.city.name", read_only=True)
    notification_type = serializers.CharField(
        source="subscription.notification_type", read_only=True
    )

    class Meta:
        model = NotificationLog
        fields = ("id", "city", "notification_type", "sent_at", "status", "response")
