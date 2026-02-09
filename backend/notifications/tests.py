from datetime import datetime, timedelta
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from subscriptions.models import City, Subscription
from notifications.models import NotificationLog
from notifications.serializers import NotificationLogSerializer
from notifications.services import NotificationService
from notifications.tasks import send_weather_updates
from weather.services import WeatherData

User = get_user_model()


class NotificationLogModelTests(TestCase):
    """
    This class contains test cases for the NotificationLog model.

    It sets up a testing environment with a user, city, subscription, and notification log to ensure
    the correctness of string representation and serialized data fields for the NotificationLog model.

    :ivar user: The user associated with the testing environment.
    :type user: User
    :ivar city: The city associated with the subscription in the testing environment.
    :type city: City
    :ivar sub: The subscription object created for the user and city.
    :type sub: Subscription
    :ivar log: The notification log associated with the created subscription.
    :type log: NotificationLog
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="m@test.com", username="m", password="pw"
        )
        self.city = City.objects.create(name="MCity")
        self.sub = Subscription.objects.create(
            user=self.user, city=self.city, interval_hours=1, notification_type="email"
        )
        self.log = NotificationLog.objects.create(
            subscription=self.sub, status="sent", response="OK"
        )

    def test_str(self):
        s = str(self.log)
        self.assertIn("Notification to", s)
        self.assertIn("sent", s)
        self.assertIn(self.city.name, s)

    def test_serializer_fields(self):
        data = NotificationLogSerializer(self.log).data
        self.assertEqual(data["id"], self.log.id)
        self.assertEqual(data["city"], self.city.name)
        self.assertEqual(data["notification_type"], self.sub.notification_type)
        self.assertEqual(data["status"], "sent")
        self.assertEqual(data["response"], "OK")


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class NotificationServiceTests(TestCase):
    """
    Test suite for the Notification Service.

    This class contains test cases to validate the functionality of sending
    email and webhook notifications within the NotificationService. It ensures
    that notifications are correctly sent and logs are appropriately created
    or updated based on various conditions such as missing recipient details
    or server errors. Mocking is used to simulate external dependencies like
    HTTP requests.

    :ivar user: A dummy user instance used for testing notification scenarios.
    :type user: User
    :ivar city: A dummy city instance associated with user subscriptions.
    :type city: City
    :ivar sub_email: A subscription object for testing email notifications.
    :type sub_email: Subscription
    :ivar sub_webhook: A subscription object for testing webhook notifications.
    :type sub_webhook: Subscription
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="e@test.com", username="e", password="pw"
        )
        self.city = City.objects.create(name="ECity")
        self.sub_email = Subscription.objects.create(
            user=self.user, city=self.city, interval_hours=1, notification_type="email"
        )
        self.sub_webhook = Subscription.objects.create(
            user=self.user,
            city=self.city,
            interval_hours=1,
            notification_type="webhook",
        )

    def test_send_email_no_recipient_logs_failure(self):
        self.user.email = ""
        self.user.save()
        NotificationService.send_email(
            self.sub_email, WeatherData(1, 2, "Cond", datetime.now())
        )
        log = NotificationLog.objects.get(subscription=self.sub_email)
        self.assertEqual(log.status, "failed")
        self.assertIn("No email address", log.response)

    def test_send_email_success_logs_sent(self):
        NotificationService.send_email(
            self.sub_email, WeatherData(10, 20, "Sunny", datetime.now())
        )
        log = NotificationLog.objects.get(subscription=self.sub_email)
        self.assertEqual(log.status, "sent")
        self.assertEqual(log.response, "OK")

    @patch("notifications.services.requests.post")
    def test_send_webhook_no_url(self, mock_post):
        NotificationService.send_webhook(
            self.sub_webhook, WeatherData(0, 0, "X", datetime.now())
        )
        self.assertFalse(
            NotificationLog.objects.filter(subscription=self.sub_webhook).exists()
        )
        mock_post.assert_not_called()

    @patch("notifications.services.requests.post")
    def test_send_webhook_success_and_failure(self, mock_post):
        self.user.webhook_url = "http://example.com/hook"
        self.user.save()
        mock_resp = MagicMock(status_code=200, text="OK")
        mock_post.return_value = mock_resp
        NotificationService.send_webhook(
            self.sub_webhook, WeatherData(5, 5, "C", datetime.now())
        )
        log = NotificationLog.objects.get(subscription=self.sub_webhook)
        self.assertEqual(log.status, "sent")
        self.assertIn("HTTP 200", log.response)
        NotificationLog.objects.filter(subscription=self.sub_webhook).delete()
        mock_resp = MagicMock(status_code=500, text="Err")
        mock_post.return_value = mock_resp
        NotificationService.send_webhook(
            self.sub_webhook, WeatherData(5, 5, "C", datetime.now())
        )
        log = NotificationLog.objects.get(subscription=self.sub_webhook)
        self.assertEqual(log.status, "failed")
        self.assertIn("HTTP 500", log.response)
        NotificationLog.objects.filter(subscription=self.sub_webhook).delete()
        mock_post.side_effect = Exception("timeout")
        NotificationService.send_webhook(
            self.sub_webhook, WeatherData(5, 5, "C", datetime.now())
        )
        log = NotificationLog.objects.get(subscription=self.sub_webhook)
        self.assertEqual(log.status, "failed")
        self.assertIn("timeout", log.response)


