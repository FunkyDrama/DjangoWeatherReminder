import io
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.core.management import call_command
from django.contrib.auth import get_user_model
from subscriptions.models import City, Subscription
from users.serializers import RegisterSerializer

User = get_user_model()


class FakeDataCommandTests(TestCase):
    """
    Unit test class for testing the `fake_data` management command.

    This class contains methods for verifying the correct behavior of the `fake_data`
    management command. The tests ensure the command generates the expected number of
    User, City, and Subscription objects when executed with default and custom parameters.
    """

    def test_fake_data_default(self):
        out = io.StringIO()
        call_command("fake_data", stdout=out)
        self.assertIn("Created", out.getvalue())
        self.assertGreater(User.objects.count(), 0)
        self.assertGreater(City.objects.count(), 0)
        self.assertGreater(Subscription.objects.count(), 0)

    def test_fake_data_params(self):
        call_command("fake_data", "--users", "2", "--cities", "3", "--subs", "5")
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(City.objects.count(), 3)
        self.assertTrue(0 < Subscription.objects.count() <= 5)


class RegisterSerializerTests(TestCase):
    """
    Tests for the RegisterSerializer class.

    This test case ensures that the RegisterSerializer correctly handles user
    creation and validation of unique email addresses. It checks if a user
    is successfully created with the provided valid data and confirms that
    duplicate email addresses are rejected during registration.

    The test case exercises the functionality of the serializer, ensuring
    that it adheres to expected behavior when creating users or processing
    duplicate email attempts.
    """

    def test_register_serializer_creates_user(self):
        data = {"email": "a@b.com", "password": "secret123"}
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertIsInstance(user, User)
        self.assertEqual(user.email, "a@b.com")
        self.assertTrue(user.check_password("secret123"))

    def test_register_serializer_rejects_duplicate_email(self):
        User.objects.create_user(email="dup@b.com", password="pw")
        data = {"email": "dup@b.com", "password": "pw2"}
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)


class UserAPITests(TestCase):
    """
    A test case for testing the user API functionalities, including registration,
    login, and retrieving user details.

    This test case covers the following flow:
    - User registration.
    - User login to obtain an access token.
    - Authorization and authentication of API requests using the obtained token.

    :ivar client: The testing client for simulating API requests.
    :type client: APIClient
    """

    def setUp(self):
        self.client = APIClient()

    def test_full_registration_and_me_flow(self):
        url_register = reverse("register")
        payload = {"email": "bob@b.com", "password": "pwd1234"}
        r = self.client.post(url_register, payload, format="json")
        self.assertEqual(r.status_code, 201)
        url_login = reverse("token_obtain_pair")
        r = self.client.post(
            url_login, {"email": "bob@b.com", "password": "pwd1234"}, format="json"
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("access", r.data)
        token = r.data["access"]
        r = self.client.get(reverse("user_detail"))
        self.assertEqual(r.status_code, 401)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        r = self.client.get(reverse("user_detail"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["email"], "bob@b.com")
