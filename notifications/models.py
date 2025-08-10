from django.db import models
from subscriptions.models import Subscription


class NotificationLog(models.Model):
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)
    response = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Notification to {self.subscription} at {self.sent_at} - {self.status}"
