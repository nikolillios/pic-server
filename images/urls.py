from .views import getUserImages, uploadImageFile
from django.urls import path, include

urlpatterns = [
    path('getImagesByUser/', getUserImages, name='getImagesByUser'),
    path('uploadImageFile/', uploadImageFile, name='uploadImageFile'),
]

