from django.core.files import File
from django.core.files.images import ImageFile
from django.core.files.base import ContentFile
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
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
from auth.models import RaspberryPi
from auth.serializers import RaspberryPiSerializer
from .services.image_service import ditherAtkinson
from .tasks import ditherImageFromBytesAndSave

# Create your views here.
@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserImages(request):
    # Get pagination parameters, if any
    page = request.query_params.get('page', None)
    page_size = request.query_params.get('page_size', None)

    user_images_qs = request.user.imagemodel_set.all().order_by('-id')

    if page is not None and page_size is not None:
        try:
            page = int(page)
            page_size = int(page_size)
            if page < 1 or page_size < 1:
                raise ValueError
            start = (page - 1) * page_size
            end = start + page_size
            # Use queryset slicing to avoid loading all objects
            user_images_qs = user_images_qs[start:end]
        except (ValueError, TypeError):
            return Response({"error": "Invalid pagination parameters"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = ImageSerializer(user_images_qs, many=True)
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
    return Response(ImageCollectionSerializer(collections, many=True).data)

@csrf_exempt
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_image(request, id):
    try:
        im = ImageModel.objects.get(id=id)
    except ImageModel.DoesNotExist:
        return Response({"error": "Image not found"})
    res = Response(ImageSerializer(im).data)
    im.delete()
    return res

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getDitheredImagesByCollection(request, collection_id):
    try:
        collection = ImageCollection.objects.get(id=collection_id, owner=request.user)
        res_data = {}
        for dith in collection.dithered_images.all():
            res_data[dith.id] = {
                "data": base64.b64encode(dith.image.read()).decode(),
                "mime_type": 'image/bmp'
            }
        return JsonResponse(res_data)
    except ImageCollection.DoesNotExist:
        return Response({"error": "Collection not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_image_str_from_b64_url(url):
    return url.split(',')[1]

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def uploadImageToCollection(request):
    try:
        if not request.data.get("image_url") or not request.data.get("collection_id"):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
            
        base64Str = get_image_str_from_b64_url(request.data["image_url"])
        imageBytes = io.BytesIO(base64.decodebytes(bytes(base64Str, "utf-8")))
        imgFile = ImageFile(imageBytes, f'{uuid.uuid4()}.png')

        with transaction.atomic():
            imgModel = ImageModel.objects.create(
                owner=request.user,
                image=imgFile,
            )

            collection = ImageCollection.objects.get(id=request.data["collection_id"], owner=request.user)
            collection.images.add(imgModel)

        # Scale image and convert to 3 channel RGB
        image = Image.open(imageBytes).convert('RGB').resize(MODEL_TO_SIZE[collection.device_model])
        buffered = io.BytesIO()
        image.save(buffered, format="jpeg")
        resized_b64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Call celery task to dither async
        ditherImageFromBytesAndSave.delay(resized_b64_str, request.user.id, imgModel.id, collection.id)
        return Response(ImageSerializer(imgModel).data)
    except ImageCollection.DoesNotExist:
        return Response({"error": "Collection not found"}, status=status.HTTP_404_NOT_FOUND)
    except (ValueError, KeyError) as e:
        return Response({"error": "Invalid data format"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def uploadImageFile(request):
    try:
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
        ditherImageFromBytesAndSave.delay(base64Str, request.user.id, imgModel.id)
        return Response(ImageSerializer(imgModel).data)
    except Exception as e:
        print(f'Error while uploading photo: {e}')
        return HttpResponse(f'Error uploading image: {e}', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createCollection(request):
    try:
        if not request.data.get("collection_name") or not request.data.get("model"):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
            
        collection = ImageCollection.objects.create(
            name=request.data["collection_name"],
            owner=request.user,
            device_model=int(request.data["model"])
        )
        return Response(ImageCollectionSerializer(collection).data)
    except ValueError:
        return Response({"error": "Invalid model value"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getDeviceConfigs(request):
    device_configs = DisplayDeviceConfig.objects.filter(owner=request.user.id)
    return Response(DisplayDeviceConfigSerializer(device_configs, many=True).data)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updateConfigForDevice(request):
    try:
        if not request.data.get("config_id"):
            return Response({"error": "Missing config_id"}, status=status.HTTP_400_BAD_REQUEST)
            
        config = DisplayDeviceConfig.objects.get(id=request.data["config_id"], owner=request.user)
        
        if "collection_id" in request.data:
            collection = ImageCollection.objects.get(id=request.data["collection_id"], owner=request.user)
            if collection.id == config.collection_id:
                return Response({"error": "Cannot change to the same collection"}, status=status.HTTP_400_BAD_REQUEST)
            config.collection = collection
            
        if "device_name" in request.data:
            config.name = request.data["device_name"]
            
        config.save()
        return Response(DisplayDeviceConfigSerializer(config).data)
    except DisplayDeviceConfig.DoesNotExist:
        return Response({"error": "Config not found"}, status=status.HTTP_404_NOT_FOUND)
    except ImageCollection.DoesNotExist:
        return Response({"error": "Collection not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createConfigForDevice(request):
    try:
        required_fields = ["collection_id", "device_name", "serial", "device_model"]
        for field in required_fields:
            if not request.data.get(field):
                return Response({"error": f"Missing required field: {field}"}, status=status.HTTP_400_BAD_REQUEST)
                
        collection = ImageCollection.objects.get(id=request.data["collection_id"], owner=request.user)
        config = DisplayDeviceConfig.objects.create(
            name=request.data["device_name"],
            owner=request.user,
            serial_id=request.data["serial"],
            device_model=int(request.data["device_model"]),
            collection=collection,
        )
        return Response(DisplayDeviceConfigSerializer(config).data)
    except ImageCollection.DoesNotExist:
        return Response({"error": "Collection not found"}, status=status.HTTP_404_NOT_FOUND)
    except ValueError:
        return Response({"error": "Invalid numeric value"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getRandomImages(request):
    try:
        # Get count parameter, default to 10, cap at 50
        count = int(request.query_params.get('count', 10))
        count = min(max(count, 1), 50)  # Ensure count is between 1 and 50
        
        # Get all user's images using the reverse relationship
        user_images = request.user.imagemodel_set.all()
        
        if not user_images.exists():
            return Response([])
        
        # Use order_by('?') for random ordering and limit to count
        random_images = user_images.order_by('?')[:count]
        
        return Response(ImageSerializer(random_images, many=True).data)
    except ValueError:
        return Response({"error": "Invalid count parameter"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_displays(request):
    """
    Get all paired Raspberry Pi displays for the authenticated user.
    """
    try:
        displays = request.user.raspberrypi_set.filter(is_paired=True)
        serializer = RaspberryPiSerializer(displays, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updateDisplay(request):
    """
    Update display name and/or collection.
    """
    try:
        if not request.data.get("serial_id"):
            return Response({"error": "Missing serial_id"}, status=status.HTTP_400_BAD_REQUEST)
            
        pi = RaspberryPi.objects.get(serial_id=request.data["serial_id"], owner=request.user)
        
        if "collection_id" in request.data:
            collection = request.user.imagecollection_set.get(id=request.data["collection_id"])
            if collection.id == pi.collection_id:
                return Response({"error": "Cannot change to the same collection"}, status=status.HTTP_400_BAD_REQUEST)
            pi.collection = collection
            
        if "display_name" in request.data:
            pi.display_name = request.data["display_name"]
            
        pi.save()
        return Response(RaspberryPiSerializer(pi).data)
    except RaspberryPi.DoesNotExist:
        return Response({"error": "Raspberry Pi not found"}, status=status.HTTP_404_NOT_FOUND)
    except ImageCollection.DoesNotExist:
        return Response({"error": "Collection not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
