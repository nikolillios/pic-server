from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, LogoutView, register_pi, pair_pi, unpair_pi


urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('pi/register/', register_pi, name='pi-register'),
    path('pi/pair/', pair_pi, name='pi-pair'),
    path('pi/unpair/<str:serial_id>/', unpair_pi, name='unpair-pi'),
]