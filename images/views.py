from django.core.files import File
from django.core.files.images import ImageFile
from django.core.files.base import ContentFile
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from account.models import UserData
import io, base64
import numpy as np
import uuid
from PIL import Image
from .models import ImageModel, DitheredImageModel
from .serializers import ImageSerializer
from .services.image_service import getImagesByUserID, ditherAtkinson
from .tasks import ditherImageFromBytesAndSave

# Create your views here.
@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserImages(request):
    imgModels = request.user.imagemodel_set.all()
    # for img in imgModels:
    #     print(img.image.file)
    #     img = Image.open(img.image)
    #     img.show(img)
    serializer = ImageSerializer(imgModels, many=True)
    return Response(serializer.data)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getDitheredImagesByDims(request, height, width):
    if not height or not width:
        return Response("Must provide dimensions are request param.")
    dithModels = request.user.ditheredimagemodel_set.all()
    res_data = {}
    for image_instance in dithModels:
        
        res_data[f'{image_instance.image.url.split('/')[-1]}'] = {
            "data": base64.b64encode(image_instance.image.read()).decode(),
            "mime_type": 'image/bmp'
        }
        im = Image.open(image_instance.image)
        im.show()
        resized = im.resize((800, 400))
        resized.show()
        print(im.size)
    return JsonResponse(res_data)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def uploadImageFile(request):
    base64Str = request.data["image"].split(',')[1]
    imageBytes = io.BytesIO(base64.decodebytes(bytes(base64Str, "utf-8")))
    imgFile = ImageFile(imageBytes, f'{uuid.uuid4()}.png')

    imgModel = ImageModel.objects.create(
        owner=request.user,
        image=imgFile,
    )

    image = Image.open(imageBytes).convert('RGB')
    
    image_bytes = io.BytesIO(base64.decodebytes(bytes(base64Str, "utf-8")))
    im_id = uuid.uuid4()
    imgFile = ImageFile(image_bytes, f'{im_id}.png')

    image = Image.open(imgFile).convert('RGB')
    dithered_image = ditherAtkinson(np.array(image))
    dithered_io = io.BytesIO()
    dithered_image.save(dithered_io, format="bmp")
    dithered_file = ContentFile(dithered_io.getvalue(), f'{im_id}.bmp')

    dith_model = DitheredImageModel.objects.create(
        owner=UserData.objects.get(id=request.user.id),
        original_image=ImageModel.objects.get(id=imgModel.id),
        image=dithered_file
        # image=ImageFile(dithered_file, f'{uuid.uuid4()}.bmp')
    )
    im = Image.open(dithered_io)
    im.show()
    # ditherImageFromBytesAndSave.delay(base64Str, request.user.id, imgModel.id)
    return HttpResponse("Successfully received image")
