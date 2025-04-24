from django.db import models
import account.models as acc_models
from .services.image_service import userImagesDirPath

class ImageModel(models.Model):
    owner = models.ForeignKey(acc_models.UserData, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=userImagesDirPath, null=True)

