from django.db import models
from account.models import UserData
from images.models import SupportedEPaper, ImageCollection, MODEL_TO_NAME
from django.contrib.auth.hashers import make_password, check_password

class RaspberryPi(models.Model):
    serial_id = models.CharField(max_length=100, unique=True, db_index=True)
    public_key = models.TextField()
    pairing_code = models.CharField(max_length=100)  # Hashed - never cleared, reusable
    is_paired = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(UserData, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Raspberry Pi"
        verbose_name_plural = "Raspberry Pis"
    
    def __str__(self):
        return f"Pi {self.serial_id} ({self.owner.username if self.owner else 'unpaired'})"
    
    def set_pairing_code(self, raw_code):
        """
        Hash the pairing code before storing.
        This is called ONCE when the Pi registers.
        """
        self.pairing_code = make_password(raw_code)
    
    def check_pairing_code(self, raw_code):
        """
        Verify pairing code against the hash.
        This can be used multiple times for pairing/re-pairing.
        """
        return check_password(raw_code, self.pairing_code)
