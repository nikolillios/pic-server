from django.db import models
from account.models import UserData

class RaspberryPi(models.Model):
    serial_id = models.CharField(max_length=100, unique=True, db_index=True)
    public_key = models.TextField()
    pairing_code = models.CharField(max_length=20, null=True, blank=True)
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
