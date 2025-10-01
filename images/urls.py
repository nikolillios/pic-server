from .views import getUserImages, uploadImageFile, getDitheredImagesByCollection, createCollection, getCollections, uploadImageToCollection, getDeviceCollections, delete_image, getConfigForDevice, createConfigForDevice, getDeviceConfigs, updateConfigForDevice, getRandomImages
from django.urls import path, include

urlpatterns = [
    path('getImagesByUser/', getUserImages, name='getImagesByUser'),
    path('getRandomImages/', getRandomImages, name='getRandomImages'),
    path('uploadImageFile/', uploadImageFile, name='uploadImageFile'),
    path('getDitheredImagesByCollection/<int:collection_id>', getDitheredImagesByCollection, name='getDitheredImagesByCollection'),
    path('createCollection', createCollection, name='createCollection'),
    path('getCollections/', getCollections, name='getCollections'),
    path('getCollections/<int:device_id>', getDeviceCollections, name='getDeviceCollections'),
    path('uploadImageToCollection/', uploadImageToCollection, name='uploadImageToCollection'),
    path('deleteImage/<int:id>', delete_image, name="deleteImage"),
    path('getConfigForDevice/<str:serial>', getConfigForDevice, name="getConfigForDevice"),
    path('getDeviceConfigs', getDeviceConfigs, name='getDeviceConfigs'),
    path('createConfigForDevice/', createConfigForDevice, name="createConfigForDevice"),
    path('updateDeviceConfig/', updateConfigForDevice, name='updateDeviceConfig')
]

