from django.utils import timezone
from subscriptions.models import Subscription
from weather.services import WeatherAPIClient
from notifications.services import NotificationService
from notifications.models import NotificationLog
import requests
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

# Network-level failures (DNS, refused/reset connections, timeouts) that are worth
# retrying later, as opposed to OpenWeatherMap answering with an error status.
TRANSIENT_ERRORS = (requests.ConnectionError, requests.Timeout)


def _error_message(e: Exception) -> str:
    """
    Builds a user-facing error description. Never uses ``str(e)`` for requests
    exceptions: it contains the request URL, which includes the API key.
    """
    if isinstance(e, requests.HTTPError) and e.response is not None:
        return f"Weather API error: HTTP {e.response.status_code}"
    if isinstance(e, requests.Timeout):
        return "Weather API error: request timed out"
    if isinstance(e, requests.ConnectionError):
        return "Weather API error: service unreachable"
    return f"Unexpected error: {type(e).__name__}"


def _log_error(sub: Subscription, e: Exception) -> None:
    NotificationLog.objects.create(
        subscription=sub, status="error", response=_error_message(e)
    )


def _deliver(sub: Subscription, data) -> None:
    if sub.notification_type == "email":
        NotificationService.send_email(sub, data)
    else:
        NotificationService.send_webhook(sub, data)
    sub.last_notified = timezone.now()
    sub.save(update_fields=["last_notified"])


@shared_task(ignore_result=True)
def send_weather_updates():
    """
    Sends weather updates to subscribers based on their preferred notification type and
    update interval. This task fetches the latest weather data for subscribed cities and
    sends notifications via email or webhook. It also ensures that notifications are sent
    only if the elapsed time since the last notification exceeds the subscriber's update
    interval.

    Transient network errors are not logged as failed notifications: ``last_notified``
    stays unchanged, so the next beat run retries the subscription automatically.

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
        except TRANSIENT_ERRORS as e:
            logger.warning(
                "Weather API unreachable for %s, retrying on next run: %s",
                sub.city.name,
                type(e).__name__,
            )
            continue
        except Exception as e:
            _log_error(sub, e)
            continue

        _deliver(sub, data)


@shared_task(bind=True, ignore_result=True, max_retries=3)
def send_for_subscription(self, sub_id: int):
    """
    Retrieves a subscription by its ID and sends a weather notification based on the
    subscription's associated city and notification type.

    On transient network errors the task is retried with backoff (1, 2, 4 minutes);
    an error is logged only once all retries are exhausted.

    :param sub_id: The unique identifier of the subscription.
    :type sub_id: int

    :return: None
    """
    try:
        sub = Subscription.objects.select_related("user", "city").get(pk=sub_id)
    except Subscription.DoesNotExist:
        return

    # While this task waited to retry, the periodic task may have delivered already.
    if self.request.retries and sub.last_notified:
        return

    client = WeatherAPIClient()
    try:
        data = client.get_current(sub.city.name)
    except TRANSIENT_ERRORS as e:
        if not self.request.called_directly and self.request.retries < self.max_retries:
            logger.warning(
                "Weather API unreachable for %s, retry %d/%d: %s",
                sub.city.name,
                self.request.retries + 1,
                self.max_retries,
                type(e).__name__,
            )
            raise self.retry(countdown=60 * 2**self.request.retries)
        _log_error(sub, e)
        return
    except Exception as e:
        _log_error(sub, e)
        return

    _deliver(sub, data)
