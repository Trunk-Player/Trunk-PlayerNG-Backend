from rest_framework import serializers

from users.models import CustomUser
from radio.serializers import UserProfileSerializer

class UserSerializer(serializers.ModelSerializer):
    userProfile = UserProfileSerializer()

    class Meta:
        model = CustomUser
        fields = ["id", "email", "first_name", "last_name", "enabled", "userProfile"]
