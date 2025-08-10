import requests
from django.core.mail import send_mail
from django.conf import settings
from notifications.models import NotificationLog


class NotificationService:
    """
    Handles notifications related to weather updates by sending them via email or webhook.

    This service provides two notification methods: sending an email to the subscriber's
    registered email address or sending a JSON payload to the subscriber's webhook URL.
    The notification content includes weather data such as temperature, humidity, and
    weather condition.

    Static Methods:
    - `send_email(subscription, weather_data)`: Sends weather updates via email based
      on the subscriber's preferences.
    - `send_webhook(subscription, weather_data)`: Sends weather updates as a JSON
      payload to the subscriber's webhook URL.
    """

    @staticmethod
    def send_email(subscription, weather_data):
        subject = f"Weather update for {subscription.city.name}"
        message = (
            f"Temperature: {weather_data.temperature}°C\n"
            f"Humidity: {weather_data.humidity}%\n"
            f"Condition: {weather_data.condition}"
        )
        recipient = subscription.user.email

        if not recipient:
            NotificationLog.objects.create(
                subscription=subscription,
                status="failed",
                response="No email address provided",
            )
            return

        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])
            status = "sent"
            response = "OK"
        except Exception as e:
            status = "failed"
            response = str(e)
        NotificationLog.objects.create(
            subscription=subscription, status=status, response=response
        )

    @staticmethod
    def send_webhook(subscription, weather_data):
        """
        Sends weather update as JSON to the user's webhook URL.
        """
        url = subscription.user.webhook_url
        if not url:
            return

        payload = {
            "temperature": weather_data.temperature,
            "humidity": weather_data.humidity,
            "condition": weather_data.condition,
            "timestamp": (
                weather_data.timestamp.isoformat() if weather_data.timestamp else None
            ),
        }

        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code >= 400:
                status = "failed"
                response = f"HTTP {resp.status_code}: {resp.text}"
            else:
                status = "sent"
                response = f"HTTP {resp.status_code}"
        except Exception as e:
            status = "failed"
            response = str(e)

        NotificationLog.objects.create(
            subscription=subscription, status=status, response=response
        )
