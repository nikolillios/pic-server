from account.models import UserData
from account.serializers import RegisterSerializer
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from .models import RaspberryPi
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


class RegisterView(generics.CreateAPIView):
    queryset = UserData.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class LogoutView(APIView):
     permission_classes = (IsAuthenticated,)
     def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_pi(request):
    """Pi registration endpoint - no auth required"""
    serial_id = request.data.get('serial_id')
    public_key = request.data.get('public_key')
    pairing_code = request.data.get('pairing_code')
    
    if not all([serial_id, public_key, pairing_code]):
        return Response(
            {'error': 'Missing required fields'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if already registered
    if RaspberryPi.objects.filter(serial_id=serial_id).exists():
        return Response(
            {'error': 'Device already registered'},
            status=status.HTTP_409_CONFLICT
        )
    
    pi = RaspberryPi.objects.create(
        serial_id=serial_id,
        public_key=public_key,
        pairing_code=pairing_code,
        is_paired=False
    )
    
    return Response(
        {'message': 'Device registered successfully'},
        status=status.HTTP_201_CREATED
    )