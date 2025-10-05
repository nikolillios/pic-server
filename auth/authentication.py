from rest_framework import authentication
from rest_framework import exceptions
import jwt
from jwt.exceptions import InvalidTokenError
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from .models import RaspberryPi

class PiAuthentication(authentication.BaseAuthentication):
    """Custom authentication for Raspberry Pi devices"""
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None  # Let other auth methods try
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decode without verification first to get serial_id
            unverified = jwt.decode(token, options={"verify_signature": False})
            serial_id = unverified.get('serial_id')
            
            if not serial_id:
                raise exceptions.AuthenticationFailed('No serial_id in token')
            
            # Get the Pi and its public key
            try:
                pi = RaspberryPi.objects.get(serial_id=serial_id)
            except RaspberryPi.DoesNotExist:
                raise exceptions.AuthenticationFailed('Unknown device')
            
            # Check if paired and has owner
            if not pi.is_paired or not pi.owner:
                raise exceptions.AuthenticationFailed('Device not paired to an account')
            
            if not pi.is_active:
                raise exceptions.AuthenticationFailed('Device is deactivated')
            
            public_key_obj = serialization.load_pem_public_key(
                pi.public_key.encode('utf-8'),  # Convert string to bytes
                backend=default_backend()
            )
            
            # Verify the token with the loaded public key object
            payload = jwt.decode(
                token,
                public_key_obj,
                algorithms=['RS256']
            )
            
            # Verify serial_id consistency
            if payload.get('serial_id') != serial_id:
                raise exceptions.AuthenticationFailed('Serial ID mismatch')
            
            # Update last_seen
            pi.save(update_fields=['last_seen'])
            
            # Return owner as user, Pi as auth
            return (pi.owner, pi)
            
        except InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')
    
    def authenticate_header(self, request):
        return 'Bearer'
