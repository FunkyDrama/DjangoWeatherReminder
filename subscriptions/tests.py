from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from django.contrib.auth import get_user_model
from subscriptions.models import City, Subscription
from subscriptions.serializers import CitySerializer, SubscriptionSerializer

User = get_user_model()


class CityModelSerializerTests(TestCase):
    """
    Unit tests for City model string representation and serializer.

    This test class is designed to verify the functionality of the City model
    and the CitySerializer. It ensures that the City's string representation
    is correctly implemented and that the serializer outputs the expected
    data format.
    """

    def test_city_str_and_serializer(self):
        city = City.objects.create(name="Testville", external_id="t123")
        self.assertEqual(str(city), "Testville")
        data = CitySerializer(city).data
        self.assertEqual(
            data, {"id": city.id, "name": "Testville", "external_id": "t123"}
        )


class SubscriptionModelTests(TestCase):
    """
    Test suite for verifying Subscription model behaviors and functionality.

    This class contains tests for validating the string representation of
    subscriptions and ensuring that attribute relationships between
    Subscription, User, and City models function appropriately.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="u@example.com", username="u", password="pw"
        )
        self.city = City.objects.create(name="AlphaCity")

    def test_subscription_str(self):
        sub = Subscription.objects.create(
            user=self.user,
            city=self.city,
            interval_hours=3,
            notification_type="webhook",
        )
        expected = f"{self.user.email} - {self.city.name} every 3h via webhook"
        self.assertEqual(str(sub), expected)


class SubscriptionSerializerTests(TestCase):
    """
    Test case class for testing SubscriptionSerializer functionality.

    This class contains unit tests designed to verify the functionality
    of the SubscriptionSerializer. It checks for creation of new
    subscriptions with city details, reusability of existing city
    entries in subscriptions, and updating existing subscription
    data.

    :ivar user: Test user created for running the tests.
    :type user: User
    :ivar city: Pre-existing City object used in test cases.
    :type city: City
    :ivar context: Context containing a simulated request object
                   with the test user.
    :type context: dict
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="a@b.com", username="a", password="pw"
        )
        self.city = City.objects.create(name="ExistingCity")
        self.context = {"request": type("R", (), {"user": self.user})}

    def test_create_new_city_subscription(self):
        data = {
            "city": {"name": "NewCity", "external_id": "nc123"},
            "interval_hours": 6,
            "notification_type": "email",
        }
        serializer = SubscriptionSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        sub = serializer.save()
        self.assertTrue(City.objects.filter(name="NewCity").exists())
        self.assertEqual(sub.interval_hours, 6)
        self.assertEqual(sub.notification_type, "email")
        self.assertEqual(sub.user, self.user)
        self.assertEqual(sub.city.external_id, "nc123")

    def test_serializer_reuses_existing_city(self):
        City.objects.create(name="Exist2", external_id="e2")
        data = {
            "city": {"name": "Exist2", "external_id": "IGNORED"},
            "interval_hours": 1,
            "notification_type": "webhook",
        }
        serializer = SubscriptionSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        sub = serializer.save()
        c = City.objects.get(name="Exist2")
        self.assertEqual(c.external_id, "e2")
        self.assertEqual(sub.city, c)

    def test_update_subscription(self):
        sub = Subscription.objects.create(
            user=self.user, city=self.city, interval_hours=1, notification_type="email"
        )
        data = {
            "city": {"name": "AnotherCity"},
            "interval_hours": 12,
            "notification_type": "webhook",
        }
        serializer = SubscriptionSerializer(
            sub, data=data, context=self.context, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.interval_hours, 12)
        self.assertEqual(updated.notification_type, "webhook")
        self.assertEqual(updated.city.name, "AnotherCity")


class SubscriptionAPITests(TestCase):
    """
    Test suite for Subscription API endpoints.

    This class contains a set of test cases to validate the functionality of
    Subscription API endpoints. The primary purpose is to ensure the correct
    behavior of creating, retrieving, listing, updating, and deleting subscription
    records, as well as validating triggered notifications and city listing.

    :ivar client: API client used to make requests to the endpoints.
    :type client: APIClient
    :ivar user: Authenticated user object used for testing API endpoints.
    :type user: User
    :ivar city1: First city object created for testing purposes.
    :type city1: City
    :ivar city2: Second city object created for testing purposes.
    :type city2: City
    :ivar sub1: Subscription object associated with the first city.
    :type sub1: Subscription
    :ivar sub2: Subscription object associated with the second city.
    :type sub2: Subscription
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="api@sub.com", username="apiuser", password="pw"
        )
        self.client.force_authenticate(user=self.user)
        self.city1 = City.objects.create(name="CityOne")
        self.city2 = City.objects.create(name="CityTwo")
        self.sub1 = Subscription.objects.create(
            user=self.user, city=self.city1, interval_hours=1, notification_type="email"
        )
        self.sub2 = Subscription.objects.create(
            user=self.user,
            city=self.city2,
            interval_hours=3,
            notification_type="webhook",
        )

    def test_list_cities(self):
        url = reverse("city-list")
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in r.data]
        self.assertIn("CityOne", names)
        self.assertIn("CityTwo", names)

    def test_list_subscriptions(self):
        url = reverse("subscription-list")
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 2)

    @patch("subscriptions.views.send_weather_updates")
    def test_create_subscription_triggers_send(self, mock_task):
        url = reverse("subscription-list")
        payload = {
            "city": {"name": "NewCityAPI"},
            "interval_hours": 6,
            "notification_type": "email",
        }
        r = self.client.post(url, payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        mock_task.assert_called_once()

    def test_retrieve_update_delete_subscription(self):
        url = reverse("subscription-detail", args=[self.sub1.id])
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["city"]["name"], "CityOne")
        r = self.client.patch(url, {"interval_hours": 12}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.sub1.refresh_from_db()
        self.assertEqual(self.sub1.interval_hours, 12)
        r = self.client.delete(url)
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Subscription.objects.filter(id=self.sub1.id).exists())
