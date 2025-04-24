from django.core.files import File
from django.core.files.images import ImageFile
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import ImageModel
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .services.image_service import getImagesByUserID, saveImageModel
from account.models import UserData
import io, base64
import uuid
from PIL import Image

# Create your views here.
@csrf_exempt
@permission_classes([IsAuthenticated])
def getUserImages(request):
    user = request.user
    print(f'User: {user}')
    images = getImagesByUserID(user.id)
    print("images")
    print(images)
    return HttpResponse(f"{len(images)}") # TODO

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def uploadImageFile(request):
    print(f"Saving image! User: {request.user}")
    # print(type(request.user))
    # user = UserData.objects.get(request.user.id)
    # print(user)
    # if not user:
    #     raise Exception("No user!")
    # print(request.data["url"])
    print(f"data: {request.data['image'][:100]}")
    base64Str = request.data["image"].split(',')[1]
    imageBytes = io.BytesIO(base64.decodebytes(bytes(base64Str, "utf-8")))
    # img = Image.open(imageBytes)
    imgFile = ImageFile(imageBytes, f'{uuid.uuid4()}.png')
    imgModel = ImageModel.objects.create(
        owner=request.user,
        image=imgFile,
    )
    print("recevied image")
    return HttpResponse("Successfully received image")

def getImageById(image_id):
    return