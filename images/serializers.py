from rest_framework import serializers
from .models import ImageModel, ImageCollection, DisplayDeviceConfig
from auth.models import RaspberryPi

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageModel
        fields = '__all__'

class ImageCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageCollection
        fields = '__all__'

class DisplayDeviceConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisplayDeviceConfig
        fields = '__all__'

class RasberryPiSerializer(serializers.ModelSerializer):
    class Meta:
        model = RaspberryPi
        fields = ['serial_id', 'display_name', 'collection']