from django.core.files import File
from django.core.files.images import ImageFile
from django.core.files.base import ContentFile
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from account.models import UserData
import io, base64
import numpy as np
import uuid
from PIL import Image
from .models import *
from .serializers import ImageSerializer, ImageCollectionSerializer, DisplayDeviceConfigSerializer
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
def getCollections(request):
    collections = ImageCollection.objects.filter(owner=request.user)
    return Response(ImageCollectionSerializer(collections, many=True).data)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getDeviceCollections(request, device_id):
    collections = ImageCollection.objects.filter(owner=request.user).filter(device_model=device_id)
    print(collections)
    return Response(ImageCollectionSerializer(collections, many=True).data)

@csrf_exempt
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_image(request, id):
    try:
        im = ImageModel.objects.get(id=id)
    except ImageModel.DoesNotExist:
        return Response({"error": "Image not found"})
    im.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getDitheredImagesByCollection(request, collection_id):
    collection = ImageCollection.objects.get(id=collection_id)
    res_data = {}
    for dith in collection.dithered_images.all():
        res_data[dith.id] = {
            "data": base64.b64encode(dith.image.read()).decode(),
            "mime_type": 'image/bmp'
        }
        # im = Image.open(dith.image)
        # im.show()
        # print(im.size)
    return JsonResponse(res_data)

def get_image_str_from_b64_url(url):
    return url.split(',')[1]

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def uploadImageToCollection(request):
    base64Str = get_image_str_from_b64_url(request.data["image_url"])
    imageBytes = io.BytesIO(base64.decodebytes(bytes(base64Str, "utf-8")))
    imgFile = ImageFile(imageBytes, f'{uuid.uuid4()}.png')

    imgModel = ImageModel.objects.create(
        owner=request.user,
        image=imgFile,
    )

    collection = ImageCollection.objects.get(id=request.data["collection_id"])
    collection.images.add(imgModel)

    # Scale image and convert to 3 channel RGB
    image = Image.open(imageBytes).convert('RGB').resize(MODEL_TO_SIZE[collection.device_model])
    buffered = io.BytesIO()
    image.save(buffered, format="jpeg")
    resized_b64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # Call celery task to dither async
    ditherImageFromBytesAndSave.delay(resized_b64_str, request.user.id, imgModel.id, collection.id)
    return HttpResponse("Successfully received image")


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def uploadImageFile(request):
    base64Str = get_image_str_from_b64_url(request.data["image"])
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
    # ditherImageFromBytesAndSave.delay(base64Str, request.user.id, imgModel.id)
    return HttpResponse("Successfully received image")

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createCollection(request):
    data = request.data
    user = request.user
    collection = ImageCollection.objects.create(
        name = data["collection_name"],
        owner = user,
        device_model = int(data["model"])
    )
    return Response(ImageCollectionSerializer(collection).data)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getConfigForDevice(request, serial):
    device_config = DisplayDeviceConfig.objects.filter(serial_id=serial)
    if device_config.exists():
        return Response(DisplayDeviceConfigSerializer(device_config.first()).data)
    else:
        return Response(status=status.HTTP_204_NO_CONTENT)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createConfigForDevice(request):
    try:
        print(request.data)
        print(type(request.data))
        print(request.user.id)
        if not request.data["collection_id"]:
            raise Exception("No collection id given")
        collection_id = int(request.data["collection_id"])
        config_collection = ImageCollection.objects.get(id=collection_id)
        if not config_collection:
            raise Exception(f'No matching config for {collection_id}')
        config = DisplayDeviceConfig.objects.create(
            name = request.data["device_name"],
            owner = request.user,
            serial_id = request.data["serial"],
            device_model = int(request.data["device_model"]),
            collection = config_collection,
        )
        return Response(DisplayDeviceConfigSerializer(config).data)
    except Exception as e:
        print(e)
        return Response(f'Error: {e}', status=status.HTTP_400_BAD_REQUEST)
