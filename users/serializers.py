from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer class for registering new users.

    This class is tailored for creating a new user instance with the necessary fields,
    managing passwords securely by ensuring it is write-only. It interacts with the
    User model to create user instances.

    :ivar password: Write-only field for user password.
    :type password: serializers.CharField
    """

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "username", "password")

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"],
        )


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.

    This class defines the serialization and deserialization processes for the
    `User` model. It specifies the fields that are included in serialized output
    and deserialized input. The serializer is typically used for API requests and
    responses to handle user-related data efficiently.

    :ivar Meta.model: The model associated with this serializer.
    :type Meta.model: type[User]
    :ivar Meta.fields: The fields to include in serialization and deserialization.
    :type Meta.fields: tuple[str, ...]
    """

    class Meta:
        model = User
        fields = ("id", "email", "username", "password")
