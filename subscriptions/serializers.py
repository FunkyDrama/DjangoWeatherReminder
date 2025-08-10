from rest_framework import serializers
from .models import City, Subscription


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("id", "name", "external_id")
        extra_kwargs = {
            "name": {"validators": []},
        }


class SubscriptionSerializer(serializers.ModelSerializer):
    city = CitySerializer()

    class Meta:
        model = Subscription
        fields = (
            "id",
            "city",
            "interval_hours",
            "notification_type",
            "last_notified",
            "created_at",
        )

    def create(self, validated_data):
        user = validated_data.pop("user", None) or self.context["request"].user
        city_data = validated_data.pop("city")
        city, _ = City.objects.get_or_create(
            name=city_data["name"],
            defaults={"external_id": city_data.get("external_id")},
        )
        return Subscription.objects.create(user=user, city=city, **validated_data)

    def update(self, instance, validated_data):
        city_data = validated_data.pop("city", None)
        if city_data:
            city, _ = City.objects.get_or_create(
                name=city_data["name"],
                defaults={"external_id": city_data.get("external_id")},
            )
            instance.city = city

        instance.interval_hours = validated_data.get(
            "interval_hours", instance.interval_hours
        )
        instance.notification_type = validated_data.get(
            "notification_type", instance.notification_type
        )
        instance.save()
        return instance
