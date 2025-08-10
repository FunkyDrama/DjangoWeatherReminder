from django.utils import timezone
from subscriptions.models import Subscription
from weather.services import WeatherAPIClient
from notifications.services import NotificationService
from notifications.models import NotificationLog
import requests


# use it when Celery is added
def send_weather_updates():
    """
    Sends weather updates to subscribers based on their preferences.

    This function iterates through all active subscriptions and checks if a
    notification needs to be sent based on the last notification time and
    the defined interval. Weather data for the subscribed city is retrieved
    from the WeatherAPIClient, and notifications are sent either via email
    or webhook. It updates the last notified time for successful notifications.
    In case of errors during the process, logs are created in the
    NotificationLog model for tracking.

    :raises requests.exceptions.HTTPError: Raised when there is an HTTP-related
        error while fetching weather data from the external API.
    :raises Exception: Raised for any other unexpected error during the
        process.
    :return: None
    """
    client = WeatherAPIClient()
    now = timezone.now()

    for sub in Subscription.objects.select_related("user", "city").all():
        if sub.last_notified:
            elapsed = (now - sub.last_notified).total_seconds()
            if elapsed < sub.interval_hours * 3600:
                continue

        try:
            data = client.get_current(sub.city.name)
        except requests.exceptions.HTTPError as e:
            NotificationLog.objects.create(
                subscription=sub, status="error", response=f"Weather API error: {e}"
            )
            continue
        except Exception as e:
            NotificationLog.objects.create(
                subscription=sub, status="error", response=f"Unexpected error: {e}"
            )
            continue

        if sub.notification_type == "email":
            NotificationService.send_email(sub, data)
        else:
            NotificationService.send_webhook(sub, data)
        sub.last_notified = now
        sub.save()


def send_for_subscription(sub):
    """
    Sends a weather update notification according to the subscription
    details. It fetches current weather data for the given subscription's
    city and triggers the appropriate notification.

    :param sub: The subscription object containing the notification type,
        subscriber details, and city for which weather updates are to be
        fetched. Must have `city` and `notification_type` attributes.
    :type sub: Subscription
    :return: None
    """
    client = WeatherAPIClient()
    try:
        data = client.get_current(sub.city.name)
    except requests.exceptions.HTTPError as e:
        NotificationLog.objects.create(
            subscription=sub, status="error", response=f"Weather API error: {e}"
        )
        return
    except Exception as e:
        NotificationLog.objects.create(
            subscription=sub, status="error", response=f"Unexpected error: {e}"
        )
        return

    if sub.notification_type == "email":
        NotificationService.send_email(sub, data)
    else:
        NotificationService.send_webhook(sub, data)

    sub.last_notified = timezone.now()
    sub.save()
