from django.utils import timezone
from subscriptions.models import Subscription
from weather.services import WeatherAPIClient
from notifications.services import NotificationService
from notifications.models import NotificationLog
import requests
from celery import shared_task


@shared_task(ignore_result=True)
def send_weather_updates():
    """
    Sends weather updates to subscribers based on their preferred notification type and
    update interval. This task fetches the latest weather data for subscribed cities and
    sends notifications via email or webhook. It also ensures that notifications are sent
    only if the elapsed time since the last notification exceeds the subscriber's update
    interval.

    The task handles and logs any errors encountered during the weather data retrieval
    or notification sending process.

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
        sub.save(update_fields=["last_notified"])


@shared_task(ignore_result=True)
def send_for_subscription(sub_id: int):
    """
    Retrieves a subscription by its ID and sends a weather notification based on the
    subscription's associated city and notification type.

    :param sub_id: The unique identifier of the subscription.
    :type sub_id: int

    :return: None
    """
    try:
        sub = Subscription.objects.select_related("user", "city").get(pk=sub_id)
    except Subscription.DoesNotExist:
        return

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
    sub.save(update_fields=["last_notified"])
