from django.core.files import File
from django.core.files.images import ImageFile
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import ImageModel
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .services.image_service import getImagesByUserID
from account.models import UserData
import io, base64
import uuid
from PIL import Image
from .serializers import ImageSerializer

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
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def uploadImageFile(request):
    print(f"Saving image! User: {request.user}")
    # print(f"data: {request.data['image'][:100]}")
    base64Str = request.data["image"].split(',')[1]
    imageBytes = io.BytesIO(base64.decodebytes(bytes(base64Str, "utf-8")))
    imgFile = ImageFile(imageBytes, f'{uuid.uuid4()}.png')
    imgModel = ImageModel.objects.create(
        owner=request.user,
        image=imgFile,
    )
    print("recevied image")
    return HttpResponse("Successfully received image")
