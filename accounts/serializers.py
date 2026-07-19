from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "role"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        # Only allow admin role if no admin exists yet (setup mode)
        requested_role = validated_data.get("role", "editor")
        if requested_role == "admin" and User.objects.filter(role="admin").exists():
            raise serializers.ValidationError({"role": "Admin already exists. Contact existing admin."})
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            role=requested_role,
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "bio", "date_joined"]
        read_only_fields = ["id", "date_joined"]


class AdminSetupOpenSerializer(serializers.Serializer):
    open = serializers.BooleanField()
