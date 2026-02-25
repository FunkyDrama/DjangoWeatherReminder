import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from faker import Faker
from subscriptions.models import City, Subscription


class Command(BaseCommand):
    """
    Command to populate the database with fake users, cities, and subscriptions for testing or development purposes.

    This command generates a specified number of fake users, cities, and user subscriptions,
    allowing for the quick setup of a populated database. It leverages the Faker library to
    generate random data for cities and users and creates user subscriptions with random intervals
    and notification types.

    :ivar help: Description of the command's purpose displayed with the `help` command.
    :type help: str
    """

    help = "Fill DB with fake users, cities, and subscriptions"

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=5)
        parser.add_argument("--cities", type=int, default=10)
        parser.add_argument("--subs", type=int, default=20)

    def handle(self, *args, **options):
        fake = Faker()
        User = get_user_model()
        types = ["email", "webhook"]

        cities = [
            City.objects.get_or_create(name=fake.city())[0]
            for _ in range(options["cities"])
        ]
        self.stdout.write(self.style.SUCCESS(f"Created {len(cities)} cities"))

        users = []
        for _ in range(options["users"]):
            email = fake.unique.email()
            users.append(User.objects.create_user(email=email, password="password123"))
        self.stdout.write(self.style.SUCCESS(f"Created {len(users)} users"))

        count = 0
        for _ in range(options["subs"]):
            user = random.choice(users)
            city = random.choice(cities)
            interval = random.choice([1, 3, 6, 12])
            ntype = random.choice(types)
            sub, created = Subscription.objects.get_or_create(
                user=user, city=city, interval_hours=interval, notification_type=ntype
            )
            if created:
                sub.last_notified = timezone.now() - timezone.timedelta(
                    hours=random.randint(0, interval)
                )
                sub.save()
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Created {count} subscriptions"))
