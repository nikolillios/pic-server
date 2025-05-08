from account.models import UserData
from celery import shared_task
from django.core.files.base import ContentFile
from django.core.files.images import ImageFile
from PIL import Image
from .models import ImageModel, DitheredImageModel
from .services.image_service import ditherAtkinson
import base64
import io
import uuid

@shared_task
def ditherImageFromBytesAndSave(bytes64, user_id, original_id):
    image_bytes = io.BytesIO(base64.decodebytes(bytes(bytes64, "utf-8")))
    imgFile = ImageFile(image_bytes, f'{uuid.uuid4()}.png')

    image = Image.open(imgFile).convert('RGB')
    dithered_image = ditherAtkinson(np.array(image))
    dithered_io = io.BytesIO()
    dithered_image.save(dithered_io, format="bmp")
    dithered_file = ContentFile(dithered_io.getvalue())

    dith_model = DitheredImageModel.objects.create(
        owner=UserData.objects.get(id=user_id),
        original_image=ImageModel.objects.get(id=original_id),
        image=ImageFile(dithered_file, f'{uuid.uuid4()}.bmp')
    )
