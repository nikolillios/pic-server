from account.models import UserData
from celery import shared_task
from django.core.files.base import ContentFile
from django.core.files.images import ImageFile
from PIL import Image
from .models import ImageModel, DitheredImageModel, ImageCollection
from .services.image_service import ditherAtkinson
import base64
import io
import numpy as np
import uuid

@shared_task
def ditherImageFromBytesAndSave(base64Str, user_id, original_id, collection_id):
    image_bytes = io.BytesIO(base64.decodebytes(bytes(base64Str, "utf-8")))
    im_id = uuid.uuid4()
    imgFile = ImageFile(image_bytes, f'{im_id}.jpeg')

    image = Image.open(imgFile).convert('RGB')
    dithered_image = ditherAtkinson(np.array(image))
    dithered_io = io.BytesIO()
    dithered_image.save(dithered_io, format="bmp")
    dithered_file = ContentFile(dithered_io.getvalue(), f'{im_id}.bmp')

    dith_model = DitheredImageModel.objects.create(
        owner=UserData.objects.get(id=user_id),
        original_image=ImageModel.objects.get(id=original_id),
        image=dithered_file,
    )
    collection = ImageCollection.objects.get(id=collection_id)
    collection.dithered_images.add(dith_model)
