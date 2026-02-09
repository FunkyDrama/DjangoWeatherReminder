from django.db import models
from django.conf import settings


class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    external_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    TYPE_CHOICES = [("email", "Email"), ("webhook", "Webhook")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    city = models.ForeignKey(
        City, on_delete=models.CASCADE, related_name="subscriptions"
    )
    interval_hours = models.PositiveSmallIntegerField(
        choices=[(1, "1h"), (3, "3h"), (6, "6h"), (12, "12h")]
    )
    notification_type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default="email"
    )
    last_notified = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.city.name} every {self.interval_hours}h via {self.notification_type}"
