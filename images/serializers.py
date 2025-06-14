from rest_framework import serializers
from .models import ImageModel, ImageCollection, DisplayDeviceConfig

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
