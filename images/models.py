from django.db import models
import account.models as acc_models
from .services.image_service import userImagesDirPath, ditheredImagesDirPath

class ImageModel(models.Model):
    owner = models.ForeignKey(acc_models.UserData, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=userImagesDirPath, null=True)

class DitheredImageModel(models.Model):
    owner = models.ForeignKey(acc_models.UserData, on_delete=models.CASCADE)
    original_image = models.ForeignKey(ImageModel, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=ditheredImagesDirPath, null=True)


# SUPPORTED_EPAPER = [
#     ("7in3e", "7.3inch E-Paper"),
#     ("4in0e", "4inch E-Paper"),
#     ("13in3e", "13.3inch E-Paper"),
# ]
class SupportedEPaper(models.IntegerChoices):
    EPD4IN0 = 0
    EPD7IN3 = 1
    EPD13IN3 = 2

MODEL_TO_SIZE = {
    SupportedEPaper.EPD4IN0: (600, 400),
    SupportedEPaper.EPD7IN3: (800, 480),
    SupportedEPaper.EPD13IN3: (1600, 1200),
}

class ImageCollection(models.Model):
    name = models.CharField(max_length=36)
    owner = models.ForeignKey(acc_models.UserData, on_delete=models.CASCADE)
    images = models.ManyToManyField(ImageModel)
    dithered_images = models.ManyToManyField(DitheredImageModel)
    device_model = models.IntegerField(choices=SupportedEPaper)

    def validate_unique(self, exclude=None):
        if ImageCollection.objects.filter(name=self.name).exists():
            raise ValidationError('Names must be unique')

class DisplayDeviceConfig(models.Model):
    name = models.CharField(max_length=30)
    owner = models.ForeignKey(acc_models.UserData, on_delete=models.CASCADE)
    serial_id = models.CharField(max_length=16)
    device_model = models.IntegerField(choices=SupportedEPaper, null=True)
    collection = models.ForeignKey(ImageCollection, on_delete=models.SET_NULL, null=True)
