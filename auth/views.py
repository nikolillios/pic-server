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
from images.models import SupportedEPaper
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
    """
    Pi registration endpoint - no auth required.
    """
    serial_id = request.data.get('serial_id')
    public_key = request.data.get('public_key')
    pairing_code = request.data.get('pairing_code')
    device_model = request.data.get('device_model')
    
    # Check for missing fields and provide specific feedback
    missing_fields = []
    if not serial_id:
        missing_fields.append('serial_id')
    if not public_key:
        missing_fields.append('public_key')
    if not pairing_code:
        missing_fields.append('pairing_code')
    if not device_model:
        missing_fields.append('device_model')
    
    if missing_fields:
        return Response(
            {'error': f'Missing required fields: {", ".join(missing_fields)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    # Validate device_model
    try:
        device_model_int = int(device_model)
    except (ValueError, TypeError):
        return Response(
            {'error': 'device_model must be a valid integer'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if device_model_int not in SupportedEPaper.values:
        return Response(
            {'error': f'Invalid device_model. Must be one of: {", ".join([str(choice[0]) for choice in SupportedEPaper.choices])}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if already registered
    if RaspberryPi.objects.filter(serial_id=serial_id).exists():
        return Response(
            {'error': 'Device already registered'},
            status=status.HTTP_409_CONFLICT
        )
    
    # Create Pi with hashed pairing code
    pi = RaspberryPi(
        serial_id=serial_id,
        public_key=public_key,
        device_model=device_model,
        display_name=serial_id,  # Set initial display name to serial_id
        is_paired=False
    )
    pi.set_pairing_code(pairing_code)  # Hash it
    pi.save()
    
    return Response({
        'message': 'Device registered successfully',
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pair_pi(request):
    """
    User pairs a Pi to their account using serial ID and pairing code.
    The pairing code is NOT cleared after pairing - it can be reused.
    """
    serial_id = request.data.get('serial_id')
    pairing_code = request.data.get('pairing_code')
    
    if not serial_id or not pairing_code:
        return Response(
            {'error': 'Serial ID and pairing code are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Device must not already be paired
        pi = RaspberryPi.objects.get(serial_id=serial_id, is_paired=False)
    except RaspberryPi.DoesNotExist:
        return Response(
            {'error': 'Invalid serial ID or device already paired'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Verify pairing code against hash
    if not pi.check_pairing_code(pairing_code):
        return Response(
            {'error': 'Invalid pairing code'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Pair the device - pairing_code remains in database (hashed)
    pi.owner = request.user
    pi.is_paired = True
    pi.set_default_display_name()  # Set default display name
    pi.save()
    
    # TODO: Send email notification
    # send_device_paired_email(request.user, pi.serial_id)
    
    return Response({
        'message': 'Device paired successfully',
        'serial_id': pi.serial_id
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unpair_pi(request, serial_id):
    """
    User can unpair their Pi.
    The pairing code remains valid - same code can be used to re-pair.
    """
    try:
        pi = RaspberryPi.objects.get(serial_id=serial_id, owner=request.user)
    except RaspberryPi.DoesNotExist:
        return Response(
            {'error': 'Device not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    pi.owner = None
    pi.is_paired = False
    pi.is_active = True  # Reset to active for next pairing
    pi.display_name = pi.serial_id  # Reset display name to serial_id for next user
    pi.collection = None  # Clear the associated collection
    # pairing_code is NOT cleared - it remains valid for re-pairing
    pi.save()
    
    # Optional: Send email notification
    # send_device_unpaired_email(request.user, pi.serial_id)
    
    return Response({
        'message': 'Device unpaired successfully. Same pairing code can be used to re-pair.'
    })

