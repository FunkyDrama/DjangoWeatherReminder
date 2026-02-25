from datetime import datetime, timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from django.contrib.auth import get_user_model
from subscriptions.models import City, Subscription
from notifications.models import NotificationLog
from notifications.tasks import send_weather_updates
from weather.services import WeatherData

User = get_user_model()


class CeleryEnqueueOnCreateTests(TestCase):
    """
    Unit test class to ensure tasks are enqueued upon the creation of a subscription.

    This class is dedicated to testing the behavior of the system when a new
    subscription is created. Specifically, it ensures that the Celery task
    responsible for handling subscriptions is enqueued with the proper arguments.
    The test mocks the Celery task to verify its invocation.

    :ivar client: Provides an interface for making API requests as an authenticated user.
    :type client: APIClient
    :ivar user: Represents the authenticated user for the test cases.
    :type user: User
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="c1@test.com", password="pw")
        self.client.force_authenticate(user=self.user)

    @patch("subscriptions.views.send_for_subscription")
    def test_create_subscription_enqueues_task(self, mock_task):
        url = reverse("subscription-list")
        payload = {
            "city": {"name": "Kyiv"},
            "interval_hours": 1,
            "notification_type": "email",
        }
        r = self.client.post(url, payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        new_id = r.data["id"]
        mock_task.delay.assert_called_once_with(new_id)


class CeleryFallbackWhenBrokerDownTests(TestCase):
    """
    Test case for handling fallback execution when message broker is down.

    This class contains tests related to verifying fallback execution for message
    delivery failures in a subscription system. It leverages mocked services to
    simulate failures in the broker and confirm the fallback mechanism works as
    intended.

    :ivar client: API test client used for making HTTP requests in test cases.
    :type client: APIClient
    :ivar user: Test user instance created for authentication in test cases.
    :type user: User
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="c2@test.com", password="pw")
        self.client.force_authenticate(user=self.user)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    @patch("weather.services.WeatherAPIClient.get_current")
    def test_sync_fallback_executes_if_delay_fails(self, mock_get_current):
        mock_get_current.return_value = WeatherData(10.0, 50, "Clear", datetime.now())
        with patch(
            "subscriptions.views.send_for_subscription.delay",
            side_effect=Exception("broker down"),
        ):
            url = reverse("subscription-list")
            payload = {
                "city": {"name": "Kyiv"},
                "interval_hours": 1,
                "notification_type": "email",
            }
            r = self.client.post(url, payload, format="json")
            self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        self.assertTrue(NotificationLog.objects.exists())

        sub = Subscription.objects.get(id=r.data["id"])
        self.assertIsNotNone(sub.last_notified)


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class CeleryEagerIntervalTests(TestCase):
    """
    Test case for verifying weather updates functionality with respect to the notification
    interval.

    This test case is defined to ensure that weather updates are sent to users based on their
    specified subscription interval. It mocks required external dependencies to simulate real
    application behavior during testing.

    :ivar user: The test user object created for these tests.
    :type user: User
    :ivar city: The test city object associated with user subscriptions.
    :type city: City
    :ivar sub_old: Subscription object for the user created to represent a past notification.
    :type sub_old: Subscription
    :ivar sub_new: Subscription object for the user created to represent a recent notification.
    :type sub_new: Subscription
    """

    def setUp(self):
        self.user = User.objects.create_user(email="c3@test.com", password="pw")
        self.city = City.objects.create(name="TestCity")
        self.sub_old = Subscription.objects.create(
            user=self.user,
            city=self.city,
            interval_hours=1,
            notification_type="email",
            last_notified=timezone.now() - timedelta(hours=2),
        )
        self.sub_new = Subscription.objects.create(
            user=self.user,
            city=self.city,
            interval_hours=1,
            notification_type="email",
            last_notified=timezone.now() - timedelta(minutes=30),
        )

    @patch("weather.services.WeatherAPIClient.get_current")
    def test_send_weather_updates_respects_interval(self, mock_get_current):
        mock_get_current.return_value = WeatherData(3.3, 44, "Clouds", datetime.now())
        send_weather_updates.delay()
        self.assertEqual(
            NotificationLog.objects.filter(subscription=self.sub_old).count(), 1
        )
        self.assertEqual(
            NotificationLog.objects.filter(subscription=self.sub_new).count(), 0
        )
        self.sub_old.refresh_from_db()
        self.assertAlmostEqual(
            self.sub_old.last_notified.timestamp(), timezone.now().timestamp(), delta=5
        )


class CeleryBeatConfigTests(TestCase):
    """
    Tests for verifying Celery Beat configuration.

    This class is designed to test if the Celery Beat schedule in the Django settings
    contains the task `notifications.tasks.send_weather_updates`. Proper configuration
    of Celery Beat ensures scheduled tasks are properly executed in the application.
    """

    def test_beat_schedule_has_weather_task(self):
        from django.conf import settings

        schedule = getattr(settings, "CELERY_BEAT_SCHEDULE", {})
        has_entry = any(
            (entry.get("task") == "notifications.tasks.send_weather_updates")
            for entry in schedule.values()
        )
        self.assertTrue(
            has_entry,
            "CELERY_BEAT_SCHEDULE must include notifications.tasks.send_weather_updates",
        )
