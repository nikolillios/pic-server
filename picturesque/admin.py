from django.contrib import admin
from images.models import ImageModel, DitheredImageModel, ImageCollection, DisplayDeviceConfig

admin.site.register(ImageModel)
admin.site.register(DitheredImageModel)
admin.site.register(ImageCollection)
admin.site.register(DisplayDeviceConfig)
