from .views import getUserImages, uploadImageFile, getDitheredImagesByDims
from django.urls import path, include

urlpatterns = [
    path('getImagesByUser/', getUserImages, name='getImagesByUser'),
    path('uploadImageFile/', uploadImageFile, name='uploadImageFile'),
    path('getDitheredImagesByDims/<int:height>/<int:width>/', getDitheredImagesByDims, name='getDitheredImagesByDims')
]

