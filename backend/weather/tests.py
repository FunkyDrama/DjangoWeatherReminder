from django.test import TestCase
from unittest.mock import patch
from datetime import datetime
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model

from weather.services import WeatherAPIClient, WeatherData

User = get_user_model()


class WeatherServiceTests(TestCase):
    """
    Test suite for WeatherAPIClient.

    This class contains test cases to verify the functionality of the
    WeatherAPIClient, particularly the `get_current` method. The tests
    ensure the proper interfacing with the external weather API and
    validation of the returned weather data.

    """

    @patch("weather.services.requests.get")
    def test_get_current_returns_weatherdata(self, mock_get):
        mock_resp = mock_get.return_value
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "main": {"temp": 21.3, "humidity": 73},
            "weather": [{"main": "Clouds"}],
            "dt": 1625155200,
        }

        client = WeatherAPIClient()
        wd = client.get_current("TestCity")
        self.assertIsInstance(wd, WeatherData)
        self.assertEqual(wd.temperature, 21.3)
        self.assertEqual(wd.humidity, 73)
        self.assertEqual(wd.condition, "Clouds")
        self.assertEqual(wd.timestamp, datetime.fromtimestamp(1625155200))
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn("/weather", args[0])
        self.assertEqual(kwargs["params"]["q"], "TestCity")
        self.assertEqual(kwargs["params"]["units"], "metric")


class WeatherAPITests(TestCase):
    """
    Test suite for the Weather API.

    This class contains test cases to verify the behavior and functionality of the
    Weather API endpoints. It includes tests for authentication requirements,
    validations on input parameters, and the correctness of API responses. The
    purpose of this class is to ensure the robustness and reliability of the
    Weather API implementation.

    :ivar client: An instance of APIClient used for making HTTP requests in the tests.
    :type client: APIClient
    :ivar user: A user object created for authentication testing purposes.
    :type user: User
    :ivar token: A valid JWT token obtained for the created user for authenticated requests.
    :type token: str
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="api@test.com", password="pass1234")
        login_url = reverse("token_obtain_pair")
        r = self.client.post(
            login_url, {"email": "api@test.com", "password": "pass1234"}, format="json"
        )
        self.assertEqual(r.status_code, 200)
        self.token = r.data["access"]

    def test_unauthenticated_cannot_access(self):
        url = reverse("weather")
        r = self.client.get(url + "?city=Paris")
        self.assertEqual(r.status_code, 401)

    def test_missing_city_param(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        url = reverse("weather")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.data, {"detail": "City parameter is required."})

    @patch("weather.services.requests.get")
    def test_weather_api_view_returns_data(self, mock_get):
        mock_resp = mock_get.return_value
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "main": {"temp": 3.5, "humidity": 22},
            "weather": [{"main": "Snow"}],
            "dt": 1609459200,
        }

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        url = reverse("weather")
        r = self.client.get(url + "?city=Reykjavik")

        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["temperature"], 3.5)
        self.assertEqual(r.data["humidity"], 22)
        self.assertEqual(r.data["condition"], "Snow")
        self.assertIn("timestamp", r.data)
        mock_get.assert_called_once()
