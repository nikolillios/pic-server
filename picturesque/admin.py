from django.contrib import admin
from images.models import ImageModel, DitheredImageModel, ImageCollection

admin.site.register(ImageModel)
admin.site.register(DitheredImageModel)
admin.site.register(ImageCollection)