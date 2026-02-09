import requests
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
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
        recipient = subscription.user.email
        message = render_to_string(
            "weather_update.html",
            {
                "city": subscription.city.name,
                "temperature": weather_data.temperature,
                "humidity": weather_data.humidity,
                "condition": weather_data.condition,
                "description": weather_data.description,
                "icon": weather_data.icon,
                "wind_speed": weather_data.wind_speed,
                "feels_like": weather_data.feels_like,
                "timestamp": weather_data.timestamp,
            },
        )

        if not recipient:
            NotificationLog.objects.create(
                subscription=subscription,
                status="failed",
                response="No email address provided",
            )
            return

        try:
            email = EmailMultiAlternatives(
                subject, message, settings.DEFAULT_FROM_EMAIL, [recipient]
            )
            email.attach_alternative(message, "text/html")
            email.send()
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
            "city": subscription.city.name,
            "temperature": weather_data.temperature,
            "humidity": weather_data.humidity,
            "condition": weather_data.condition,
            "description": weather_data.description,
            "icon": weather_data.icon,
            "wind_speed": weather_data.wind_speed,
            "feels_like": weather_data.feels_like,
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
