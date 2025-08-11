from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer class for user registration.

    This serializer is responsible for handling user registration data. It ensures
    that the password is write-only, and allows an optional webhook_url to be provided
    during registration. The validated data is used to create a new user instance.

    :ivar password: Write-only field for the user's password.
    :type password: serializers.CharField
    :ivar webhook_url: Optional URL for user-specific webhook functionality. It can
        be null or blank.
    :type webhook_url: serializers.URLField
    """

    password = serializers.CharField(write_only=True)
    webhook_url = serializers.URLField(
        required=False, allow_null=True, allow_blank=True
    )

    class Meta:
        model = User
        fields = ("id", "email", "username", "password", "webhook_url")

    def create(self, validated_data):
        webhook_url = validated_data.pop("webhook_url", None)
        user = User.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"],
        )
        if webhook_url:
            user.webhook_url = webhook_url
            user.save(update_fields=["webhook_url"])
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for handling User model data.

    This serializer is designed to manage the serialization and deserialization of
    data related to the User model. It specifies the fields to include during
    serialization and provides configuration for read-only fields.

    :ivar id: The unique identifier of the user.
    :type id: int
    :ivar email: The email address of the user. This field is read-only.
    :type email: str
    :ivar username: The username of the user. This field is read-only.
    :type username: str
    :ivar webhook_url: The webhook URL associated with the user.
    :type webhook_url: str
    """

    class Meta:
        model = User
        fields = ("id", "email", "username", "webhook_url")
        read_only_fields = ("email", "username")