class SendWeatherUpdatesTaskTests(TestCase):
    """
    Test cases for the functionality of sending weather updates.

    This class contains unit tests for verifying the behavior of the weather
    updates task, ensuring it adheres to set conditions such as notification
    intervals.

    :ivar user: Instance of the user who has subscribed to weather notifications.
    :type user: User
    :ivar city: Instance of a city for which the user subscribes to receive
                weather updates.
    :type city: City
    :ivar sub_old: Subscription instance representing an older notification,
                   where the last notified time exceeds the specified interval.
    :type sub_old: Subscription
    :ivar sub_new: Subscription instance representing a more recent notification,
                   where the last notified time does not exceed the specified
                   interval.
    :type sub_new: Subscription
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="t@test.com", username="t", password="pw"
        )
        self.city = City.objects.create(name="TCity")
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

    @patch("notifications.tasks.WeatherAPIClient.get_current")
    @patch("notifications.services.NotificationService.send_email")
    def test_task_respects_interval(self, mock_send_email, mock_get_current):
        wd = WeatherData(3.3, 44, "X", datetime.now())
        mock_get_current.return_value = wd
        send_weather_updates()
        mock_send_email.assert_called_once_with(self.sub_old, wd)
        self.assertEqual(NotificationLog.objects.count(), 0)


class NotificationLogViewSetTests(TestCase):
    """
    Unit test class for testing notification log views.

    This class contains tests for ensuring that the notification log views
    function as expected for authenticated and unauthenticated users, and
    appropriately filter logs based on the logged-in user.

    :ivar client: API client used for simulating API requests.
    :type client: APIClient
    :ivar user1: First test user with associated subscription and logs.
    :type user1: User
    :ivar user2: Second test user with associated subscription and logs.
    :type user2: User
    """

    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email="v1@test.com", username="v1", password="pw"
        )
        self.user2 = User.objects.create_user(
            email="v2@test.com", username="v2", password="pw"
        )
        city = City.objects.create(name="VCity")
        sub1 = Subscription.objects.create(
            user=self.user1, city=city, interval_hours=1, notification_type="email"
        )
        sub2 = Subscription.objects.create(
            user=self.user2, city=city, interval_hours=1, notification_type="email"
        )
        NotificationLog.objects.create(subscription=sub1, status="s", response="r1")
        NotificationLog.objects.create(subscription=sub2, status="s", response="r2")
        self.client.force_authenticate(user=self.user1)

    def test_list_logs_filters_by_user(self):
        url = reverse("notificationlog-list")
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 1)
        self.assertEqual(r.data[0]["response"], "r1")

    def test_unauthenticated_cannot_access(self):
        self.client.logout()
        url = reverse("notificationlog-list")
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)
