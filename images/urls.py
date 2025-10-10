from .views import getUserImages, uploadImageFile, getDitheredImagesByCollection, createCollection, getCollections, uploadImageToCollection, getDeviceCollections, delete_image, getConfigForDevice, createConfigForDevice, updateConfigForDevice, getRandomImages, get_user_displays, updateDisplay, get_dithered_images, get_config_for_display_device
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
    path('createConfigForDevice/', createConfigForDevice, name="createConfigForDevice"),
    path('updateDeviceConfig/', updateConfigForDevice, name='updateDeviceConfig'),
    path('displays/', get_user_displays, name='get-user-displays'),
    path('displays/update/', updateDisplay, name='update-display'),
    path('getDitheredImages/<int:collection_id>', get_dithered_images, name='getDitheredImages'),
    path('config/<str:serial_id>', get_config_for_display_device, name='get_config_for_display_device'),
]

