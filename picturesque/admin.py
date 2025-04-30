from django.contrib import admin
from images.models import ImageModel, DitheredImageModel

admin.site.register(ImageModel)
admin.site.register(DitheredImageModel)