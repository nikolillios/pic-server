from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import RaspberryPi
from rest_framework import serializers

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['uid'] = user.id
        return token


class RaspberryPiSerializer(serializers.ModelSerializer):
    class Meta:
        model = RaspberryPi
        fields = [
            'serial_id', 'is_active', 'is_paired', 'created_at', 'last_seen',
            'display_name', 'device_model', 'collection'
        ]
        read_only_fields = ['serial_id', 'created_at', 'last_seen']
