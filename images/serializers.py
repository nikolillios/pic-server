from rest_framework import serializers
from .models import ImageModel, ImageCollection

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageModel
        fields = '__all__'

class ImageCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageCollection
        fields = '__all__'

